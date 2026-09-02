{
 "claims": [
  {
   "claim": "D6: sub-shape roles are materialised from merged `BRepTools_History` via `Generated/Modified/IsDeleted`.",
   "refuted": true,
   "evidence": "server/.venv (cadquery-ocp 7.9.3.1.1): `[m for m in dir(OCP.BRepTools.BRepTools_History) if m in ('Generated','Modified','IsRemoved','IsDeleted','Merge')]` prints `['Generated', 'IsRemoved', 'Merge', 'Modified']` - there is no `IsDeleted`. `ShapeUpgrade_UnifySameDomain.History()` and `AllowInternalEdges` are bound (verified), so the merge step the plan describes is otherwise sound.",
   "fix": "In D6 and history.py write `IsRemoved(shape)` (OCCT's name) and merge with `BRepTools_History.Merge(unify.History())`; keep the `<px>_ref_stale` message text 'deleted by hole h' if you like, but the API call is IsRemoved."
  },
  {
   "claim": "D2: the sidecar interpreter and `batch_timeout_s` are overridable from `.tee/config.toml` under a `[<kiln>]` section, and `server/src/tee/config.py` is not in the MODIFY list.",
   "refuted": true,
   "evidence": "server/src/tee/config.py:60-77 `ProjectConfig` is a fixed dataclass (assets, pins, kb, web, llm, gateway, capture, scheduler, trust, senses, pipeline, ...); `load()` :81-175 only does `data.get(\"assets\")`, `data.get(\"scheduler\")` etc. - grep for any generic passthrough (`data.items()`, `.sections`, `config.raw`) returns nothing, so an unknown `[<kiln>]` table is silently dropped. The precedent the plan cites, `fleet/cad.py:209-212 _sidecar_python(spec)`, reads `cad_python` from the TOOL-CALL args (`spec`), not from config. `app.py:147-160` re-reads config.toml only through `ProjectConfig.load`.",
   "fix": "Add `server/src/tee/config.py` to the MODIFY table: a `<kiln>: dict[str, Any] = field(default_factory=dict)` field plus a `data.get(\"<kiln>\", {})` block mirroring `scheduler` (:161-164), and have `_build_<kiln>_app` read `app.config.<kiln>` for `python` and `batch_timeout_s`. Alternatively drop the config claim and accept the interpreter as a per-call arg exactly like `cad_python`."
  },
  {
   "claim": "Version bump x3 at `server/Makefile:8` / `packaging/mcpb_manifest.json:5` / `server/pyproject.toml:3`.",
   "refuted": true,
   "evidence": "`sed -n 3,4p server/pyproject.toml` -> line 3 `name = \"tee-engine\"`, line 4 `version = \"0.19.0\"`. Makefile:8 `TEE_SERVER_VERSION ?= 0.19.0` and manifest:5 `\"version\": \"0.19.0\"` are correct. The E3 report (afa326944037ca372.md, section 10) repeats the same `:3` error, so the plan inherited it.",
   "fix": "Cite `server/pyproject.toml:4` in the touch list and in P6; keep :8 and :5."
  },
  {
   "claim": "`SidecarKernel` is copied from `gateway/wire.py:70-227` (NDJSON, `Popen(bufsize=0)`, `select()` 1 s ticks, `_dead()` naming exit code).",
   "refuted": true,
   "evidence": "`wc -l server/src/tee/gateway/wire.py` = 225 lines, so `:70-227` overruns the file. The pieces exist at: `class StdioBackendWire` :32, `start()` :60 with `bufsize=0` :75, `_read_message(deadline)` :183-215 (newline framing, skips blank/non-JSON/non-dict lines, `select.select(..., min(remaining, 1.0))` :207, `gateway_timeout` :200-205), `_dead(during)` :217-225 naming `exit {code}` and `self.stderr_path`.",
   "fix": "Cite `gateway/wire.py:32-225` (or `:60-225` for the spawn+reader half) and preserve two behaviours the copy must keep: the non-JSON-line skip in `_read_message` (OCCT chatter insurance on top of the fd-swap) and `_dead()`'s `close()` before raising."
  },
  {
   "claim": "Orientation: server suite = 1,224 passed / 17 skipped / 97 dcc-deselected; surface = 17 always-loaded tools = 2,033 tok; the tree carries staged A65 seamkiln work.",
   "refuted": false,
   "evidence": "docs/PROGRESS.md:9862-9864 records exactly that line. Today, `server/.venv/bin/python -m pytest tests -q --collect-only -p no:cacheprovider` -> `1225/1338 tests collected (113 deselected)`; per marker with `-o addopts=\"\"`: dcc 97, ml 2, network 8, llm 6 (=113; addopts at server/pyproject.toml:158 deselects all four). `run_surface_scenario()` alone prints `surface: 17 always-loaded tools = 2033 tok on the wire (2500 by model_dump); 126 virtual tools ...`; `len(tee.server._DESC) == 17`. `git status --short`: staged (`M `/`A `) seamkiln files incl. `_blender_body.py`, three tests (test_avatar, test_collision_symmetry_locks, test_figure_dressing) plus `drape/garment.py` which the plan's list omits.",
   "fix": "None required. When quoting the raw pytest line into PROGRESS say '113 deselected (97 dcc + 16 ml/network/llm)' so the number reconciles; add `drape/garment.py` and `test_avatar.py` to the pre-P0a commit's subject."
  },
  {
   "claim": "TEE seams (fact 13 / touch list): `app.py:204-211` metadata-only registration, `app.py:301-304` snapshot-before-execute, `cli.py:47-57/:244-247/:250-251/:333`, `trust.py:164-192/:179-188/:193-363/:293-295`, `checkpoints.py:105-113`, `fleet/cad.py:206`, `script.py:29`, `test_server_lint.py:82`, `test_gateway.py:168`, `purge.py:78-88`, `doctor.py:254-299/:562-578`, `_cad_worker.py:63-77`, `physical/sketch.py:209`.",
   "refuted": false,
   "evidence": "All verified at the cited lines: `register_seamkiln_tools(self)` app.py:211; `cp = self.checkpoints.create(...)` :302 then `adapter.execute(ops)` :304; `_build_seamkiln_app` cli.py:47; `elif args.adapter == \"godot\"` :246-247; error string :249-253; `--adapter` help :332-334 (no `choices=`); `_FAMILY` trust.py:164, cad_/trade_ comment :179-188, `_EXPLICIT` :193-363, cad rows :293-295, `capability_for` :365; `_discard` checkpoints.py:105-113 (also called from `rollback` :86 and `discard_all` :91); `SIDECAR_PY` cad.py:206; `MAX_SECONDS = 120.0` script.py:29; `EXPECTED_TOOL_COUNT = 17` test_server_lint.py:82; `test_always_loaded_surface_delta_is_zero` test_gateway.py:168; `\"sidecars\"` purge.py:78-82 excluded from `DEFAULT_CATEGORIES` :88; `check_voxkiln` doctor.py:254, `run_checks` :562-578 (14 checks, no freecad/seamkiln check today); fd-swap `_cad_worker.py:63-77`; sketch.py:209 is literally `free_allowance = 0 if anchored else 3  # translation x2 + rotation`. ONE gap: `run_batch` calls `self.warm(adapter_name)` at app.py:300 BEFORE the snapshot; `warm()` :272-281 calls `adapter.probe()` and then `cache.resync(adapter)` -> `adapter.list_entities()` on first contact.",
   "fix": "In D2 state that `list_entities()` (not only `probe()` and `snapshot()`) must answer from the in-process mirror while the kernel is warming, because the kernel's first batch triggers `warm()` -> `list_entities()` before the checkpoint is even taken."
  },
  {
   "claim": "Measured facts 5-8 / P0 row 4: the 26 OCP classes are bound, `RWObj`/`RWPly` are not, STEP schema reads '' until `Init_s()` then AP214IS then AP242DIS, `Model(True)` exists, glTF `SetLengthUnit_s` + `SetMergeFaces` exist, `BRepTools.Write_s` takes a path + VERSION_3, `BRepFeat_MakeCylindricalHole` has no counterbore, `Message_ProgressRange` is the boolean cancellation hook.",
   "refuted": false,
   "evidence": "Printed from server/.venv (vtk wheel, `vtkmodules` NOT in sys.modules after `import OCP`): all 26 named classes import (`bound 26 missing []`); `OCP.RWObj`/`OCP.RWPly` raise ImportError, `RWStl`/`RWMesh` import; `Interface_Static.CVal_s('write.step.schema')` = '' -> 'AP214IS' after `STEPControl_Controller.Init_s()` -> `SetCVal_s(...,'AP242DIS')` True; `STEPControl_Writer.Model` present; `STEPCAFControl_Writer.SetNameMode/SetColorMode/SetLayerMode`; `XCAFDoc_DocumentTool.SetLengthUnit_s(theDoc, theUnitValue: float)`; `RWGltf_CafWriter.SetMergeFaces`; `BRepTools.Write_s` overload 4 `(shape, theFile: str, withTriangles, withNormals, TopTools_FormatVersion, progress) -> bool` and `TopTools_FormatVersion_VERSION_3` exists; `BRepAlgoAPI_Cut` has `SetGlue/SimplifyResult/SetFuzzyValue/SetRunParallel` and `Build(theRange: Message_ProgressRange)`; `HLRBRep_HLRToShape` exposes `VCompound/Rg1LineVCompound/OutLineVCompound/HCompound/OutLineHCompound`; `BRepFeat_MakeCylindricalHole` methods are only `Perform/PerformBlind/PerformThruNext/PerformUntilEnd/PerformWithFiller`; `BRepMesh_IncrementalMesh(shape, linDefl, isRelative=False, angDefl=0.5, isInParallel=False)` matches the plan's positional call; `cadquery-ocp-novtk`, `build123d`, `lib3mf` ABSENT in server/.venv and the sidecar.",
   "fix": "None on the vtk wheel; P0 row 4 must still re-run this exact one-liner on the novtk venv before any of it is asserted for `[brep]`."
  },
  {
   "claim": "Where OCCT lives: the Claude Desktop extension venv has NO `OCP`; interpreters are server/.venv 3.11.15, sidecar `cad` 3.11.15, default python3 3.14.7.",
   "refuted": false,
   "evidence": "`~/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/python` is a symlink to uv's cpython-3.13.9; `find_spec('OCP')` False, `cadquery` False, `seamkiln` True there. `~/TEE/.tee/sidecars/cad/bin/python` 3.11.15 with cadquery-ocp 7.9.3.1.1; `python3 --version` 3.14.7; server/.venv 3.11.15.",
   "fix": "Add the fourth interpreter to the roster: the production `.mcpb` runtime is Python 3.13.9, so `SidecarKernel` is spawned FROM a 3.13 process into a 3.11 sidecar; make `check_<kiln>` print both `sys.version` and the sidecar's version, and do not let `LocalKernel` be chosen by `find_spec` on 3.13 if a future novtk wheel appears there."
  },
  {
   "claim": "P4: `Test<Kiln>AdapterContract(AdapterContract)` over a `FakeKernel` with no OCCT is green, `capture()` refusing honestly is contract-compatible, and `create object` lands as a BOM virtual component so the packaged suite runs on the fake.",
   "refuted": false,
   "evidence": "`from tee.kernel.contract import AdapterContract` (server/src/tee/kernel/contract.py:1-40, used by test_freecad_adapter.py:11-22 with `FakeFcWire` from fixtures_freecad.py). `test_capture_respects_the_byte_budget_or_refuses_loud` :148-159 accepts `TeeError` provided `exc.code and exc.fix` are set. `test_snapshot_restore_roundtrip` :134-144 issues `{\"op\":\"create\",\"kind\":\"object\",\"name\":\"kit_keep\"}` and expects names to round-trip through `snapshot()/restore()`. E1 notes SeamkilnAdapter never subclassed the contract; FreeCAD does.",
   "fix": "None; keep `<px>_capture_text_first` with a non-empty `fix`, and let `create object` produce an entity whose `name` survives `restore()` on the fake (the contract checks `e.name`, not id)."
  },
  {
   "claim": "D9: 14 `<px>_*` tools tabled explicitly with capabilities `read-compute/read-scene/write-artifacts/write-scene`, an untabled name is a STARTUP error, no `_FAMILY` row (the cad_/trade_ rule), and search ranking drops words <= 2 chars so `M6` never scores.",
   "refuted": false,
   "evidence": "registry.py:86-91 `register()` resolves `trust.capability_for(tool.name)` when `capability is None` (raises `trust_untabled_tool`, trust.py:365-382) and rejects unknown capability strings against `trust.CAPABILITIES` (trust.py:99 = READ_TIER | SIDE_EFFECTING; `read-scene` :48, `read-compute` :59, `write-scene` :75, `write-artifacts` :77). `_FAMILY` has `sk_` :169 but no `cad_`/`trade_` (:179-188 comment); `fc_drawing`/`fc_export` are explicit rows :311-312; `tee_purge` is the real tool name :202. registry.py:151 `words = [... if len(w) > 2]`, scoring name 3.0 / tags 2.0 / description 1.0 :155-165. `VirtualTool` fields name/description/schema/handler/tags/examples/capability registry.py:30-42; seamkiln's tools.py imports only `typing.Any`, `TeeError`, `VirtualTool` and registers 14 tools.",
   "fix": "None; note that tags are joined with spaces and matched by SUBSTRING (:157), so a tag like `flat` also matches `flatten` - pick pins accordingly."
  },
  {
   "claim": "Packaging/CI/doc conventions: `uv sync --all-extras --no-extra cad` is valid on uv 0.12.5 and a `cad` extra exists; CI is one `server` job; `packaging/mcpb_manifest.json tools[]`, `server/Makefile mcpb:`, `server/src/tee/pdf.py` exist; CHANGELOG lacks 0.19.0; next research doc is 68; DECISIONS heading form; trimesh `export_3MF`; `jobs.submit(..., qos=\"interactive\")`.",
   "refuted": false,
   "evidence": "`uv --version` 0.12.5; `uv sync --help` lists `--no-extra <NO_EXTRA>  Exclude the specified optional dependencies, if --all-extras is supplied`; `cad = [\"cadquery>=2.8.0\", ...]` server/pyproject.toml:102-103 (extras.py:41,46 marks it NOT_IN_TEE_VENV). `.github/workflows/ci.yml` = single `server` job, `uv sync --all-extras`, no cache. `\"tools\": [` manifest:34; `mcpb:` Makefile:22; pdf.py present. CHANGELOG.md:6 top entry `## 0.18.0 - 2026-08-31`. `ls docs/research | grep ^6` ends at `67-garment-cad-lane.md`. DECISIONS.md:1058 `## A53 - the garment lane (2026-09-01)`. trimesh 5.0.0 `exchange.threemf.export_3MF` True. jobs.py:26 `QOS_RANK = {\"interactive\": 0, ...}`, `submit(label, fn: Callable[[], dict], *, qos=\"standard\", engine=None)` :107-114; `app.jobs` app.py:119. `knowledge-base/15_software_autodesk_fusion` exists.",
   "fix": "Two small conformances: date the DECISIONS heading `## A66 - the mechanical CAD lane (2026-09-02)`, and make `kernel.warm()` return a dict (the `submit` contract), e.g. `{\"import_s\": ..., \"rss_mb\": ...}` which doubles as the `warm.json` the doctor reads."
  },
  {
   "claim": "`server/tests/test_<kiln>_live.py` spawns a real `SidecarKernel`, measures `<px>_warming` on a COLD sidecar and the P0 'cold <= 30 s or re-justify' import, inside the server suite.",
   "refuted": true,
   "evidence": "server/pyproject.toml:149-158 `[tool.pytest.ini_options]` sets `timeout = 60` and pytest-timeout 2.4.0 is installed in server/.venv, so every server test is killed at 60 s. The plan's own facts admit cold `import OCP` is unmeasured (fact 9: '140 s first import ... unmeasured cold native page-in', row 1 expects <= 10 s but the gate tolerates up to 30 s 'or the sidecar design re-justified'). A cold spawn + F5 replay + HLR in one test can therefore fail as a timeout rather than yield a number, and the plan never mentions the per-test limit. The warm path is safe: `sys.executable` in the suite is server/.venv (OCP importable, warm import ~0.3 s).",
   "fix": "Mark the cold-spawn and replay tests `@pytest.mark.timeout(300)` (or `-o timeout=0` in the `-m dcc` invocation), gate the truly cold measurement behind `-m dcc`/`TEE_KILN_COLD=1` and record it in P0a's table instead, and keep only the warm `SidecarKernel` spawned from `sys.executable` in the default suite."
  }
 ]
}