"""The trust kernel (A43 T-1): ONE capability model, default deny, taint-aware.

Defensive security on the owner's own machine: this module is the single
decision point that answers, everywhere, **may THIS caller invoke THIS
capability on THIS project right now?** It replaces four scattered
permission flags (`allow_code_exec`, `allow_local`, `allow_sa`, gateway
`enable`) which each knew only themselves and therefore could not reason
about composition — a fronted backend steering a chore that triggers a
step that writes files.

Layers (research 65's dependency spine; this file is L0+L1, and L3/L4's
decision function):

    L0 capability map      verbs+RESOURCES; every tool tabled; unknown = refuse
    L1 grants              per project, default deny, read tier open
    L3 taint               a property of an ID, never of a string
    L4 the one check       trust.check(), called from registry.call + 3 surfaces

Two laws this file encodes and never bends:

1. **Default deny outside the read tier.** The read tier cannot change a
   byte, so it stays open even when the trust file is broken (fail OPEN
   for reads, fail CLOSED for side effects — research 62). A broken
   config must never brick `kb_search`; it must always brick `run-adhoc`.
2. **A tainted task may never invoke a side-effecting capability.**
   Untainting happens only in a live human turn. Capabilities are
   verb+RESOURCE, so a write to an inert artifact and a write to a policy
   file are different capabilities (research 63) — a path can never
   silently become privilege escalation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# -- L0: capabilities (verb + RESOURCE) ------------------------------------

# The read tier: nothing here can change a byte. Open by default (that is
# what makes onboarding a new project a zero-risk decision) and open even
# when the trust config is unreadable.
READ_TIER: frozenset[str] = frozenset(
    {
        "read-scene",
        "read-state",
        "read-session",
        "read-kb",
        "read-extract",
        "read-assets",
        "read-design",
        "read-uefn",
        # A45 P2: solvers, optimisers and local medical-image reads change
        # no byte of the owner's world - they are arithmetic over inputs the
        # caller already supplied, so they belong in the open tier.
        "read-compute",
        "read-medimg",
        # A45 P2d: querying a headless BI layer is a READ - it changes no
        # byte of the owner's world. It is nonetheless a TAINT SOURCE below,
        # exactly like read-kb: the answer is data from elsewhere and may
        # never go on to cause a side effect.
        "read-bi",
    }
)

# Everything else is default-deny. Verb+resource, deliberately: `write-
# artifacts` (inert declared outputs) is NOT `write-config` (grants future
# execution) is NOT `write-policy` (issues capability).
SIDE_EFFECTING: frozenset[str] = frozenset(
    {
        "fetch-web",
        "write-scene",
        "write-state",
        "write-artifacts",
        "write-config",
        "write-policy",
        "call-engine",
        "call-paid-engine",
        "switch-engine",
        "front-backend",
        "run-declared-step",
        "run-adhoc",
        "exec-code",
        # A45 P2: driving a local headless service (Orthanc, Cube, a trading
        # research daemon). It can change that service's state, and whatever
        # it answers is quoted data - hence a taint source below.
        "call-service",
        # RESERVED AND DELIBERATELY UNIMPLEMENTED. No tool in this codebase
        # requests it and none should: placing an order moves real money, and
        # that is a decision a human takes in their broker's own interface.
        # Named here so its absence is visible rather than merely assumed.
        "place-order",
    }
)

CAPABILITIES: frozenset[str] = READ_TIER | SIDE_EFFECTING

# Capabilities no config may grant, ever, by any route. `place-order` is
# reserved so its ABSENCE is visible; without this it sat in CAPABILITIES
# and `Grants.from_config` accepted it silently - and since A45 P0a made
# grants hot-reload, a single edited line would have activated it with no
# restart and no prompt. The guard is that the line cannot parse at all.
NEVER_GRANTABLE: frozenset[str] = frozenset({"place-order"})

# High-risk capabilities enforce deny-by-default from day one, shadow mode
# or not (research 64 FP-2: shadow-first governs engine CHOICE, never
# SAFETY — an open rollout window would be an open door, and it would feed
# the very traces that decide when to close it).
HIGH_RISK: frozenset[str] = frozenset(
    {
        "run-adhoc",
        "exec-code",
        "write-config",
        "write-policy",
        "call-paid-engine",
        "place-order",
    }
)

# A TAINT denial is a safety denial by definition, so the shadow band must
# not cover the capabilities the law is actually about: anything that
# executes, egresses, or writes policy refuses immediately whatever the
# rollout stage. HIGH_RISK alone was the wrong set to reuse here - it left
# 'run-declared-step' and 'fetch-web' in shadow, so a job that had read a
# web page could still start a build or fetch again. Found by running the
# lane against a real project (A43 P4), where a tainted job triggered a
# step that downloads tens of gigabytes.
TAINT_ENFORCED: frozenset[str] = HIGH_RISK | frozenset({"run-declared-step", "fetch-web"})

# Capabilities whose RESULTS are untrusted content: invoking one taints the
# calling task's derived ids (research 62's minting sources). KB prose and
# third-party media grounds nothing by the A30 law; a fronted backend's
# output — descriptions included — is quoted data, never instruction.
TAINT_SOURCES: frozenset[str] = frozenset(
    {
        "fetch-web",
        "front-backend",
        "read-kb",
        "read-extract",
        "call-paid-engine",
        "call-service",
        "read-bi",
    }
)

# Caller classes. The A42 task graph already stamps three of the six; L2
# mints `live-turn` at the MCP boundary and NEVER accepts it from below.
CALLER_CLASSES: frozenset[str] = frozenset(
    {"live-turn", "chore", "job", "scheduled", "gateway-fronted", "content-derived"}
)

# -- L0: the tool table ----------------------------------------------------
#
# Reviewed ONCE, here, rather than as 103 scattered decisions (research 62).
# Families carry a default; the exceptions — mutations living inside a read
# family, and everything high-risk — are named individually and win. A tool
# matching neither is a STARTUP ERROR, which is what makes completeness
# structural instead of a promise: a future tool cannot silently escape the
# kernel, because the server refuses to boot until it is tabled.

_FAMILY: tuple[tuple[str, str], ...] = (
    ("kb_", "read-kb"),
    ("ex_", "read-extract"),
    ("as_", "read-assets"),
    ("gd_", "read-design"),
    ("sk_", "read-scene"),  # A53: seamkiln garment queries
    ("uefn_", "read-uefn"),
    ("sim_", "write-scene"),
    ("capture_", "call-engine"),
    ("llm_", "call-engine"),
    ("plaus_", "read-scene"),
    ("mat_", "read-scene"),
    # --- A45 P2: the headless fleet ---
    ("solve_", "read-compute"),  # HiGHS / OR-Tools / Cbc / SCIP
    ("quant_", "read-compute"),  # skfolio / PyPortfolioOpt
    # DELIBERATELY NO ("cad_", ...) ENTRY either. A cad tool that BUILDS
    # writes a file; one that MEASURES does not. A single prefix default
    # would have given the writer the open read tier. Tabled individually
    # below, same lesson as trade_.
    # DELIBERATELY NO ("trade_", ...) ENTRY. A prefix default would let a
    # future tool called trade_place_order inherit the OPEN read tier just
    # by being named. Every trading tool is tabled INDIVIDUALLY in
    # _EXPLICIT, so an untabled trade_* name is a startup error - which is
    # the point: the kernel refuses to boot rather than quietly permit.
    ("med_", "read-medimg"),  # DICOM / MONAI / Qiber3D
    ("bi_", "read-bi"),  # Cube: a read, but the answer is quoted data
    ("svc_", "call-service"),  # generic headless-service probes
)

_EXPLICIT: dict[str, str] = {
    # A47: senses a blind host borrows. Tabled EXPLICITLY, not by family
    # prefix - A45's lesson was that a prefix silently admits whatever is
    # named next, and these read files and POST to 127.0.0.1. They mutate
    # nothing and nothing leaves the machine, so: the read tier.
    # A48: the PDF lane writes files, so it sits on write-artifacts -
    # tabled explicitly, never by family prefix (the A45 lesson).
    # A52: purge DELETES, so it sits on write-artifacts and is tabled
    # explicitly. Its own dry-run default is the real guard.
    "tee_purge": "write-artifacts",
    "pdf_compose": "write-artifacts",
    "pdf_edit": "write-artifacts",
    "sense_describe": "read-extract",
    "sense_frame": "read-scene",
    "sense_viewport": "read-scene",
    "sense_camera": "read-scene",
    "sense_transcribe": "read-extract",
    # --- A67: the point-cloud scan-prep lane ---
    # DELIBERATELY NO ("pc_", ...) FAMILY ROW. Same lesson as cad_ and trade_
    # above: a prefix default silently admits whatever is named next, and
    # nearly every tool in this lane WRITES - a cloud into the workspace, a
    # DXF onto disk. Reads get the open read tier; anything that mints a
    # cloud or emits a file is write-artifacts, tabled one line at a time.
    "pc_open": "write-artifacts",  # copies the cloud into .tee/pointcloud
    "pc_stat": "read-compute",
    "pc_level": "write-artifacts",
    "pc_control_add": "write-artifacts",
    "pc_control_verify": "read-compute",
    "pc_scale_apply": "write-artifacts",
    "pc_slice": "write-artifacts",
    "pc_section": "write-artifacts",
    "pc_export": "write-artifacts",
    "pc_report": "write-artifacts",
    "pc_crop": "write-artifacts",
    "pc_clean": "write-artifacts",
    "pc_ortho": "write-artifacts",
    "pc_merge": "write-artifacts",  # shells out to CloudCompare via capture_*
    # --- always-loaded MCP surface (17) ---
    "tee_status": "read-session",
    "tee_recall": "read-state",
    "tee_remember": "write-state",
    "tee_scene_summary": "read-scene",
    "tee_entity_detail": "read-scene",
    "tee_diff": "read-scene",
    "tee_batch": "write-scene",
    "tee_checkpoint": "write-scene",
    "tee_rollback": "write-scene",
    "tee_job": "read-session",
    "tee_capture": "write-scene",
    "tee_media": "read-extract",
    "tee_script": "exec-code",
    "tee_web_lookup": "fetch-web",
    "tee_search_tools": "read-session",
    "tee_describe_tool": "read-session",
    # tee_call dispatches INTO the registry, where the target tool's own
    # capability is checked. Its own verb is therefore the meta-read; the
    # inner check is what actually gates the work (fixture asserts this).
    "tee_call": "read-session",
    # --- assets: mutations and stores inside a read family ---
    "as_import": "write-scene",
    "as_place": "write-scene",
    "as_material": "write-scene",
    "as_photo_material": "write-scene",
    "as_sun": "write-scene",
    "as_sheet": "write-scene",
    "as_ingest": "write-state",
    "as_publish_library": "write-state",
    "as_generate": "call-engine",
    # --- extract: writes inside a read family ---
    "ex_ingest": "write-state",
    "ex_register": "write-state",
    "ex_store_facts": "write-state",
    "ex_prepare": "write-state",
    # --- kb: the staging write (lineage must survive it, research 63) ---
    "kb_propose": "write-state",
    # --- seamkiln: the two that leave a file behind (A53 P4) ---
    "sk_plot": "write-artifacts",
    "sk_techpack": "write-artifacts",
    "sk_materials": "write-artifacts",  # its export/import actions touch files
    "sk_interchange": "write-artifacts",
    "sk_handoff": "write-artifacts",  # A65: writes a bundle for another application
    # --- design: the store/render writes ---
    "gd_store": "write-state",
    "gd_render": "write-state",
    # --- capture: ingest stores, apply mutates the owner's scenes ---
    "capture_ingest": "write-state",
    "capture_apply": "write-scene",
    # --- llm: switching engines is its own verb; a PAID target additionally
    # demands call-paid-engine (checked at the call site, SI-B16's teeth) ---
    "llm_switch": "switch-engine",
    # --- uefn: mutations and the compiler ---
    "uefn_place_device": "write-scene",
    "uefn_entity_batch": "write-scene",
    "uefn_compile": "call-engine",
    "uefn_pack_channels": "call-engine",
    # --- physical tier-2 modelling ops (mutate the scene) ---
    "array_along": "write-scene",
    "opening_cut": "write-scene",
    "param_set": "write-scene",
    "profile_extrude": "write-scene",
    "roof": "write-scene",
    "slab": "write-scene",
    "stairs": "write-scene",
    "wall_with_openings": "write-scene",
    "mat_assign": "write-scene",
    "joinery_check": "read-scene",
    "sketch_solve": "read-scene",
    "phys_tier0": "read-scene",
    "sim_ready": "read-scene",
    # --- session / exports / boards ---
    "handoff": "read-session",
    # A45 P2f: trading RESEARCH only. Named one by one, never by prefix.
    # Each is pure arithmetic over series the caller supplied: no network,
    # no broker, no credential, no order verb. There is deliberately no
    # trade_place_*, trade_order_*, trade_account_* or trade_funds_* here,
    # and an untabled trade_* name is a startup error rather than a default.
    "trade_backtest": "read-compute",
    "trade_detail": "read-compute",
    "trade_probe": "read-compute",
    # A45 P2e: CAD. Build writes an artifact; measure and probe do not.
    "cad_scad_build": "write-artifacts",
    "cad_measure": "read-compute",
    "cad_probe": "read-compute",
    "report_savings": "read-session",
    "report_spend": "read-session",
    "board_compose": "write-state",
    "export_for_uefn": "write-artifacts",
    "export_preflight": "read-scene",
    # --- Blender adapter ---
    "bl_api_detail": "read-scene",
    "bl_search_docs": "read-scene",
    "bl_scene_stats": "read-scene",
    "bl_check_against_plan": "read-scene",
    "bl_assign_material": "write-scene",
    "bl_build_from_plan": "write-scene",
    "bl_render": "write-artifacts",
    "bl_execute_python": "exec-code",  # arbitrary Python in the DCC
    # --- FreeCAD adapter ---
    "fc_drawing": "write-scene",
    "fc_export": "write-artifacts",
    # --- A66: partkiln, the mechanical CAD lane. Three of these write files
    # and two mutate the document, so every one is tabled INDIVIDUALLY (the
    # cad_/trade_ rule above): there is deliberately no ("pk_", ...) family
    # row, and an untabled pk_* name is a startup error, not a default. ---
    "pk_probe": "read-compute",
    "pk_verbs": "read-scene",
    "pk_lint": "read-compute",
    "pk_query": "read-scene",
    "pk_measure": "read-compute",
    "pk_check": "read-compute",
    "pk_standards": "read-compute",
    "pk_materials": "read-compute",  # pure lookup; assignment is a batch `set`
    "pk_bom": "read-scene",
    "pk_drawing": "write-artifacts",
    "pk_export": "write-artifacts",
    "pk_flat": "write-artifacts",
    "pk_import": "write-scene",
    "pk_script": "write-scene",  # its replay action mutates the live document
    # --- gateway control. Accepting a drifted backend fingerprint is a
    # TRUST decision about a third party, not a read - so it is policy
    # (a deliberate tightening the kernel exists to make; recorded). ---
    "gw_status": "read-session",
    "gw_accept": "write-policy",
    # --- Home Builder ---
    "hb_status": "read-scene",
    "hb_room": "read-scene",
    "hb_layout": "read-scene",
    "hb_joinery_spec": "read-scene",
    "hb_cutlist": "read-scene",
    "hb_cabinet": "write-scene",
    # --- pins (Unreal actor tags) ---
    "pin_list": "read-scene",
    "pin_show": "read-scene",
    "pin_export": "read-scene",
    "pin_set": "write-scene",
    "pin_remove": "write-scene",
    "pin_fill": "write-scene",
    "pin_import": "write-scene",
    # --- Unreal adapter ---
    "ue_editor_state": "read-scene",
    "ue_entity_detail": "read-scene",
    "ue_scene_checks": "read-scene",
    "ue_look": "read-scene",
    "ue_toolset": "read-scene",
    "ue_toolsets": "read-scene",
    "ue_describe_tool": "read-scene",
    "ue_graph_dsl_docs": "read-scene",
    "ue_capture": "write-artifacts",
    "ue_blueprint_function": "write-scene",
    "ue_settle": "write-scene",
    "ue_call": "write-scene",  # dispatches editor ops; assume it mutates
    "ue_editor_python": "exec-code",  # arbitrary Python in the editor
    "ue_script": "exec-code",
    # --- web ---
    "web_search": "fetch-web",
    # --- the pipeline lane (A43 P0+), declared here so the table is the
    # single review surface even before the lane ships ---
    "pipeline_list": "read-state",
    "pipeline_run": "run-declared-step",
    "pipeline_adhoc": "run-adhoc",
    # write-state, not read-state: it drafts a file. The read tier fails
    # OPEN because nothing in it can change a byte, so anything that does
    # must sit outside it however advisory its output is.
    "pipeline_init": "write-state",
    "pipeline_adopt": "write-state",
    "trust_grant": "write-policy",
    "tee_trust": "read-session",
}


def capability_for(tool_name: str) -> str:
    """The capability a tool needs. Unknown tool -> refuse (startup guard).

    Explicit entries win over family defaults: a mutation living inside a
    read family must never inherit the family's read verb."""
    explicit = _EXPLICIT.get(tool_name)
    if explicit is not None:
        return explicit
    for prefix, capability in _FAMILY:
        if tool_name.startswith(prefix):
            return capability
    raise TeeError(
        "trust_untabled_tool",
        f"Tool '{tool_name}' has no capability in the trust table.",
        fix="Add it to _EXPLICIT (or a family) in kernel/trust.py - the "
        "table is the single review surface; an untabled tool cannot ship.",
    )


