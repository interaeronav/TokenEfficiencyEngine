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
from tee.assets.envelopes import envelope_for, load_envelopes, scale_policy
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
    adapter: str | None = None,
    asset_class: str | None = None,
    target_dims: list[float] | None = None,
    location: list[float] | None = None,
    rotation: list[float] | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    # A68: the lane is the one named, else the sole or declared one, else -
    # on an unbound multi-lane server - the one served lane that imports the
    # file's suffix, decided once the file is known. Never "blender" by name.
    if adapter is None and not app.unbound():
        adapter = app.resolve_adapter(None)
    # 1. scene reuse check (asset_in_scene lesson): same asset already
    #    placed -> report it instead of a second download/import. With no
    #    lane decided yet, every served lane's cache is checked.
    existing = []
    for scope in [adapter] if adapter is not None else list(app.adapters):
        app.warm(scope)
        cache = app.caches.get(scope)
        if cache is not None:
            existing += [
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
            # A rejection with no envelope and no target is not a bad asset -
            # it is a missing question. as_search labels every model hit
            # "model", which has no envelope, so say what would answer it.
            judged = asset_class or entry.get("class")
            if envelope_for(judged) is None and not target_dims:
                fix = (
                    f"Nothing to judge scale against: asset_class {judged!r} has no "
                    f"dimension envelope. Pass asset_class= one of "
                    f"{', '.join(sorted(load_envelopes()))}, or target_dims=[x, y, z] "
                    "in metres."
                )
            else:
                fix = (
                    "Check the asset's authored units, or pass target_dims=[x, y, z] "
                    "in metres to state the size you want."
                )
            raise TeeError("asset_rejected", f"{asset_ref}: {policy['note']}", fix=fix)
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
    source_path = (
        entry.get("path")
        if entry.get("source") == "local"
        else str(store.asset_dir(entry["hash"]) / entry["primary"])
    )
    if adapter is None:
        # A68: the one served lane that imports this suffix, declared
        adapter = app.importer_lane(source_path.rsplit(".", 1)[-1] if "." in source_path else "")
    dcc = app.adapters.get(adapter)
    if hasattr(dcc, "import_asset_file"):
        # Epic's AssetTools cannot import at all, and the sandboxed script lane
        # cannot reach the importer, so this runs through TEE's content plugin
        # rather than the typed batch. Checkpoint by hand to keep the same
        # rollback guarantee a batch would give.
        dcc = app.adapter(adapter)
        checkpoint = app.checkpoints.create(
            dcc, f"auto:import:{asset_ref}", app.cache(adapter).revision, lane=adapter
        )
        imported = dcc.import_asset_file(
            source_path,
            label=display,
            location=[v * 100.0 for v in (location or [0.0, 0.0, 0.0])],  # m -> cm
            scale=scale,
        )
        app.cache(adapter).resync(dcc)
        batch = {
            "checkpoint": checkpoint.id,
            "created": [imported["entity_id"]] if imported.get("entity_id") else [],
            "details": {imported.get("entity_id", "u?"): {"dims_m": imported.get("dims_m")}},
            **app.cache(adapter).stamp(),
        }
        ops = None
    elif app.vocab(adapter).accepts_op("import_file"):
        # Blender-shaped: the typed import_file op through the normal
        # checkpointed batch (found by what the lane declares, not its name)
        ops = [{"op": "import_file", "path": source_path, "name": display, "props": props}]
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
    if ops is not None:
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
