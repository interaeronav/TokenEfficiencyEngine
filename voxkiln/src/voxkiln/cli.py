"""CLI: one blocking `gen` command with a JSON report on stdout and an
exit code that IS the budget verdict (0 accepted / 1 rejected or failed) -
pipeline- and agent-friendly."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voxkiln", description="AI-first local image-to-3D")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("gen", help="generate a 3D asset from an image")
    gen.add_argument("image")
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument(
        "--pipeline",
        default="1024_cascade",
        choices=["512", "1024", "1024_cascade", "1536_cascade"],
    )
    gen.add_argument("--texture-size", type=int, default=1024)
    gen.add_argument("--target-faces", type=int, default=500_000)
    gen.add_argument("--repair", default="fast", choices=["fast", "manifold", "rebuild"])
    gen.add_argument("--max-tris", type=int)
    gen.add_argument("--watertight", action="store_true")
    gen.add_argument("--target-size-m", type=float)
    gen.add_argument("--out", default="voxkiln_out")
    # CLI one-shot: wait for completion by default. A bounded wait that
    # expires kills the job with the process, so the 900 s API default is
    # wrong here - export alone can out-run it (measured >12 min, 2026-08-26).
    # Pass an explicit --timeout to get the resumable-timeout response.
    gen.add_argument("--timeout", type=float, default=None)
    gen.add_argument("--no-cache", action="store_true")

    show = sub.add_parser("show", help="show a job/asset report")
    show.add_argument("job_id")

    sub.add_parser("jobs", help="list jobs in this session")
    sub.add_parser("doctor", help="engine health: backend, weights, deps")

    fetch = sub.add_parser("fetch-weights", help="download model weights to the HF cache")
    fetch.add_argument("--revision", help="pin a full HF commit hash")

    sub.add_parser("serve", help="run the MCP server over stdio (4 tools)")

    args = parser.parse_args(argv)

    if args.command == "doctor":
        from voxkiln.engine import doctor

        print(json.dumps(doctor(), indent=1, default=str))
        return 0

    if args.command == "fetch-weights":
        import voxkiln

        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            print(json.dumps({"error": "no_hub", "fix": "pip install 'voxkiln[model]'"}))
            return 1
        path = snapshot_download(voxkiln.MODEL_REPO, revision=args.revision)
        print(json.dumps({"ok": True, "path": path, "revision": args.revision or "latest"}))
        return 0

    if args.command == "serve":
        from voxkiln.mcp_server import build_server

        build_server().run()
        return 0

    from voxkiln.engine import EngineUnavailable
    from voxkiln.jobs import JobStore

    store = JobStore(
        out_dir=getattr(args, "out", "voxkiln_out"), use_cache=not getattr(args, "no_cache", False)
    )

    if args.command == "jobs":
        print(json.dumps({jid: j.state for jid, j in store.jobs.items()}, indent=1))
        return 0

    if args.command == "show":
        try:
            print(json.dumps(store.query(args.job_id), indent=1, default=str))
            return 0
        except KeyError as exc:
            print(json.dumps({"error": "unknown_job", "message": str(exc)}))
            return 1

    # gen
    budget = {}
    if args.max_tris is not None:
        budget["max_tris"] = args.max_tris
    if args.watertight:
        budget["require_watertight"] = True
    if args.target_size_m is not None:
        budget["target_size_m"] = args.target_size_m
    params = {
        "pipeline_type": args.pipeline,
        "texture_size": args.texture_size,
        "target_faces": args.target_faces,
        "repair_level": args.repair,
    }
    try:
        result = store.generate(
            args.image,
            params=params,
            budget=budget or None,
            seed=args.seed,
            timeout_s=args.timeout,
        )
    except EngineUnavailable as exc:
        print(json.dumps(exc.payload, indent=1))
        return 1
    except FileNotFoundError as exc:
        print(json.dumps({"error": "bad_input", "message": str(exc)}, indent=1))
        return 1
    print(json.dumps(result, indent=1, default=str))
    if result.get("state") == "done" and result.get("verdict", {}).get("accepted", False):
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
