from typing import *
import torch
from ..voxel import Voxel

# voxkiln vendor surgery: cumesh and flex_gemm are CUDA-only optional
# accelerators. Without them, fill_holes/remove_faces/simplify no-op with a
# recorded flag (voxkiln's export chain repairs on CPU instead), and
# query_attrs falls back to an exact portable sparse-trilinear sampler.
try:
    import cumesh  # type: ignore[import-not-found]
    _CUMESH = True
except ImportError:
    _CUMESH = False
try:
    from flex_gemm.ops.grid_sample import grid_sample_3d  # type: ignore[import-not-found]
    _FLEX_GEMM = True
except ImportError:
    _FLEX_GEMM = False

_KEY_SPAN = 2**21


def _pack3(c: torch.Tensor) -> torch.Tensor:
    c = c.long() + (_KEY_SPAN // 2)
    return (c[:, 0] * _KEY_SPAN + c[:, 1]) * _KEY_SPAN + c[:, 2]


def _sparse_trilinear(attrs: torch.Tensor, coords: torch.Tensor, grid: torch.Tensor) -> torch.Tensor:
    """Exact trilinear sampling of a sparse voxel attribute volume.

    attrs: [N, C] per-voxel attributes; coords: [N, 3] int voxel coords;
    grid: [M, 3] query positions in voxel units (voxel centers at +0.5).
    Missing corner voxels get zero weight; weights renormalize over the
    corners actually present.
    """
    keys = _pack3(coords)
    order = keys.argsort()
    sorted_keys = keys[order]
    n = sorted_keys.shape[0]

    pos = grid - 0.5
    base = torch.floor(pos)
    frac = pos - base
    out = torch.zeros(grid.shape[0], attrs.shape[1], device=attrs.device, dtype=attrs.dtype)
    wsum = torch.zeros(grid.shape[0], 1, device=attrs.device, dtype=attrs.dtype)
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                corner = base + torch.tensor([dz, dy, dx], device=grid.device, dtype=base.dtype)
                w = ((frac[:, 0] if dz else 1 - frac[:, 0])
                     * (frac[:, 1] if dy else 1 - frac[:, 1])
                     * (frac[:, 2] if dx else 1 - frac[:, 2])).unsqueeze(1).to(attrs.dtype)
                q = _pack3(corner.long())
                p = torch.searchsorted(sorted_keys, q).clamp(max=n - 1)
                found = (sorted_keys[p] == q).unsqueeze(1)
                vals = attrs[order[p]]
                out = out + torch.where(found, vals * w, torch.zeros_like(vals))
                wsum = wsum + torch.where(found, w, torch.zeros_like(w))
    return out / wsum.clamp_min(1e-8)


class Mesh:
    def __init__(self,
        vertices,
        faces,
        vertex_attrs=None
    ):
        self.vertices = vertices.float()
        self.faces = faces.int()
        self.vertex_attrs = vertex_attrs
        
    @property
    def device(self):
        return self.vertices.device
        
    def to(self, device, non_blocking=False):
        return Mesh(
            self.vertices.to(device, non_blocking=non_blocking),
            self.faces.to(device, non_blocking=non_blocking),
            self.vertex_attrs.to(device, non_blocking=non_blocking) if self.vertex_attrs is not None else None,
        )
        
    def cuda(self, non_blocking=False):
        return self.to('cuda', non_blocking=non_blocking)
        
    def cpu(self):
        return self.to('cpu')
    
    def fill_holes(self, max_hole_perimeter=3e-2):
        if not (_CUMESH and torch.cuda.is_available()):
            # voxkiln: repaired later in the export chain (repair.py);
            # the flag lets reports say honestly what was deferred.
            self.fill_holes_deferred = True
            return
        vertices = self.vertices.cuda()
        faces = self.faces.cuda()

        mesh = cumesh.CuMesh()
        mesh.init(vertices, faces)
        mesh.get_edges()
        mesh.get_boundary_info()
        if mesh.num_boundaries == 0:
            return
        mesh.get_vertex_edge_adjacency()
        mesh.get_vertex_boundary_adjacency()
        mesh.get_manifold_boundary_adjacency()
        mesh.read_manifold_boundary_adjacency()
        mesh.get_boundary_connected_components()
        mesh.get_boundary_loops()
        if mesh.num_boundary_loops == 0:
            return
        mesh.fill_holes(max_hole_perimeter=max_hole_perimeter)
        new_vertices, new_faces = mesh.read()
        
        self.vertices = new_vertices.to(self.device)
        self.faces = new_faces.to(self.device)
        
    def remove_faces(self, face_mask: torch.Tensor):
        if not (_CUMESH and torch.cuda.is_available()):
            keep = ~face_mask.to(self.faces.device, torch.bool)
            self.faces = self.faces[keep]
            return
        vertices = self.vertices.cuda()
        faces = self.faces.cuda()

        mesh = cumesh.CuMesh()
        mesh.init(vertices, faces)
        mesh.remove_faces(face_mask)
        new_vertices, new_faces = mesh.read()
        
        self.vertices = new_vertices.to(self.device)
        self.faces = new_faces.to(self.device)
        
    def simplify(self, target=1000000, verbose: bool=False, options: dict={}):
        if not (_CUMESH and torch.cuda.is_available()):
            if self.faces.shape[0] <= target:
                return
            import fast_simplification  # CPU quadric decimation (MIT)
            import numpy as np
            v, f = fast_simplification.simplify(
                self.vertices.detach().cpu().numpy().astype(np.float32),
                self.faces.detach().cpu().numpy().astype(np.int64),
                target_count=int(target),
            )
            self.vertices = torch.from_numpy(np.ascontiguousarray(v)).float().to(self.device)
            self.faces = torch.from_numpy(np.ascontiguousarray(f)).int().to(self.vertices.device)
            return
        vertices = self.vertices.cuda()
        faces = self.faces.cuda()

        mesh = cumesh.CuMesh()
        mesh.init(vertices, faces)
        mesh.simplify(target, verbose=verbose, options=options)
        new_vertices, new_faces = mesh.read()
        
        self.vertices = new_vertices.to(self.device)
        self.faces = new_faces.to(self.device)


class TextureFilterMode:
    CLOSEST = 0
    LINEAR = 1


class TextureWrapMode:
    CLAMP_TO_EDGE = 0
    REPEAT = 1
    MIRRORED_REPEAT = 2


class AlphaMode:
    OPAQUE = 0
    MASK = 1
    BLEND = 2


class Texture:
    def __init__(
        self,
        image: torch.Tensor,
        filter_mode: TextureFilterMode = TextureFilterMode.LINEAR,
        wrap_mode: TextureWrapMode = TextureWrapMode.REPEAT
    ):
        self.image = image
        self.filter_mode = filter_mode
        self.wrap_mode = wrap_mode

    def to(self, device, non_blocking=False):
        return Texture(
            self.image.to(device, non_blocking=non_blocking),
            self.filter_mode,
            self.wrap_mode,
        )


class PbrMaterial:
    def __init__(
        self,
        base_color_texture: Optional[Texture] = None,
        base_color_factor: Union[torch.Tensor, List[float]] = [1.0, 1.0, 1.0],
        metallic_texture: Optional[Texture] = None,
        metallic_factor: float = 1.0,
        roughness_texture: Optional[Texture] = None,
        roughness_factor: float = 1.0,
        alpha_texture: Optional[Texture] = None,
        alpha_factor: float = 1.0,
        alpha_mode: AlphaMode = AlphaMode.OPAQUE,
        alpha_cutoff: float = 0.5,
    ):
        self.base_color_texture = base_color_texture
        self.base_color_factor = torch.tensor(base_color_factor, dtype=torch.float32)[:3]
        self.metallic_texture = metallic_texture
        self.metallic_factor = metallic_factor
        self.roughness_texture = roughness_texture
        self.roughness_factor = roughness_factor
        self.alpha_texture = alpha_texture
        self.alpha_factor = alpha_factor
        self.alpha_mode = alpha_mode
        self.alpha_cutoff = alpha_cutoff

    def to(self, device, non_blocking=False):
        return PbrMaterial(
            base_color_texture=self.base_color_texture.to(device, non_blocking=non_blocking) if self.base_color_texture is not None else None,
            base_color_factor=self.base_color_factor.to(device, non_blocking=non_blocking),
            metallic_texture=self.metallic_texture.to(device, non_blocking=non_blocking) if self.metallic_texture is not None else None,
            metallic_factor=self.metallic_factor,
            roughness_texture=self.roughness_texture.to(device, non_blocking=non_blocking) if self.roughness_texture is not None else None,
            roughness_factor=self.roughness_factor,
            alpha_texture=self.alpha_texture.to(device, non_blocking=non_blocking) if self.alpha_texture is not None else None,
            alpha_factor=self.alpha_factor,
            alpha_mode=self.alpha_mode,
            alpha_cutoff=self.alpha_cutoff,
        )


class MeshWithPbrMaterial(Mesh):
    def __init__(self,
        vertices,
        faces,
        material_ids,
        uv_coords,
        materials: List[PbrMaterial],
    ):
        self.vertices = vertices.float()
        self.faces = faces.int()
        self.material_ids = material_ids    # [M]
        self.uv_coords = uv_coords          # [M, 3, 2]
        self.materials = materials
        self.layout = {
            'base_color': slice(0, 3),
            'metallic': slice(3, 4),
            'roughness': slice(4, 5),
            'alpha': slice(5, 6),
        }

    def to(self, device, non_blocking=False):
        return MeshWithPbrMaterial(
            self.vertices.to(device, non_blocking=non_blocking),
            self.faces.to(device, non_blocking=non_blocking),
            self.material_ids.to(device, non_blocking=non_blocking),
            self.uv_coords.to(device, non_blocking=non_blocking),
            [material.to(device, non_blocking=non_blocking) for material in self.materials],
        )


class MeshWithVoxel(Mesh, Voxel):
    def __init__(self,
        vertices: torch.Tensor,
        faces: torch.Tensor,
        origin: list,
        voxel_size: float,
        coords: torch.Tensor,
        attrs: torch.Tensor,
        voxel_shape: torch.Size,
        layout: Dict = {},
    ):
        self.vertices = vertices.float()
        self.faces = faces.int()
        self.origin = torch.tensor(origin, dtype=torch.float32, device=self.device)
        self.voxel_size = voxel_size
        self.coords = coords
        self.attrs = attrs
        self.voxel_shape = voxel_shape
        self.layout = layout

    def to(self, device, non_blocking=False):
        return MeshWithVoxel(
            self.vertices.to(device, non_blocking=non_blocking),
            self.faces.to(device, non_blocking=non_blocking),
            self.origin.tolist(),
            self.voxel_size,
            self.coords.to(device, non_blocking=non_blocking),
            self.attrs.to(device, non_blocking=non_blocking),
            self.voxel_shape,
            self.layout,
        )
        
    def query_attrs(self, xyz):
        if _FLEX_GEMM and xyz.is_cuda:
            grid = ((xyz - self.origin) / self.voxel_size).reshape(1, -1, 3)
            vertex_attrs = grid_sample_3d(
                self.attrs,
                torch.cat([torch.zeros_like(self.coords[..., :1]), self.coords], dim=-1),
                self.voxel_shape,
                grid,
                mode='trilinear'
            )[0]
            return vertex_attrs
        grid = ((xyz - self.origin) / self.voxel_size).reshape(-1, 3)
        return _sparse_trilinear(self.attrs, self.coords, grid)
        
    def query_vertex_attrs(self):
        return self.query_attrs(self.vertices)
