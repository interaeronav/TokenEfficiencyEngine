# Epic's Official Unreal MCP Plugin (UE 5.8)

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Research question

What exactly does Epic's official UE 5.8 Experimental "Unreal MCP" plugin expose and how is it extended: the concrete tool inventory (per dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor), its transport/auth details (local HTTP MCP server embedded in the editor, auto-start, generated client configs for Claude Code/Cursor/etc.), whether it can author/introspect Blueprint K2Node graphs, its per-tool schema and response verbosity (token cost), and the documented C++/Python API for registering custom tools into it?

This decides the entire UE adapter architecture and phasing: whether TEE builds its own bindings on Remote Control (`30010`/`30020`) + Python remote execution, proxies/wraps Epic's in-editor MCP server, or registers TEE tools inside it via its extension API. If Epic's plugin already covers Blueprint graph authoring, the planned optional Tier-2 custom C++ plugin phase is redundant; if its tool responses are verbose, TEE's value proposition shifts to a caching/summarizing proxy in front of it — a fundamentally different component than a from-scratch bridge.

## Summary

Epic's UE 5.8 Experimental "Unreal MCP" plugin (engine identifier: `ModelContextProtocol`) embeds a Streamable-HTTP MCP server at `http://127.0.0.1:8000/mcp` inside the editor process, loopback-only with no auth, and by default advertises only 3 meta-tools (`list_toolsets` / `describe_toolset` / `call_tool`) while dispatching a live-probed catalog of 830 tools across 52 toolsets server-side — an explicit token-efficiency design ("keeps your context window small and the prompt cache warm").

It fully covers Blueprint K2 graph authoring and introspection: `BlueprintTools` ships 53 tools including node/pin-level editing (`create_node`, `connect_pins`, `get_pin_value`), whole-graph S-expression DSL read/write (`read_graph_dsl` / `write_graph_dsl` / `get_graph_dsl_docs`), subgraph-scoped reading (`get_connected_subgraph`), and compile with diagnostics — plus UMG widget-tree authoring (`UMGToolSet`, 23 tools), 319 Sequencer/ControlRig tools, Niagara (56), PCG (31), and Materials (37).

Extension is first-class and documented: Python classes deriving `unreal.ToolsetDefinition` with `@toolset_registry.tool_call` decorators (auto-discovered from any plugin's `Content/Python/`), C++ `UToolsetDefinition` subclasses with `UFUNCTION(meta=(AICallable))` (which require explicit `UToolsetRegistry::RegisterToolsetClass` in module startup), or dynamic `IModelContextProtocolModule::AddTool()`; type hints/reflected `UPROPERTY`s generate the JSON Schemas automatically. Epic also ships its own round-trip mitigation (`ProgrammaticToolset.execute_tool_script` batches tool calls in sandboxed Python, "reducing round-trips and context usage") and an official Claude Code plugin in the `claude-plugins-official` marketplace with `create-toolset` scaffolding skill.

Token costs concentrate in `describe_toolset` responses (measured ~74K chars for `BlueprintTools`, ~127K chars for `SequencerTools` per call) and in unpaginated list results (pagination off by default). Consequence for TEE: a from-scratch Remote-Control-based bridge would duplicate an 830-tool official surface; the highest-leverage architecture is registering TEE workflow-shaped tools via the documented toolset extension API and/or a summarizing/caching front for `describe_toolset` payloads, and the Tier-2 custom C++ Blueprint-authoring plugin is largely redundant.

## Findings

### Plugin identity, status, version

Official Epic feature in UE 5.8, Experimental status ("many features are incomplete or missing. APIs and data formats are subject to change"). Engine identifier `ModelContextProtocol` (friendly name "Unreal MCP"), path `Engine/Plugins/Experimental/ModelContextProtocol`, `.uplugin` description "Anthropic MCP (Model Context Protocol) server implementation for Unreal Engine." Three modules: `ModelContextProtocol` + `ModelContextProtocolEngine` (runtime: server, protocol, settings, console commands) and `ModelContextProtocolEditor` (editor-only: auto-start hook + adapting `ToolsetRegistry` toolsets into MCP Tools). Toolsets are NOT implemented by the MCP plugin itself — the separate `AllToolsets` aggregator plugin (`EnabledByDefault` off, editor-only) must be enabled, which pulls in the `ToolsetRegistry` plugin.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/ModelContextProtocol](https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/ModelContextProtocol)

### Transport and auth