# Every shadow-band denial this process made, bounded. The L7 rollout view
# reads it: the flip is an owner decision informed by evidence, and the
# evidence has to come from somewhere other than a caller's assertion.
SHADOW_DENIALS: list[dict[str, Any]] = []


def record_shadow_denial(entry: dict[str, Any]) -> None:
    SHADOW_DENIALS.append(entry)
    if len(SHADOW_DENIALS) > 500:
        del SHADOW_DENIALS[: len(SHADOW_DENIALS) - 500]


# -- L1: grants ------------------------------------------------------------

# A45 P0b. One line the owner writes instead of assembling a list by hand.
# Presets are ADDITIVE with an explicit `grants = [...]`, and every preset
# is spelled out here so "what did I just allow" is answerable by reading,
# not by running. No preset silently includes a HIGH_RISK capability the
# name does not advertise.
PROFILES: dict[str, frozenset[str]] = {
    # look, never touch: the read tier only (baseline already covers it)
    "readonly": frozenset(),
    # drive this project's own declared build steps
    "build": frozenset({"run-declared-step", "write-artifacts"}),
    # the owner's own workstation: declared steps, ad-hoc argv, and the
    # Python escape hatch the kernel was always designed to have.
    "workstation": frozenset(
        {"run-declared-step", "run-adhoc", "exec-code", "write-artifacts", "read-compute"}
    ),
    # workstation plus the metered, off-machine engine
    "workstation+paid": frozenset(
        {
            "run-declared-step",
            "run-adhoc",
            "exec-code",
            "write-artifacts",
            "read-compute",
            "call-paid-engine",
        }
    ),
}


