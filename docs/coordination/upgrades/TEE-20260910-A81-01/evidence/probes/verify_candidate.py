"""Fresh isolated MCP probes of both A81 deliveries, not client acceptance."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import socket
import subprocess
import time
import zipfile
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path("/Users/john/TokenEfficiencyEngine")
UPDATE = ROOT / "output/updates/TEE-20260910-A81-01"
OUT = UPDATE / "probes"
PYTHON = ROOT / "server/.venv/bin/python"
LANES = ["blender", "partkiln", "seamkiln", "fusion", "unreal"]
LEARNING = ["learn_status", "learn_feedback", "learn_recommend", "learn_evaluate", "learn_control"]
DOCUMENTATION = ["doc_status", "doc_prepare", "doc_run", "doc_diff", "doc_apply"]
COMMON = ["cadagent_enclosure", "cadagent_flange", "cadagent_joint", "cadagent_f1_wing",
          "cadagent_f1_brake", "cadagent_f1_wishbone"]
OLD = json.loads((ROOT / "output/updates/TEE-20260910-A79-A80-01/candidate-smoke.json").read_text())


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":")).encode()).hexdigest()


def unpack(archive: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as zipped:
        for entry in zipped.infolist():
            path = Path(entry.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe archive path")
        zipped.extractall(destination)
    return {"archive": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "extracted": str(destination)}


def complete_evidence(result: dict[str, Any]) -> dict[str, Any]:
    """Add independent extracted payload and previous learning contract checks."""
    old_learning = json.loads((OUT / "baseline-learning.json").read_text())
    expected_payload = {
        "sha256": "3d41e182129c82f62f8a6675685098a28d38061c6c232b9f894fe2667bc50e40",
        "files": 279,
        "bytes": 3166135,
    }
    payloads = []
    for delivery, relative in zip(result["deliveries"], ("src/tee", "server/src/tee")):
        root = Path(delivery["extracted"]) / relative
        rows = []
        for path in sorted(root.rglob("*")):
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"} or path.name == ".DS_Store":
                continue
            assert not path.is_symlink(), path
            if path.is_file():
                data = path.read_bytes()
                rows.append({"path": "tee/" + path.relative_to(root).as_posix(),
                             "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        identity = {"sha256": digest({"algorithm": "tee-payload-v1", "files": rows}),
                    "files": len(rows), "bytes": sum(row["bytes"] for row in rows)}
        assert identity == expected_payload, identity
        payloads.append({"extracted_source": str(root), **identity})
    label = Path(result["deliveries"][0]["extracted"]).parent.name
    for report in result["reports"]:
        hashes = {name: digest(report["descriptions"][name]) for name in LEARNING}
        comparisons = {name: hashes[name] == old_learning["sha256"][name] for name in LEARNING}
        report["learning_descriptor_sha256"] = hashes
        report["learning_descriptor_comparisons"] = comparisons
        report["checks"]["five_learning_descriptors_unchanged"] = all(comparisons.values())
        raw = OUT / f"{label}-{report['shape']}-{'corpus' if report['corpus'] else 'empty'}-core-schemas.json"
        assert digest(json.loads(raw.read_text())) == report["core_schema_sha256"]
        report["raw_core_schemas_file"] = str(raw)
        report["passed"] = all(report["checks"].values())
        per_report = raw.with_name(raw.name.replace("-core-schemas.json", ".json"))
        per_report.write_text(json.dumps(report, indent=2) + "\n")
    result["extracted_payloads"] = payloads
    result["all_learning_descriptors_unchanged"] = all(
        report["checks"]["five_learning_descriptors_unchanged"] for report in result["reports"]
    )
    result["all_guide_responses_unchanged"] = all(
        report["checks"]["all15_old_guides_unchanged"] for report in result["reports"]
    )
    result["all_doc_descriptors_equal"] = len({digest({
        name: report["descriptions"][name] for name in DOCUMENTATION
    }) for report in result["reports"]}) == 1
    result["passed"] = (len(result["reports"]) == 4 and all(report["passed"] for report in result["reports"])
                        and result["all_core_schemas_equal"] and result["all_doc_descriptors_equal"])
    return result


def hold_unserved_ports(stack: ExitStack) -> list[int]:
    ports = []
    for _ in range(5):
        sock = stack.enter_context(socket.socket())
        sock.bind(("127.0.0.1", 0))
        ports.append(sock.getsockname()[1])
    return ports


async def probe(shape: str, corpus: bool, source_root: Path, bundle: Path, label: str) -> dict:
    started = time.monotonic()
    project = OUT / "projects" / f"{label}-{shape}-{'corpus' if corpus else 'empty'}"
    project.mkdir(parents=True)
    (project / ".tee").mkdir()
    (project / "api.py").write_text("def greet(name):\n    return 'Hello ' + name\n")
    (project / "README.md").write_text("# Isolated documentation fixture\n")
    if corpus:
        (project / "knowledge-base").symlink_to(ROOT / "knowledge-base", target_is_directory=True)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("TEE_DOCAGENT_API_KEY", None)
    env.pop("PYTHONPATH", None)
    with ExitStack() as stack:
        ports = hold_unserved_ports(stack)
        (project / ".tee/config.toml").write_text(
            '[trust]\ngrants=["write-artifacts"]\n'
            '[llm]\nadapters=""\n'
            '[llm.profiles.fixture]\nmodel="fixture-no-inference"\n'
            f'url="http://127.0.0.1:{ports[4]}/v1"\nadapters=""\npaid=false\n'
        )
        (project / ".tee/llm-profile.json").write_text(
            '{"active":"fixture","pinned":true,"ready":true}\n'
        )
        if shape == "claude":
            manifest = json.loads((bundle / "manifest.json").read_text())
            config = manifest["server"]["mcp_config"]
            source = bundle / "src"
            origin = subprocess.check_output([
                str(PYTHON), "-c",
                "import runpy,sys; runpy.run_path(sys.argv[1]); import tee; print(tee.__file__)",
                str(bundle / "launch.py"),
            ], env=env, text=True).strip()
        else:
            source = source_root / "server/src"
            env["PYTHONPATH"] = str(source)
            config = {"command": str(PYTHON), "args": ["-m", "tee.cli", "serve"]}
            for lane in LANES:
                config["args"] += ["--adapter", lane]
            config["args"] += ["--project", "${user_config.project_root}"]
            origin = subprocess.check_output([
                str(PYTHON), "-c", "import tee; print(tee.__file__)",
            ], env=env, text=True).strip()
        assert Path(origin).is_relative_to(source), origin
        args = [value.replace("${__dirname}", str(bundle)).replace(
            "${user_config.project_root}", str(project)) for value in config["args"]]
        for name, port in zip(("blender", "unreal", "fusion", "fusion-http"), ports):
            args += [f"--{name}-port", str(port)]
        params = StdioServerParameters(command=config["command"], args=args, env=env)
        stderr_path = OUT / f"{label}-{shape}-{'corpus' if corpus else 'empty'}-server.log"
        with stderr_path.open("w") as errlog:
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write) as client:
                    init = (await client.initialize()).model_dump(by_alias=True)
                    schemas = sorted([tool.model_dump(by_alias=True, exclude_none=True)
                                      for tool in (await client.list_tools()).tools],
                                     key=lambda tool: tool["name"])

                    async def call(name: str, arguments: dict, *, ok: bool = True) -> dict:
                        result = await client.call_tool(name, arguments)
                        body = json.loads(next(block.text for block in result.content
                                               if block.type == "text"))
                        assert body.get("ok") is ok, body
                        return body

                    async def virtual(name: str, arguments: dict | None = None, *, ok=True) -> dict:
                        return await call("tee_call", {"name": name, "args": arguments or {}}, ok=ok)

                    status = await call("tee_status", {})
                    learning = await virtual("learn_status")
                    descriptions = {}
                    for name in [*LEARNING, *DOCUMENTATION]:
                        descriptions[name] = await call("tee_describe_tool", {"name": name})
                    guides = {}
                    for lane, topics in [("fusion", COMMON),
                                         ("blender", [*COMMON, "house", "textures", "fabric"])]:
                        for topic in topics:
                            guide = await virtual("lane_guide", {"adapter": lane, "topic": topic})
                            guides[f"{lane}/{topic}"] = {
                                "response_sha256": digest(guide), "offline": guide.get("offline"),
                                "topic": guide.get("topic"),
                            }
                    docs = await virtual("doc_status")
                    prepared = await virtual("doc_prepare", {
                        "inputs": ["api.py"], "outputs": ["README.md"],
                        "instruction": "Describe greet from its source; isolated package probe.",
                    })
                    initial_diff = await virtual("doc_diff", {"run_id": prepared["run_id"]})
                    assert initial_diff["changes"] == []
                    refused = await virtual("doc_run", {
                        "run_id": prepared["run_id"], "backend": "aider",
                    }, ok=False)
                    assert "run-doc-agent" in json.dumps(refused), refused
                    # Only the owned harness supplies this fixture candidate;
                    # no documentation worker/model runs in this package probe.
                    candidate = Path(prepared["work_dir"]) / "README.md"
                    candidate.write_text("# Isolated documentation fixture\n\n`greet` adds Hello.\n")
                    changed_diff = await virtual("doc_diff", {"run_id": prepared["run_id"]})
                    assert len(changed_diff["changes"]) == 1
                    apply_refused = await virtual("doc_apply", {
                        "run_id": prepared["run_id"],
                        "review_sha256": changed_diff["review_sha256"],
                    }, ok=False)
                    assert "doc_not_completed" in json.dumps(apply_refused), apply_refused
                    checks = {
                        "core_count_17": len(schemas) == 17,
                        "complete_core_schemas_unchanged": digest(schemas) == OLD["reports"][0]["core_schema_sha256"],
                        "virtual_count_expected": status["virtual_tools"] == (250 if corpus else 246),
                        "five_adapters": list(status["adapters"]) == LANES,
                        "all15_old_guides_unchanged": guides == OLD["reports"][0]["guide_checks"],
                        "five_learning_descriptors": all(name in descriptions for name in LEARNING),
                        "five_doc_descriptors": all(name in descriptions for name in DOCUMENTATION),
                        "execution_disabled_without_grant": docs["execution_allowed"] is False,
                        "worker_versions": all(docs["workers"][name]["version"] == version
                                               for name, version in [("aider", "0.86.2"), ("cline", "3.0.61")]),
                        "grant_refusal": refused.get("ok") is False,
                        "prepare_and_diff": changed_diff["ok"] and len(changed_diff["changes"]) == 1,
                        "apply_requires_worker_completion": apply_refused.get("ok") is False,
                        "fixture_original_unchanged": (project / "README.md").read_text() == "# Isolated documentation fixture\n",
                        "code_exec_disabled": status["code_exec_enabled"] is False,
                        "root_is_disposable_fixture": status["rooted_at"]["project_root"] == str(project),
                    }
                    report = {
                        "scope": "fresh isolated harness; not actual Claude/Codex client acceptance",
                        "shape": shape, "corpus": corpus, "source_origin": origin,
                        "protocol": init["protocolVersion"], "server": init["serverInfo"],
                        "core_schema_sha256": digest(schemas), "core_count": len(schemas),
                        "virtual_tools": status["virtual_tools"], "guide_checks": guides,
                        "learning_status": learning, "doc_status": docs,
                        "descriptions": descriptions, "grant_refusal": refused,
                        "apply_refusal": apply_refused, "diff": changed_diff,
                        "checks": checks, "passed": all(checks.values()),
                        "gui_bridge_endpoints": "reserved non-listening local fixture ports",
                        "models_invoked": False, "actual_gui_dcc_contact": False,
                        "seconds": round(time.monotonic() - started, 3),
                    }
                    prefix = f"{label}-{shape}-{'corpus' if corpus else 'empty'}"
                    (OUT / f"{prefix}-core-schemas.json").write_text(json.dumps(schemas, indent=2) + "\n")
                    (OUT / f"{prefix}.json").write_text(json.dumps(report, indent=2) + "\n")
                    assert report["passed"], checks
                    return report


async def main() -> None:
    label = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    artifacts = UPDATE / "artifacts"
    bundle = OUT / "extracted" / label / "claude"
    snapshot = OUT / "extracted" / label / "codex"
    delivered = [
        unpack(artifacts / "tee-engine-0.30.1-a81-local.mcpb", bundle),
        unpack(artifacts / "tee-a81-codex-source-snapshot.zip", snapshot),
    ]
    reports = []
    for corpus in (False, True):
        for shape in ("claude", "codex"):
            report = await asyncio.wait_for(probe(shape, corpus, snapshot, bundle, label), timeout=90)
            reports.append(report)
            print(json.dumps({key: report[key] for key in
                              ("shape", "corpus", "passed", "core_count", "virtual_tools", "seconds")}), flush=True)
    result = {"scope": "fresh isolated delivery harness, not actual recipient acceptance",
              "passed": all(report["passed"] for report in reports), "deliveries": delivered,
              "all_core_schemas_equal": len({row["core_schema_sha256"] for row in reports}) == 1,
              "reports": reports}
    result = complete_evidence(result)
    path = OUT / "candidate-smoke.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(str(path), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
