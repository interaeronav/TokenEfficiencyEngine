"""Backend probe, structured refusal, and the pipeline loader.

Everything torch-shaped is lazy: `import voxkiln` and `voxkiln doctor`
work on machines with no GPU stack and answer with the exact gap instead
of a stack trace (decision A28 requirement 7). The real pipeline runs
only on a machine with MPS or CUDA + the [model] extra + weights; its
first live validation happens on the physical Mac (script 13.6.3).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import voxkiln

# Estimates for the submit ack (decision A28 requirement 6), from measured
# stage tables in research 45 (M4 Pro figures; the doctor labels them
# "estimate" until the Mac battery replaces them with measured rows).
_ESTIMATES = {
    "512": {"est_seconds": 210, "est_peak_mem_gb": 18},
    "1024": {"est_seconds": 480, "est_peak_mem_gb": 28},
    "1024_cascade": {"est_seconds": 600, "est_peak_mem_gb": 30},
    "1536_cascade": {"est_seconds": 900, "est_peak_mem_gb": 40},
}


class EngineUnavailable(RuntimeError):
    """Structured refusal - never a hang, never a bare stack trace."""

    def __init__(self, code: str, message: str, fix: str):
        super().__init__(message)
        self.payload = {"error": code, "message": message, "fix": fix}


def _vendor_paths() -> list[Path]:
    here = Path(__file__).resolve().parent
    for base in (here / "_vendor", here.parent.parent / "vendor"):
        if (base / "trellis2").exists():
            return [base, base / "o-voxel"]
    return []


def add_vendor_to_path() -> None:
    for p in _vendor_paths():
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)


def probe() -> dict[str, Any]:
    """One compact answer: which backend can run the pipeline here."""
    try:
        import torch
    except ImportError:
        return {
            "backend": None,
            "fix": "install the model stack: pip install 'voxkiln[model]' "
            "(Apple Silicon: torch>=2.13 recommended for FlexAttention-MPS)",
        }
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        return {
            "backend": "cuda",
            "device": torch.cuda.get_device_name(0),
            "vram_gb": round(props.total_memory / 2**30, 1),
            "torch": torch.__version__,
        }
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return {
            "backend": "mps",
            "device": "Apple Silicon (unified memory)",
            "torch": torch.__version__,
        }
    return {
        "backend": None,
        "torch": torch.__version__,
        "fix": "no CUDA or MPS device - voxkiln needs Apple Silicon or an NVIDIA GPU; "
        "hosted fallback: TEE's tripo/meshy drivers",
    }


def estimate(pipeline_type: str) -> dict[str, Any]:
    est = dict(_ESTIMATES.get(pipeline_type, _ESTIMATES["1024_cascade"]))
    est["basis"] = "estimate (M4 Pro measurements, research 45); Mac battery replaces these"
    return est


def require_backend() -> dict[str, Any]:
    p = probe()
    if p.get("backend") is None:
        raise EngineUnavailable(
            "no_backend",
            "no device can run the generation pipeline here",
            p.get("fix", "install voxkiln[model] on Apple Silicon or CUDA hardware"),
        )
    return p


def doctor() -> dict[str, Any]:
    """Engine health for `voxkiln doctor` and the gen3d_status tool."""
    checks: dict[str, Any] = {
        "version": voxkiln.__version__,
        "upstream_commit": voxkiln.UPSTREAM_COMMIT,
        "vendor_tree": bool(_vendor_paths()),
        "probe": probe(),
    }
    try:
        from huggingface_hub import scan_cache_dir

        cache = scan_cache_dir()
        repos = {r.repo_id: round(r.size_on_disk / 2**30, 2) for r in cache.repos}
        checks["weights_cached_gb"] = repos.get(voxkiln.MODEL_REPO)
    except BaseException:
        checks["weights_cached_gb"] = None
    deps = {}
    for name in ("trimesh", "fast_simplification", "xatlas", "cv2", "manifold3d"):
        try:
            __import__(name)
            deps[name] = True
        except ImportError:
            deps[name] = False
    checks["deps"] = deps
    return checks


class Engine:
    """The real pipeline runner. Loads the vendored TRELLIS.2 fork lazily,
    keeps it resident (no low_vram model ping-pong on big-memory machines),
    and hands raw outputs to voxkiln.export."""

    def __init__(self, model_repo: str = voxkiln.MODEL_REPO, revision: str | None = None):
        self.model_repo = model_repo
        self.revision = revision
        self._pipeline = None
        self.backend = None

    def load(self) -> None:
        if self._pipeline is not None:
            return
        info = require_backend()
        self.backend = info["backend"]
        add_vendor_to_path()
        import os

        if self.backend == "mps":
            # segment_reduce and a few other ops still lack MPS kernels
            os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
            os.environ.setdefault("SPARSE_ATTN_BACKEND", "sdpa")
            os.environ.setdefault("SPARSE_CONV_BACKEND", "none")
        else:
            for candidate, env in (("flash_attn", "flash_attn"), ("xformers", "xformers")):
                try:
                    __import__(candidate)
                    os.environ.setdefault("SPARSE_ATTN_BACKEND", env)
                    break
                except ImportError:
                    continue
            else:
                os.environ.setdefault("SPARSE_ATTN_BACKEND", "sdpa")
            try:
                import flex_gemm  # noqa: F401
            except ImportError:
                os.environ.setdefault("SPARSE_CONV_BACKEND", "none")

        import torch
        from trellis2.pipelines import Trellis2ImageTo3DPipeline

        path = self.model_repo
        if self.revision:
            from huggingface_hub import snapshot_download

            path = snapshot_download(self.model_repo, revision=self.revision)
        pipeline = Trellis2ImageTo3DPipeline.from_pretrained(path)
        # Residency (research 45): with unified/large memory, model
        # ping-pong is pure latency. Keep everything loaded.
        pipeline.low_vram = False
        device = torch.device(self.backend)
        pipeline.to(device)
        pipeline.image_cond_model.to(device)
        if pipeline.rembg_model is not None:
            pipeline.rembg_model.to(device)
        self._pipeline = pipeline

    def generate(self, image, seed: int, params: dict[str, Any]) -> dict[str, Any]:
        """Run the pipeline; returns raw arrays for the export chain plus
        the pipeline's own run report (resolution downgrades etc.)."""
        self.load()
        started = time.monotonic()
        meshes = self._pipeline.run(
            image,
            seed=seed,
            pipeline_type=params.get("pipeline_type"),
            max_num_tokens=params.get("max_num_tokens", 49152),
        )
        m = meshes[0]
        sample_s = time.monotonic() - started
        from voxkiln.export import VoxelAttrs

        voxel = VoxelAttrs(
            coords=m.coords.detach().cpu().numpy(),
            attrs=m.attrs.detach().float().cpu().numpy(),
            origin=m.origin.detach().cpu().numpy(),
            voxel_size=float(m.voxel_size),
            layout={k: v for k, v in m.layout.items()},
        )
        notices = []
        run_report = getattr(self._pipeline, "last_run_report", {})
        if "resolution_downgraded" in run_report:
            d = run_report["resolution_downgraded"]
            notices.append(
                f"resolution downgraded {d['requested']} -> {d['actual']} ({d['reason']})"
            )
        if getattr(m, "fill_holes_deferred", False):
            notices.append("decode-time hole fill deferred to the export repair stage")
        return {
            "vertices": m.vertices.detach().cpu().numpy(),
            "faces": m.faces.detach().cpu().numpy(),
            "voxel": voxel,
            "notices": notices,
            "timings": {"pipeline_s": sample_s},
            "run_report": run_report,
        }