def profile_covering(capability: str) -> str | None:
    """The smallest named profile that would grant `capability` - so a
    refusal can offer one line instead of a scavenger hunt."""
    best: tuple[int, str] | None = None
    for name, caps in PROFILES.items():
        if capability in caps and (best is None or len(caps) < best[0]):
            best = (len(caps), name)
    return best[1] if best else None


@dataclass
class Grants:
    """What the owner authorized, per project. Plain TOML lines, no policy
    language: if it ever needs a DSL it is wrong (research 61)."""

    granted: frozenset[str] = frozenset()
    source: str = "(no trust config)"
    enforce_quality_band: bool = False  # L6/L7: the owner-signed flip
    broken: str | None = None  # config unreadable -> fail closed for effects
    profile: str | None = None  # A45: the preset that widened this, if any

    @classmethod
    def from_config(cls, config: Any, source: str = "(config)") -> Grants:
        """Read `[trust] grants = [...]` plus the legacy flag aliases, so
        every existing .tee/config.toml keeps working untouched."""
        trust_cfg = dict(getattr(config, "trust", {}) or {})
        granted: set[str] = set()
        profile = trust_cfg.get("profile")
        if profile is not None:
            key = str(profile).strip()
            if key not in PROFILES:
                raise TeeError(
                    "trust_unknown_profile",
                    f"[trust] profile = '{key}' is not a known profile.",
                    fix=f"Known profiles: {', '.join(sorted(PROFILES))}.",
                )
            smuggled = PROFILES[key] & NEVER_GRANTABLE
            if smuggled:  # unreachable today; asserted by test, kept as a tripwire
                raise TeeError(
                    "trust_never_grantable",
                    f"profile '{key}' contains {sorted(smuggled)}, which can never be granted.",
                    fix="This is a TEE bug - report it.",
                )
            granted |= set(PROFILES[key])
        for name in trust_cfg.get("grants") or []:
            text = str(name).strip()
            if text in NEVER_GRANTABLE:
                raise TeeError(
                    "trust_never_grantable",
                    f"'{text}' can never be granted. It is reserved so that its "
                    f"absence is auditable, not to be switched on.",
                    fix="TEE does not place orders or move funds under any "
                    "configuration. Do that in your broker's own interface.",
                )
            if text not in CAPABILITIES:
                raise TeeError(
                    "trust_unknown_capability",
                    f"[trust] grants lists '{text}', which is not a capability.",
                    fix=f"Known: {', '.join(sorted(CAPABILITIES))}.",
                )
            granted.add(text)
        # Legacy flags become aliases (research 62's migration law): the
        # behavior each flag bought is preserved exactly, through the kernel.
        if getattr(config, "allow_code_exec", None):
            granted.add("exec-code")
        assets = dict(getattr(config, "assets", {}) or {})
        if assets.get("allow_local"):
            granted.add("fetch-web")
        if assets.get("allow_sa"):
            granted.add("read-assets")
        gateway = dict(getattr(config, "gateway", {}) or {})
        backends = dict(gateway.get("backends") or {}).values()
        if any(dict(b or {}).get("enable", True) for b in backends):
            granted.add("front-backend")
        return cls(
            granted=frozenset(granted),
            source=source,
            enforce_quality_band=bool(trust_cfg.get("enforce", False)),
            profile=str(profile).strip() if profile is not None else None,
        )