HTTP + Server-Sent Events (Streamable HTTP) only; stdio and WebSocket NOT supported. Default binding `http://127.0.0.1:8000/mcp` (port and URL path configurable in Editor Preferences > Model Context Protocol; `serverInfo.name` always `unreal-mcp`). Loopback-only per `[HTTPServer.Listeners] DefaultBindAddress`; server rejects non-loopback `Origin` headers; "no authentication layer... not safe to expose beyond the local machine." Third-party live verification: MCP protocol version `2025-06-18`, `Mcp-Session-Id` header; quirk — `initialize`/`tools/list` answer plain JSON but `tools/call` answers SSE frames on the same POST, so clients must send `Accept: application/json, text/event-stream`. Epic security note: "Localhost is not a trust boundary... any process running as the same user on the same machine can connect."

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [github.com/NAJEMWEHBE/unreal-ai-connection](https://github.com/NAJEMWEHBE/unreal-ai-connection) `docs/PORT-SPEC/00-overview.md` + [github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin) README

### Auto-start and startup controls

Auto Start Server defaults to false; toggled in Edit > Editor Preferences > General > Model Context Protocol, persisted per-user in `Saved/Config/<Platform>Editor/EditorPerProjectUserSettings.ini` under `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings] bAutoStartServer=True` (NOT `DefaultEngine.ini`). Console commands: `ModelContextProtocol.StartServer [port]`, `StopServer`, `RefreshTools` (re-poll registry after authoring/hot-reload/Game Feature activation), `GenerateClientConfig <Client|All>`. Command-line flags: `-ModelContextProtocolStartServer` (works in editor or commandlet startup) and `-ModelContextProtocolPort=N`. Cooked/shipping builds can host the server via `IModelContextProtocolModule::StartServer()` but registry toolsets are NOT auto-discovered there (must use `AddTool()`); tool-search meta-tools are editor-only.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [unreal-engine-skills-for-claude-code-plugin skills/unreal-mcp/references/setup.md](https://raw.githubusercontent.com/EpicGames/unreal-engine-skills-for-claude-code-plugin/main/skills/unreal-mcp/references/setup.md)

### Generated client configs

`ModelContextProtocol.GenerateClientConfig` writes `.mcp.json` to the project root (source builds: workspace root alongside `Engine/`, not next to the `.uproject`) for clients `ClaudeCode`, `Cursor`, `VSCode`, `Gemini`, `Codex`, `All`. Generated content: `{"mcpServers":{"unreal-mcp":{"type":"http","url":"http://127.0.0.1:8000/mcp"}}}`. JSON configs merge with existing entries (safe to re-run); Codex TOML (`.codex/config.toml`) is write-once and refuses to overwrite. Optional Terminal plugin embeds a terminal panel in the editor to run the agent CLI in-editor (needs `TERM=xterm-256color` or `claude` falls back to degraded escape-sequence output).

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)

### Tool Search mode — Epic's core token-efficiency mechanism

`bEnableToolSearch` defaults to true: `tools/list` returns ONLY `list_toolsets` ("Returns the available toolset names and descriptions"), `describe_toolset` ("Returns the schemas for a named toolset"), and `call_tool` ("Dispatches a named toolset's Tool with the supplied arguments and returns the result on the same turn"). Doc: "keeps tools/list responses small even when the registry exposes hundreds of Tools." Epic skill: tool names "are not in tools/list... dispatched server-side through call_tool and never registered as native MCP tools. This is deliberate. It keeps your context window small and the prompt cache warm." `call_tool` shape: `{toolset_name, tool_name (unprefixed), arguments}`; wrong/missing args return the full schema in the error text (verified live). Setting it to false eagerly registers all tools "at the cost of a much larger initial schema payload" (used by Epic's hash-mapping commandlet). Note: a UE 5.8 Preview build had a `load_toolset` meta-tool requiring next-turn availability; final 5.8 replaced it with same-turn `call_tool`.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [unreal-engine-skills-for-claude-code-plugin skills/unreal-mcp/SKILL.md](https://raw.githubusercontent.com/EpicGames/unreal-engine-skills-for-claude-code-plugin/main/skills/unreal-mcp/SKILL.md) + `references/operations.md` + [github.com/imgamer/AILearn](https://github.com/imgamer/AILearn) `Tools/UE5.8.0-Preview-MCP-Study/MCP_Toolsets.md` + [github.com/OrionUE/Orion_FreeEdition](https://github.com/OrionUE/Orion_FreeEdition) `orion-mcp-project-toolsets/SKILL.md`

### Concrete tool inventory (final UE 5.8.0, live-probed)

52 toolsets / 830 tools total (live probe of official 5.8.0 server, schemas verbatim from `describe_toolset`). By domain:

- Blueprint graphs & logic: 1 toolset / 53 tools
- Materials & textures: 3 / 37
- Niagara FX: 5 / 56 (`NiagaraToolset_System` alone 46)
- Animation + ControlRig + Sequencer: 8 / 319 (`SequencerTools` 140, `SequencerControlRigTools` 72, `ControlRigTools` 44, `SequencerKeyframingTools` 22, `SequencerOutlinerTools` 18, `SequencerConditionTools` 9, `SequencerCustomBindingTools` 8, `SequencerImportExportTools` 6 incl. FBX)
- Mesh/primitives/PCG: 5 / 73 (`SkeletalMeshTools` 22, `StaticMeshTools` 16, `PCGToolset` 30, `PCGSpatialToolset` 1, `PrimitiveTools` 4)
- Scene/actors/assets/objects: 4 / 64 (`AssetTools` 21, `SceneTools` 20, `ActorTools` 17, `ObjectTools` 6)
- GAS & tags: 4 / 20 (`AbilitySystemInspectorToolset` 4, `AttributeSetToolset` 2, `GameplayCueToolset` 8, `GameplayTagsToolset` 6)
- UMG/StateTree/BehaviorTree: 5 / 48 (`UMGToolSet` 23, `SlateInspectorToolset` 14 "Playwright-style Slate UI automation", `BehaviorTreeTools` 7 read-only, `StateTreeTools` 9, `WorldConditionTools` 2)
- Data tables: 5 / 35 (`DataTableTools` 10, `CurveTableTools` 9, `StringTableTools` 8, `DataAssetTools` 1, `DataRegistryTools` 7)
- Editor control: 6 / 56 (`EditorAppToolset` 21 — screenshots, camera, content browser, selection, CVars; `LogsToolset` 4; `AutomationTestToolset` 7; `ConfigSettingsToolset` 8; `AgentSkillToolset` 4; `ProgrammaticToolset` 2)
- Project: 6 / 69 (`GameFeaturesToolset` 7, `PluginToolset` 17, `DataflowAgentToolset` 22, `PhysicsAssetToolset` 17, `SemanticSearchToolset` 2 "hybrid vector + BM25 asset search", `ConversationTools` 7)

ue-mcp.com independently corroborates "830 official tools across 52 toolsets."

Source: [tc-imba.github.io/ue-official-mcp/references/](https://tc-imba.github.io/ue-official-mcp/references/) and [/references/toolsets/](https://tc-imba.github.io/ue-official-mcp/references/toolsets/) + [ue-mcp.com/docs/native-tools](https://ue-mcp.com/docs/native-tools)

### Blueprint K2 graph authoring — YES, fully covered including a whole-graph DSL

`editor_toolset.toolsets.blueprint.BlueprintTools` (53 tools, Python-authored, shipped) covers:

- Asset ops: `create`, `get_parent`/`set_parent`, `compile_blueprint`, `get_default_object`
- Graphs: `list_graphs`, `get_graph`, `add_function_graph`/`remove_function_graph`
- Variables: `add_variable`, `add_object_variable`, `add_struct_variable`, `remove_variable`, `set_variable_instance_editable`, `get`/`set_variable_replication` (`None`/`Replicated`/`RepNotify` with auto `OnRep_`), `get`/`set_variable_category`
- Function params: `add_function_param`, `add_object_function_param`, `add_struct_function_param`, `remove_function_param`
- Event dispatchers: `add_event_dispatcher`, `list_event_dispatchers`
- Events: `add_event` (overrides inherited events, e.g. `ReceiveAnyDamage`, or creates custom events; idempotent), `add_component_bound_event`, `list_component_events`, `list_compatible_event_functions`, `get`/`set_create_event_function`
- Node-level editing: `find_node_types`, `find_node_categories`, `create_node` with `type_id` strings like `Development|PrintString`, `Utilities|Operators|Add`, `Utilities|FlowControl|ForLoop`, `AddEvent|EventBeginPlay`, `AddEvent|Custom|MyEventName`; `delete_node`, `set_node_position`, `arrange_nodes`, `add_node_pin`/`remove_node_pin`, `get_node_type_pins`, `retarget_node_class`
- Pin wiring: `connect_pins`, `break_pins`, `get_pin_value`, `set_pin_value`; PinID = `{node refPath, direction EGPD_Output/EGPD_Input, index_id}`
- Introspection: `find_nodes`, `get_node_infos` (batch), `get_connected_subgraph` ("read a single event chain from a large graph... without reading the entire graph")
- Whole-graph S-expression DSL: `get_graph_dsl_docs` ("full syntax reference"), `read_graph_dsl` ("returns a DSL script... can be edited and passed back to write_graph_dsl"), `write_graph_dsl` ("Populates a Blueprint graph with nodes from a DSL script and compiles the Blueprint")

Round-trip graph-as-text authoring is therefore native in 5.8.0 final.

Source: [tc-imba.github.io/ue-official-mcp/references/toolsets/editor_toolset.toolsets.blueprint.BlueprintTools/](https://tc-imba.github.io/ue-official-mcp/references/toolsets/editor_toolset.toolsets.blueprint.BlueprintTools/) (schemas verbatim from `describe_toolset` of official 5.8.0 server)

### UMG widget authoring — covered in final 5.8 (was missing in Preview)

`UMGToolSet.UMGToolSet`: "UMG widget toolset for AI-driven widget creation and tree manipulation", 23 tools: `CreateWidgetBlueprint`, `CompileWidgetBlueprint`, `ListWidgetBlueprints`, `ListWidgetClasses`, `GetWidgetClassInfo`, `GetWidgets`, `GetWidgetDescription`, `GetWidgetTreeDepth`, `GetNamedSlots`, `AddWidget`, `RemoveWidget`, `RenameWidget`, `MoveWidget`, `WrapWidgets`, `ReplaceWidgetWithChild`, `ReplaceWidgetWithNamedSlot`, `ReplaceWidgetWithTemplate`, `SetNamedSlotContent`, `ToggleWidgetAsVariable`, `BindToEventProperty`, `AddUIComponent`, `MoveUIComponent`, `RemoveUIComponent`. A UE 5.8.0-Preview community audit had found zero Widget-tree tools — this gap closed by release. `BehaviorTreeTools` remains read-only (`get_*`/`list_*` only, no mutation).

Source: [tc-imba.github.io/ue-official-mcp/references/toolsets/UMGToolSet.UMGToolSet/](https://tc-imba.github.io/ue-official-mcp/references/toolsets/UMGToolSet.UMGToolSet/) + [github.com/imgamer/AILearn](https://github.com/imgamer/AILearn) `Tools/UE5.8.0-Preview-MCP-Study/MCP_Toolsets.md`

### Per-tool schema shape and response conventions

Schemas are reflection-generated: Python type hints (`unreal.Actor`, `str`, `bool`, `list[str]`, dataclasses) and Google-style docstrings (`Args:`/`Returns:` blocks) drive the JSON Schema; C++ doc comments and `UPROPERTY` metadata (`ClampMin`/`ClampMax`) flow in automatically. `UObject*`/`UClass*` parameters/returns serialize as `{"refPath": "/Game/Path.Asset"}` soft-path objects via `FToolsetReferenceConverter` with title e.g. `/Script/Engine.Blueprint` (confirmed live). `FToolsetTransformConverter` makes location/rotation/scale optional fields (`{"location":{x,y,z},"rotation":{pitch,yaw,roll},"scale":{x,y,z}}`, degrees not radians, omitted = identity/unchanged). `FToolsetColorConverter` unifies `FColor`/`FLinearColor` (`r,g,b,a` floats 0–1, >1 = HDR). Outputs are wrapped: `{"returnValue": ...}`; primitives additionally wrapped `{"result": ...}` per CVar `ModelContextProtocol.WrapPODToolResultsInObject` (bool, default true). Wire format is standard MCP content blocks (`{"content":[{"type":"text","text":...}]}`). Actor instance refs look like `/Game/Maps/MyMap.MyMap:PersistentLevel.PointLight_0` and component refs append `.PointLightComponent0`.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [unreal-engine-skills-for-claude-code-plugin skills/create-toolset/SKILL.md](https://raw.githubusercontent.com/EpicGames/unreal-engine-skills-for-claude-code-plugin/main/skills/create-toolset/SKILL.md) + [github.com/NAJEMWEHBE/unreal-ai-connection](https://github.com/NAJEMWEHBE/unreal-ai-connection) `docs/PORT-SPEC/00-overview.md` + tc-imba raw schemas

### Token cost measurements (verbatim describe_toolset payloads, whitespace-normalized chars)

`describe_toolset` returns docstrings + full input/output JSON Schemas for every tool in the toolset in one response. Measured from the live-probed 5.8.0 catalog:

- `BlueprintTools` (53 tools): ~74,300 chars (~18–19K tokens at 4 chars/token)
- `SequencerTools` (140 tools): ~126,900 chars (~32K tokens)
- `UMGToolSet` (23 tools): ~63,400 chars
- `SceneTools` (20 tools): ~24,600 chars
- `ObjectTools` (6 tools): ~5,700 chars
- `ProgrammaticToolset` (2 tools): ~2,800 chars

Reference-heavy schemas are verbose: every `refPath` parameter repeats the boilerplate `{'description':'Represents a reference to a UObject or UClass.','properties':{'refPath':{...}},'required':['refPath'],'title':'/Script/...','type':'object'}`. Eager mode (`bEnableToolSearch=false`) would front-load all 830 schemas (order ~1MB / low hundreds of thousands of tokens). Other verbosity facts: `ModelContextProtocol.PaginationPageSize` defaults to 0 = pagination DISABLED, all items returned; no documented hard byte cap on responses; failed `call_tool` with wrong args returns the full tool schema in the error text; `LogsToolset.GetLogEntries` default cap 1000 entries; `ModelContextProtocol.ProgressIntervalSeconds` (float, default 1.0) throttles progress notifications; `ModelContextProtocol.AudioResultOggFormat` (default false = WAV); `ModelContextProtocol.EnableAnalytics` default true.

Source: [tc-imba.github.io/ue-official-mcp/references/toolsets/](https://tc-imba.github.io/ue-official-mcp/references/toolsets/) (per-toolset pages, measured) + [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [github.com/NAJEMWEHBE/unreal-ai-connection](https://github.com/NAJEMWEHBE/unreal-ai-connection) `docs/PORT-SPEC/00-overview.md`

### Epic's own round-trip/token mitigations already shipped

1. Tool-search meta-tools (3-tool `tools/list`, stable catalog = warm prompt cache).
2. `ProgrammaticToolset.execute_tool_script`: "batch multiple tool calls into a single script execution, reducing round-trips and context usage" — sandboxed Python (must define `run() -> Dict[str,Any]`; `get_execution_environment` must be called first; only whitelisted stdlib modules — `json`/`math`/`datetime`/`copy`/`re`; `import unreal` is BLOCKED; purpose is "tool orchestration, not general Python execution"; has full access to every toolset API).
3. Blueprint whole-graph DSL (`read_graph_dsl`/`write_graph_dsl`) replaces N node/pin calls with one text payload.
4. `get_connected_subgraph` + `find_nodes` for partial graph reads.
5. `AgentSkillToolset` (`ListSkills`/`GetSkills`/`CreateSkill`/`UpdateSkill`): project-registered Agent Skill assets loaded on demand instead of stuffed in system prompt.
6. Toolset descriptions designed to stand alone: "An LLM will often see only the toolset name and this description without ever loading its tools."

Source: [tc-imba.github.io/ue-official-mcp/references/toolsets/editor_toolset.toolsets.programmatic.ProgrammaticToolset/](https://tc-imba.github.io/ue-official-mcp/references/toolsets/editor_toolset.toolsets.programmatic.ProgrammaticToolset/) + [unreal-engine-skills-for-claude-code-plugin skills/create-toolset/SKILL.md](https://raw.githubusercontent.com/EpicGames/unreal-engine-skills-for-claude-code-plugin/main/skills/create-toolset/SKILL.md) + `unreal-mcp` SKILL.md

### Extension API — Python (recommended path)

`.py` modules under any plugin's `Content/Python/`; class decorated `@unreal.uclass()` deriving `unreal.ToolsetDefinition`; class docstring = toolset description; each tool is `@toolset_registry.tool_call` + `@staticmethod` (generates `unreal.ufunction(static=True, meta={'AICallable': ''})`); functions without the decorator are not advertised; mandatory type annotations on every param/return using standard Python types (`list[str]`, `dict[str,str]` — not `unreal.Array`); Google-style docstrings become schema descriptions. Epic's official skill says registration "is never automatic" — call `unreal.ToolsetRegistry.register_toolset_class(MyToolset)` in `init_unreal.py`/`__init__.py` (though the docs page says the registry "discovers them at startup" for `Content/Python` modules). Errors: raise exceptions directly (`ValueError` etc.); "Return values carry data, not status." Tests: extend `ToolCallTestCase`, `assertToolRaisesRuntimeError`; reload via `Engine/Plugins/Experimental/ToolsetRegistry/Content/Python/toolset_registry/tests/reload_remote.py` (requires Python Remote Execution enabled). Shipped reference: `Engine/Plugins/Experimental/ToolsetRegistry/Content/Python/toolset_registry/toolsets/core/actor.py` (38 lines). After authoring, run `ModelContextProtocol.RefreshTools`.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [unreal-engine-skills-for-claude-code-plugin skills/create-toolset/SKILL.md](https://raw.githubusercontent.com/EpicGames/unreal-engine-skills-for-claude-code-plugin/main/skills/create-toolset/SKILL.md)

### Extension API — C++

Derive `UToolsetDefinition` (`ToolsetRegistry/ToolsetDefinition.h`), `UCLASS(BlueprintType, Hidden)` (skill shows `MinimalAPI` variant), static `UFUNCTION(meta=(AICallable))` methods; doc comments become tool descriptions; `meta=(AIIgnore)` or omitting `AICallable` excludes a function. C++ toolsets do NOT auto-register (proven live 2026-07: DLL loads clean, zero log lines, absent from `list_toolsets`): call `UToolsetRegistry::RegisterToolsetClass(UMyToolset::StaticClass())` in `StartupModule()` and `UnregisterToolsetClass` in `ShutdownModule()` — the pattern used by every Epic C++ toolset module (e.g. `ConfigSettingsToolsetModule.cpp`). Live Coding picks up body edits; NEW `UFUNCTION`s require full editor restart. Async: return `UToolCallAsyncResult` subclass (e.g. `UToolCallAsyncResultImage`), call `SetValue()`/`SetError()`. Errors: `UKismetSystemLibrary::RaiseScriptError` then return default (5.8 source has single-`FString` signature at `KismetSystemLibrary.h:124`; Epic's skill shows a newer `EScriptExceptionType` overload — main-branch vs 5.8 divergence). Custom serialization: subclass `FToolsetJsonConverter` (`ToolsetRegistry/ToolsetJsonConverter.h`). Shipped C++ reference: `UAttributeSetToolset` in `Engine/Plugins/Experimental/Toolsets/GASToolsets/`. When to use C++: engine functionality not exposed to Python, `USTRUCT` signatures, hot paths. Gotcha (proven live): tool calls run serially on the game thread, so any editor API reaching `ShowModal()` (e.g. `FBlueprintEditorUtils::ChangeMemberVariableType` popping `FSuppressableWarningDialog`) deadlocks the MCP server until a human clicks.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + [unreal-engine-skills-for-claude-code-plugin skills/create-toolset/SKILL.md](https://raw.githubusercontent.com/EpicGames/unreal-engine-skills-for-claude-code-plugin/main/skills/create-toolset/SKILL.md) + [github.com/NAJEMWEHBE/unreal-ai-connection](https://github.com/NAJEMWEHBE/unreal-ai-connection) `docs/PORT-SPEC/00-overview.md` (live-verified)

### Extension API — dynamic direct registration

For runtime-determined schemas / dynamic tools / data outside the type system: implement `IModelContextProtocolTool` and register via `IModelContextProtocolModule::GetChecked().AddTool(MakeShared<FMyDynamicTool>())`; caller owns deregistration; interface methods invoked on the game thread (HTTP server ticked from core ticker). `AddTool`-registered tools advertise EAGERLY regardless of `bEnableToolSearch` (the tool-search meta-tools are part of the editor-only adapter). This is the hook a TEE facade tool would use to appear in `tools/list` directly.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)

### Concurrency and threading model

"A key function of the MCP server is to synchronize external requests with the Unreal Engine game thread by executing Tool invocations on the game thread serially, meaning clients should not issue overlapping Tool calls." Epic skill hard rule: "Sequential, never parallel. Tool calls execute on the game thread, so issuing them in parallel deadlocks or fails." Also: editor busy compiling/loading/PIE causes hangs; `LiveCodingToolset.CompileLiveCoding` blocks until compile finishes and surfaces MSVC diagnostics; editor-only tools behave differently during PIE; MCP edits "are not always undoable, especially across compilation boundaries."

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) + `unreal-mcp` SKILL.md

### MCP Resources/Prompts and pagination

"MCP Resources and Prompts are not advertised by any shipping toolset" (Tools only). Pagination exists but is off by default (`ModelContextProtocol.PaginationPageSize` int32, default 0 = return all items). Progress notifications supported (min interval CVar). Debugging: `LogModelContextProtocol` category; MCP Inspector (`npx @modelcontextprotocol/inspector`) over Streamable HTTP is the recommended debug client.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor)

### Official Claude Code plugin + skills

Epic publishes `unreal-engine-skills-for-claude-code` in Anthropic's official marketplace (`claude-plugins-official`): the `unreal-mcp` skill (usage contract: discover via `list_toolsets`/`describe_toolset`, dispatch via `call_tool`; check `AgentSkillToolset.ListSkills` for project skills; safety rules) and the `create-toolset` skill (scaffolds new toolsets in either language; design principles: "Don't mirror Unreal's existing APIs directly"; "Use real types... Converting to or from a JSON-formatted string inside a tool call is a code smell"; CRUD symmetry; `ObjectTools` already provides generic `UObject` property get/set — don't reimplement). Also `unreal-skill` (author Agent Skills) and a SessionStart hook. README headline: "Hundreds of tools exposed via Unreal's ToolsetRegistry across 30+ toolsets." Security: `ProgrammaticToolset.execute_tool_script` "executes arbitrary Python inside the editor process" with full toolset API access.

Source: [github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin) (`README.md`, `skills/unreal-mcp/SKILL.md`, `skills/create-toolset/SKILL.md`)

### Toolset plugin packaging & module naming drift

Domain toolsets are separate Experimental plugins under `Engine/Plugins/Experimental/Toolsets/<Name>/`: `GASToolsets` ("ships disabled by default; enabling surfaces an experimental-feature warning"), `NiagaraToolsets`, `PCGToolset`, `StateTreeToolset`, `WorldConditionsToolset`, `ConversationToolset`, `DataRegistryToolset`, `AIModuleToolset`, `AnimationAssistantToolset` (deps: Control Rig, Level Sequence Editor, Sequencer Scripting), `SequencerAnimMixerToolset` ("EDA toolset"), `MCPClientToolset` (Beta: "An adapter that allows toolset registry customers (like the EDA) to connect to local/private MCP servers" — i.e., external MCP servers can be bridged INTO the registry). `MetaHumanGenerator` Toolset exists for MetaHuman creation (eye color, skin tone, body shape). `AllToolsets` aggregates; individual toolset plugins can be enabled selectively instead. Core Python toolsets were at `toolset_registry.toolsets.core.*` (docs, Preview, and Orion live logs use e.g. `toolset_registry.toolsets.core.blueprint.BlueprintTools`) but the 5.8.0 release probe reports `editor_toolset.toolsets.*` module paths and an `EditorToolset` plugin (zuqqhi2 setup enabled "Unreal MCP" + "EditorToolset") — naming churned within the 5.8 cycle; treat `toolset_name` strings as unstable, discover at runtime.

Source: [dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/*](https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/) (per-plugin pages) + [tc-imba.github.io/ue-official-mcp/references/toolsets/](https://tc-imba.github.io/ue-official-mcp/references/toolsets/) + [zuqqhi2.com/en/https-zuqqhi2-com-unreal-engine-mcp-codex-blueprint-en](https://zuqqhi2.com/en/https-zuqqhi2-com-unreal-engine-mcp-codex-blueprint-en) + Orion_FreeEdition skills

### PCG toolset official workflow doc

Official page "Working with PCG and LLMs Using Unreal MCP" documents the `PCGToolset` plugin (30 tools, "Toolset for building and modifying PCG graphs") plus shipped Agent Skills: `Skill_PCGGraphGeneration`, `Skill_PCGShapeGrammarDefinition`, `Skill_PCGMeshPartition`, `Skill_PCGInstancingOnMeshActor`, `Skill_PCGBiomeCore`. Epic's stated failure mode without skill context: the LLM will "Misunderstand PCG concepts, Overcomplicate solutions, Misuse nodes or parameters, Produce unreliable graph logic" — i.e., Epic pairs raw tools with domain skill-prompt packs.

Source: [dev.epicgames.com/documentation/en-us/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine)

### Real-world usage evidence

zuqqhi2 (July 2026): UE 5.8 + Unreal MCP + EditorToolset plugins, Codex CLI via `.codex/config.toml` (30s startup timeout, 60s tool timeout) built a simple 3D Blueprint tag game plus Functional Tests "in a single interaction", no editor crashes (vs earlier community VibeUE attempts). NAJEMWEHBE port-spec (live 5.8 sessions): abandoned their own 151-tool custom C++ MCP bridge to re-target Epic's registry, ruled out re-porting actors/scene/materials/objects/data-tables/Niagara/Level-Sequence families because Epic's coverage is a strict superset ("Epic's 8 sequencer toolsets ≈230 tools cover it"; "Epic's NiagaraToolsets... 34 tools" [5.8-preview count; final probe shows 56]); still ported gap families: Movie Render Queue, DMX/nDisplay/OCIO, and workflow-shaped ("fewer, fatter") Blueprint whole-function define tools — note their whole-graph-spec critique predates/parallels Epic's own `write_graph_dsl`. Ecosystem wrappers already exist: ue-mcp.com wraps all 830 tools in-process with seed strategies trading "token cost against discovery round-trips" (full/lean/micro gateway modes).

Source: [zuqqhi2.com/en/https-zuqqhi2-com-unreal-engine-mcp-codex-blueprint-en](https://zuqqhi2.com/en/https-zuqqhi2-com-unreal-engine-mcp-codex-blueprint-en) + [github.com/NAJEMWEHBE/unreal-ai-connection](https://github.com/NAJEMWEHBE/unreal-ai-connection) `docs/PORT-SPEC/00-overview.md`, `blueprint-k2.md` + [ue-mcp.com/docs/native-tools](https://ue-mcp.com/docs/native-tools)

### Known gaps in Epic's 5.8.0 tool surface (for TEE gap-fill scoping)

From live audits: BehaviorTree editing (read-only toolset); PIE start/stop control not exposed; C++ compile is only via `LiveCodingToolset` (new `UFUNCTION`s need editor restart); Landscape, Foliage, Audio/MetaSounds, Chaos, World Partition, Movie Render Queue, DMX/nDisplay/OCIO have no dedicated toolsets (generic `ObjectTools` property writes are the only lever); `ProgrammaticToolset` sandbox cannot `import unreal` so arbitrary editor scripting still requires Python Remote Execution (upyrc/remote exec on ports `6766`/`9998`) or Remote Control API (`30010`/`30020`) outside MCP; GAS is inspect-heavy (mutation limited); `TextureTools` minimal (2 tools). Community gap-filler toolsets already registering into the registry: Niagara spawn, ISM instance management, viewport frame capture, GAS mutation, Enhanced Input introspection (xkazm04/pof `PoFToolset`), KawaiiPhysics AnimGraph auditing (pafuhana1213/KawaiiPhysics ships its own `toolset.py` in the marketplace plugin).

Source: [github.com/imgamer/AILearn](https://github.com/imgamer/AILearn) `MCP_Toolsets.md` + [github.com/NAJEMWEHBE/unreal-ai-connection](https://github.com/NAJEMWEHBE/unreal-ai-connection) PORT-SPEC + GitHub code search results (xkazm04/pof, pafuhana1213/KawaiiPhysics toolset files)

### Related but distinct: UEFN MCP

Fortnite/UEFN has a separate "UEFN MCP" (dev.epicgames.com/documentation/fortnite/uefn-mcp, Fortnite ecosystem v42.00 era) — a different product from the UE 5.8 in-editor plugin; UEFN community toolbelts (e.g. UEFN-TOOLBELT, "361 level-design, asset and Verse tools") also build on `unreal.ToolsetDefinition`. Relevant only if TEE targets UEFN.

Source: [dev.epicgames.com/documentation/fortnite/uefn-mcp](https://dev.epicgames.com/documentation/fortnite/uefn-mcp) + [github.com/undergroundrap/UEFN-TOOLBELT](https://github.com/undergroundrap/UEFN-TOOLBELT)

## Recommendations for TEE

1. Do not build a from-scratch UE bridge on Remote Control (`30010`/`30020`) + Python remote execution as the primary path: Epic's in-editor MCP server already exposes 830 tools across 52 toolsets in UE 5.8.0 including full Blueprint K2 authoring; reserve Remote Control/remote-exec only as a fallback for pre-5.8 engines or for the gaps Epic's sandbox blocks (arbitrary `import unreal` scripting, PIE control).
2. Cancel or drastically descope the planned Tier-2 custom C++ Blueprint-authoring plugin: Epic's `BlueprintTools` (53 tools) already does node/pin editing, compile-with-diagnostics, AND whole-graph S-expression DSL round-tripping (`read_graph_dsl`/`write_graph_dsl`/`get_graph_dsl_docs`). Any remaining TEE Blueprint value is a thin workflow layer (e.g. atomic define-function-from-spec with node-id-keyed diagnostics), not graph plumbing.
3. Position TEE's UE adapter as (a) a token-optimizing proxy in front of Epic's server plus (b) a small set of custom toolsets registered INTO Epic's registry via the documented extension API — not as a parallel bridge. The Python path (`unreal.ToolsetDefinition` + `@toolset_registry.tool_call` in any plugin's `Content/Python/`) is the cheapest to ship and iterate; use C++ `UToolsetDefinition` only where Python bindings are missing.
4. The proxy's highest-leverage token wins, in order: (1) cache and summarize `describe_toolset` payloads — they are the dominant cost (~74K chars for `BlueprintTools`, ~127K for `SequencerTools` per call) and Epic's server re-serves them verbatim; serve compressed per-tool signatures and lazy-expand full schemas on demand; (2) deduplicate the repeated `refPath` boilerplate object in schemas; (3) paginate/truncate unpaginated list results client-side (Epic's `PaginationPageSize` defaults to 0 = everything); (4) strip the full-schema-in-error-text responses down to the offending field.
5. Exploit Epic's own batching primitive before inventing one: route multi-step TEE macros through `ProgrammaticToolset.execute_tool_script` (sandboxed Python orchestrating any registered tool in one round-trip, explicitly built for "reducing round-trips and context usage"), and cache the `get_execution_environment` instructions once per session.
6. Preserve Epic's tool-search contract in any TEE facade: keep `tools/list` tiny and stable (3 meta-tools) so the prompt cache stays warm; if TEE registers dynamic tools via `IModelContextProtocolModule::AddTool`, remember those advertise eagerly and will bloat `tools/list` — prefer registry toolsets that stay behind `call_tool`.
7. Treat `toolset_name` strings as unstable across 5.8 point builds (`toolset_registry.toolsets.core.*` vs `editor_toolset.toolsets.*` drift observed): TEE must discover names at runtime via `list_toolsets` and map by suffix (e.g. `*.BlueprintTools`), never hardcode full module paths.
8. Enforce strict call serialization in the TEE proxy: Epic's server executes tools serially on the game thread; parallel calls deadlock or fail, and any tool body that reaches a modal dialog hangs the server until a human clicks. Add per-call timeouts and a busy-state probe (compiling/PIE/level-load) before dispatch.
9. Scope TEE's custom-toolset phase to the verified 5.8 gaps only: PIE start/stop, BehaviorTree mutation, Landscape/Foliage/Audio-MetaSounds/World Partition, Movie Render Queue, GAS mutation, and an unsandboxed editor-Python escape hatch — everything else (actors, scene, assets, materials, meshes, sequencer, Niagara, UMG, PCG, data tables, tests, screenshots, logs) is already covered and re-porting it is wasted effort.
10. Ship TEE's UE know-how as Agent Skills (`AgentSkillToolset` assets) and Claude Code skills rather than system-prompt stuffing — this is Epic's sanctioned on-demand context mechanism (their PCG toolset explicitly relies on paired `Skill_PCG*` packs for reliable output), and it keeps per-session seed tokens near zero.
11. For the Blender side, mirror the winning UE patterns validated here: gateway/meta-tool discovery instead of eager tool registration, a whole-graph/text DSL for node-graph domains (shader nodes, geometry nodes) instead of per-node calls, `refPath`-style compact object references, and a sandboxed batch-script tool for multi-step operations.
12. Setup/integration facts to encode in TEE's UE connector: enable `ModelContextProtocol` + `AllToolsets` (server exposes zero tools without the latter); auto-start via `EditorPerProjectUserSettings.ini` `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings] bAutoStartServer=True` or `-ModelContextProtocolStartServer`; endpoint `http://127.0.0.1:8000/mcp`, Streamable HTTP, protocol `2025-06-18`, `Mcp-Session-Id` header, `Accept` must include both `application/json` and `text/event-stream` (`tools/call` streams SSE); loopback-only, origin-checked, no auth — TEE must run on the same machine or provide its own authenticated tunnel.
