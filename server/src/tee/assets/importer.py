"""Asset import (9.3): cache-or-reuse → probe → scale policy → typed batch
→ read-back verification.

Order of checks is the BlenderKit lesson: scene first, cache second,
network last. All scene mutation goes through the NORMAL run_batch
machinery (checkpointed, diff-reported) - import is not a side channel.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

from tee.assets import gltf
from tee.assets.envelopes import scale_policy
from tee.assets.http import fetch_bytes
from tee.kernel.errors import TeeError

_VERIFY_TOLERANCE = 0.05  # read-back dims within 5% (rotation-no-op lesson)


def ensure_cached(store, backends: dict[str, Any], asset_ref: str) -> dict[str, Any]:
    """Return the store entry for `source:id`, downloading (license-gated)
    if it is not cached yet. Local entries pass straight through."""
    entry = store.entry(asset_ref)
    if entry is not None:
        return entry
    source, _, source_id = asset_ref.partition(":")
    if source == "local":
        raise TeeError(
            "unknown_asset",
            f"No local asset '{asset_ref}' in the index.",
            fix="Index your library first: as_ingest(directory=...).",
        )
    backend = backends.get(source)
    if backend is None:
        raise TeeError(
            "unknown_backend",
            f"No enabled backend '{source}'.",
            fix=f"Enabled: {', '.join(sorted(backends)) or '(none)'}. "
            "Keys/opt-ins are configured under [assets] in .tee/config.toml.",
        )
    plan = backend.resolve(source_id)
    if not plan.files:
        raise TeeError(
            "no_download",
            f"{asset_ref}: the backend offered no downloadable files.",
            fix="Pick another search hit.",
        )
    files: list[tuple[str, bytes]] = []
    for rel, url, md5 in plan.files:
        data = fetch_bytes(url, headers=plan.headers or None)
        if md5:
            import hashlib

            actual = hashlib.md5(data).hexdigest()
            if actual != md5.lower():
                raise TeeError(
                    "checksum_mismatch",
                    f"MD5 mismatch for {rel} of {asset_ref}.",
                    fix="Retry; if it persists the backend catalog is stale.",
                )
        files.append((rel, data))
    # zip bundles (ambientCG, Sketchfab) are unpacked into the store so the
    # primary payload is directly usable
    if len(files) == 1 and files[0][0].endswith(".zip"):
        files = _unpack_zip(files[0][1], asset_ref) or files
    return store.add_asset(
        source=plan.source,
        source_id=plan.source_id,
        name=plan.name,
        license_id=plan.license_id,
        files=files,
        attribution=plan.attribution,
        meta=plan.meta,
    )


def _unpack_zip(data: bytes, asset_ref: str) -> list[tuple[str, bytes]] | None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return None
    out: list[tuple[str, bytes]] = []
    for info in archive.infolist():
        if info.is_dir():
            continue
        rel = Path(info.filename)
        if rel.is_absolute() or ".." in rel.parts:  # zip-slip (prior-art CVE class)
            raise TeeError(
                "bad_archive",
                f"{asset_ref}: archive member escapes its directory ('{info.filename}').",
            )
        out.append((str(rel), archive.read(info)))
    # primary first: prefer glTF/GLB, then anything model-ish
    out.sort(
        key=lambda pair: (
            0
            if pair[0].lower().endswith((".gltf", ".glb"))
            else 1
            if pair[0].lower().endswith((".obj", ".fbx"))
            else 2
        )
    )
    return out or None


def measure(store, entry: dict[str, Any]) -> tuple[list[float] | None, str | None]:
    """Measured [x, y, z] dims in meters (Z-up) for a cached/local asset."""
    if entry.get("dims_m"):
        return list(entry["dims_m"]), "catalog"
    path = (
        Path(entry["path"])
        if entry.get("source") == "local" and entry.get("path")
        else store.asset_dir(entry["hash"]) / entry["primary"]
        if entry.get("hash")
        else None
    )
    if path and path.suffix.lower() in (".gltf", ".glb") and path.exists():
        probed = gltf.probe(path)
        dims = probed.get("dims_zup_m")
        if dims:
            return dims, "gltf_probe"
    return None, None


def import_asset(
    app,
    store,
    backends: dict[str, Any],
    asset_ref: str,
    *,
    adapter: str = "blender",
    asset_class: str | None = None,
    target_dims: list[float] | None = None,
    location: list[float] | None = None,
    rotation: list[float] | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    # 1. scene reuse check (asset_in_scene lesson): same asset already
    #    placed -> report it instead of a second download/import
    app.warm(adapter)
    cache = app.caches.get(adapter)
    existing = []
    if cache is not None:
        existing = [
            e.id for e in cache.entities.values() if e.summary.get("asset_key") == asset_ref
        ]

    # 2. cache-or-download
    entry = ensure_cached(store, backends, asset_ref)

    # 3. measure + 4. scale policy
    measured, how = measure(store, entry)
    policy: dict[str, Any] | None = None
    scale = 1.0
    if measured:
        policy = scale_policy(
            measured, asset_class=asset_class or entry.get("class"), target=target_dims
        )
        if policy["band"] == "reject":
            raise TeeError("asset_rejected", f"{asset_ref}: {policy['note']}")
        scale = policy["scale"]

    # 5. typed batch through the normal machinery
    display = name or entry.get("name") or asset_ref
    props: dict[str, Any] = {"asset_key": asset_ref}
    if location:
        props["location"] = location
    if rotation:
        props["rotation_euler"] = rotation
    if scale != 1.0:
        props["scale"] = [scale, scale, scale]
    if adapter == "blender":
        path = (
            entry.get("path")
            if entry.get("source") == "local"
            else str(store.asset_dir(entry["hash"]) / entry["primary"])
        )
        ops = [{"op": "import_file", "path": path, "name": display, "props": props}]
    else:
        if measured:
            props["dims_m"] = [round(v * scale, 4) for v in measured]
        ops = [
            {
                "op": "create",
                "kind": entry.get("class", "model"),
                "name": display,
                "props": props,
            }
        ]
    batch = app.run_batch(adapter, ops, label=f"import:{asset_ref}")

    # 6. read-back verification: expected dims vs the DCC's reported dims
    verification: dict[str, Any] | None = None
    if measured and batch.get("details"):
        expected = [v * scale for v in measured]
        for detail in batch["details"].values():
            got = detail.get("dimensions") or detail.get("dims_m")
            if not got:
                continue
            deviation = _max_deviation(sorted(got), sorted(expected))
            verification = {
                "expected_dims": [round(v, 4) for v in expected],
                "read_back": [round(float(v), 4) for v in got],
                "ok": deviation <= _VERIFY_TOLERANCE,
            }
            if not verification["ok"]:
                verification["note"] = (
                    f"read-back deviates {deviation:.0%} from expected - "
                    "check units/axis of the source asset"
                )
            break

    out: dict[str, Any] = {
        "ok": True,
        "asset": asset_ref,
        "name": display,
        "license": entry.get("license"),
        **{k: batch[k] for k in ("checkpoint", "epoch", "revision", "created") if k in batch},
    }
    if policy:
        out["scale_band"] = policy["band"]
        if scale != 1.0:
            out["scale"] = scale
        if policy.get("fact"):
            out["scale_fact"] = policy["fact"]
        if how:
            out["measured_via"] = how
    if verification:
        out["verify"] = verification
    if existing:
        out["note"] = f"asset was already in the scene as {existing[:3]} - now placed twice"
    return out


def _max_deviation(got: list[float], expected: list[float]) -> float:
    worst = 0.0
    for g, e in zip(got, expected, strict=False):
        if e > 1e-6:
            worst = max(worst, abs(g - e) / e)
    return worst