class GrantsWatcher:
    """A45 P0a: the owner's config is authoritative NOW, not at boot.

    Grants used to be read once at `TeeApp` construction, so an edit was
    invisible until Claude Desktop restarted - and a widening that landed
    nowhere is indistinguishable from a bug (the trap SI-B17 named, hit
    again by the session that wrote this). This re-reads on mtime change:
    one stat() per decision, no daemon, no polling thread.

    A config that stops parsing does NOT revert to the last good grants -
    that would let a typo silently keep power on. It fails closed for side
    effects via `broken`, while the read tier keeps answering."""

    def __init__(self, path: Path | str, loader: Callable[[], Grants]) -> None:
        self.path = Path(path)
        self.loader = loader
        self._stamp: tuple[int, int] | None = None
        self._cached: Grants | None = None

    def _mtime(self) -> tuple[int, int]:
        try:
            st = self.path.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return (0, 0)

    def __call__(self) -> Grants:
        stamp = self._mtime()
        if self._cached is not None and stamp == self._stamp:
            return self._cached
        self._stamp = stamp
        try:
            self._cached = self.loader()
        except TeeError as exc:
            self._cached = Grants(source=str(self.path), broken=exc.message)
        except Exception as exc:  # a malformed file is the owner's typo, not a crash
            self._cached = Grants(source=str(self.path), broken=str(exc))
        return self._cached


