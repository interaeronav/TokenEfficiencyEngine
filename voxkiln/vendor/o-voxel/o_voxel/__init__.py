# voxkiln vendor surgery: submodules load lazily. Upstream imported
# postprocess (nvdiffrast + cumesh + flex_gemm - NVIDIA non-commercial /
# CUDA-only) and io (plyfile - GPL) eagerly, which made `import o_voxel`
# impossible on a clean machine. postprocess itself is NOT vendored; its
# replacement is voxkiln.export. See vendor/VENDOR.md.
import importlib

__submodules = ['convert', 'io', 'rasterize', 'serialize']

__all__ = list(__submodules)


def __getattr__(name):
    if name in __submodules:
        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__} has no attribute {name}")