class FakeEngine:
    """Deterministic stand-in carrying the Engine contract for tests and
    for TEE's fakes: a unit cube whose attribute volume colors each octant
    differently - enough signal to validate the whole export/bake path."""

    backend = "fake"

    def __init__(self, resolution: int = 16):
        self.resolution = resolution

    def load(self) -> None:  # pragma: no cover - nothing to load
        return

    def generate(self, image, seed: int, params: dict[str, Any]) -> dict[str, Any]:
        import numpy as np
        import trimesh as tm

        from voxkiln.export import DEFAULT_LAYOUT, VoxelAttrs

        rng = np.random.default_rng(seed)
        box = tm.creation.box(extents=(1.0, 1.0, 1.0))
        box = box.subdivide()
        res = self.resolution
        grid = np.stack(
            np.meshgrid(np.arange(res), np.arange(res), np.arange(res), indexing="ij"), axis=-1
        ).reshape(-1, 3)
        centers = (grid + 0.5) / res - 0.5
        shell = np.abs(centers).max(axis=1) > (0.5 - 2.0 / res)
        coords = grid[shell]
        centers = centers[shell]
        octant = (centers > 0).astype(float)
        attrs = np.zeros((len(coords), 6))
        attrs[:, 0:3] = 0.15 + 0.7 * octant  # base color by octant
        attrs[:, 3] = 0.0  # metallic
        attrs[:, 4] = 0.8  # roughness
        attrs[:, 5] = 1.0  # alpha
        attrs[:, 0] += rng.normal(0, 1e-4, len(coords))  # seed-sensitive
        voxel = VoxelAttrs(
            coords=coords,
            attrs=attrs.clip(0, 1),
            origin=np.array([-0.5, -0.5, -0.5]),
            voxel_size=1.0 / res,
            layout=dict(DEFAULT_LAYOUT),
        )
        return {
            "vertices": np.asarray(box.vertices),
            "faces": np.asarray(box.faces),
            "voxel": voxel,
            "notices": ["fake engine output (no GPU pipeline in this environment)"],
            "timings": {"pipeline_s": 0.0},
            "run_report": {"seed": seed, "pipeline_type": params.get("pipeline_type", "fake")},
        }