# The capabilities every project holds without asking: the read tier, plus
# the ambient verbs TEE has always exercised on its own state and engines.
# These are what make "a new project is useful immediately, at zero risk"
# true — and what keeps the 790-test battery behaving identically.
BASELINE: frozenset[str] = READ_TIER | frozenset(
    {
        "write-scene",
        "write-state",
        "write-artifacts",
        "call-engine",
        "switch-engine",
        "fetch-web",
    }
)


@dataclass
class Decision:
    allowed: bool
    capability: str
    caller: str
    reason: str
    grant: str | None = None
    source: str | None = None  # the config file actually loaded (SI-B17)
    tainted_by: list[str] = field(default_factory=list)
    # Is this decision enforced NOW, or is it in the shadow band?
    # Safety never waits on a rollout: high-risk capabilities and broken-
    # config denials enforce from day one (research 64 FP-2). Only the
    # taint-vs-quality band is measured first and enforced after the
    # owner's signed flip (L7).
    enforced: bool = True

    def raise_if_denied(self, tool_name: str) -> None:
        if self.allowed:
            return
        raise TeeError("trust_denied", f"{tool_name}: {self.reason}", fix=self.fix())

    def fix(self) -> str:
        if self.tainted_by:
            return (
                "This task carries untrusted content "
                f"({', '.join(self.tainted_by[:3])}). Untrusted content can "
                "never cause a side effect. Re-run the step yourself in a "
                "live turn if you have read the content and intend it."
            )
        where = self.source or ".tee/config.toml"
        line = f'grants = ["{self.capability}"]'
        fix = (
            f"Add {line} under [trust] in {where} - that is the config file "
            "this server actually loaded (SI-B17). It takes effect on the "
            "next call; no restart (A45 P0a)."
        )
        cover = profile_covering(self.capability)
        if cover:
            fix += f'  One line instead: profile = "{cover}".'
        return fix


def check(
    capability: str,
    *,
    caller: str,
    grants: Grants,
    taint: tuple[str, ...] = (),
    consent: bool = False,
) -> Decision:
    """The ONE decision. Every entry surface routes here (L4).

    Order matters and is the security argument:
      1. an unknown capability is refused (fail closed on our own bugs);
      2. the read tier always answers - it cannot change a byte, so a
         broken trust file must not brick it;
      3. the taint law - untrusted content may never cause a side effect,
         and only a live human turn can lift that;
      4. the grant - default deny, with the exact missing line named.
    """
    if capability not in CAPABILITIES:
        return Decision(
            allowed=False,
            capability=capability,
            caller=caller,
            reason=f"'{capability}' is not a known capability (refusing rather than guessing)",
        )
    if caller not in CALLER_CLASSES:  # forged or unknown class: treat as the worst
        caller = "content-derived"

    if capability in READ_TIER:
        return Decision(
            allowed=True, capability=capability, caller=caller, reason="read tier", grant="baseline"
        )

    high_risk = capability in HIGH_RISK

    if grants.broken:
        return Decision(
            allowed=False,
            capability=capability,
            caller=caller,
            reason=f"the trust config could not be read ({grants.broken}), so side "
            "effects fail closed while the read tier keeps answering",
        )

    # The central law. A live human turn is the ONLY untaint path, and for
    # high-risk capabilities the human must have consented to THIS call, not
    # merely be present (research 63's habituation limit: the human gate is
    # the last layer, never the only one).
    if taint and (caller != "live-turn" or (high_risk and not consent)):
        return Decision(
            allowed=False,
            capability=capability,
            caller=caller,
            reason=f"a {caller} task carrying untrusted content may not invoke '{capability}'",
            tainted_by=list(taint),
            source=grants.source,
            # Safety-critical taint denials (egress, execution, policy)
            # enforce immediately; the rest are the shadow band.
            enforced=capability in TAINT_ENFORCED,
        )

    if capability in grants.granted:
        return Decision(
            allowed=True,
            capability=capability,
            caller=caller,
            reason="granted",
            grant=grants.source,
        )
    if capability in BASELINE and not high_risk:
        return Decision(
            allowed=True,
            capability=capability,
            caller=caller,
            reason="baseline capability",
            grant="baseline",
        )
    return Decision(
        allowed=False,
        capability=capability,
        caller=caller,
        reason=f"'{capability}' is not granted for this project (default deny)",
        source=grants.source,
    )
