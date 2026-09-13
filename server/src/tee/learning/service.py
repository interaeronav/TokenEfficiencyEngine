"""Bounded project-local learning, chronological evaluation and reversible promotion.

The observer accepts only identifiers and scalars. It never retains tool arguments,
results, exceptions or input pointers. Operational completion and reported quality
are distinct domains from evidence supplied by a deterministic verifier.
"""

from __future__ import annotations

import contextlib
import json
import math
import re
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

DOMAINS = frozenset({"execution", "verified", "reported"})
CATEGORIES = frozenset(
    {
        "completed",
        "error",
        "failed",
        "validation",
        "refused",
        "queued",
        "cancelled",
        "unreachable",
        "timeout",
        "feedback",
        "skipped",
        "unknown",
        "unverifiable",
    }
)
# "unverifiable" (W0, 2026-09-13): the hop ran and the chore's validate()
# accepted, but that validator was MEASURED to accept every seeded wrong answer
# (chores.VERIFIER_COVERAGE), so its acceptance is not evidence of quality. The
# row is kept for latency and coverage; only the success label is withheld.
# Same family as "unreachable" - a category that carries no quality claim.
UNLABELLED = frozenset(
    {"refused", "queued", "cancelled", "unreachable", "skipped", "unknown", "unverifiable"}
)
if not UNLABELLED <= CATEGORIES:  # pragma: no cover - a boot-time programming error
    # These two sets were independent literals, and observe() is fail-open: a
    # category missing from CATEGORIES fails _validate, the exception is
    # swallowed, and the observation VANISHES - no error, no row, no signal.
    # Adding "unverifiable" to UNLABELLED alone did exactly that, and only a
    # persistence test caught it. Telemetry that fails open loses data quietly,
    # so the invariant is enforced where it cannot be forgotten: at import,
    # loudly, the way an untabled capability or an unlaned scene-writer already
    # refuses to let this server boot.
    raise RuntimeError(
        "learning: UNLABELLED contains categories the store will reject and then "
        f"silently drop: {sorted(UNLABELLED - CATEGORIES)}. Add them to CATEGORIES."
    )
MAX_EVENTS, MAX_SNAPSHOTS = 2000, 6
MIN_TRAIN, MIN_HOLDOUT, EVALUATE_EVERY, MIN_SUPPORT = 64, 16, 32, 6
MAX_MODEL_BYTES = 131072
MAX_TRAIN_ROWS, AUTO_INTERVAL_S = 512, 5.0
MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000
SAFE_ID = re.compile(r"[A-Za-z0-9_.:+@-]{1,96}\Z", re.ASCII)
SOURCES = {"execution": "runtime", "verified": "verifier", "reported": "feedback"}
_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
 domain TEXT NOT NULL, context TEXT NOT NULL, choice TEXT NOT NULL, version TEXT NOT NULL,
 success INTEGER, elapsed_ms REAL NOT NULL, tokens INTEGER, group_id TEXT NOT NULL,
 category TEXT NOT NULL, source TEXT NOT NULL, feedback_of TEXT UNIQUE,
 prediction REAL, prediction_model INTEGER, fixed_baseline REAL, created_ms INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS domain_events ON events(domain,seq);
CREATE INDEX IF NOT EXISTS grouped_events ON events(domain,group_id);
CREATE TABLE IF NOT EXISTS groups (
 domain TEXT NOT NULL, group_id TEXT NOT NULL, first_seq INTEGER NOT NULL,
 last_seq INTEGER NOT NULL, PRIMARY KEY(domain,group_id));
CREATE TABLE IF NOT EXISTS snapshots (
 id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT NOT NULL, model_json TEXT NOT NULL,
 through_seq INTEGER NOT NULL, evaluated_seq INTEGER NOT NULL, fixed_baseline REAL NOT NULL,
 created_ms INTEGER NOT NULL, drifted INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS domains (
 domain TEXT PRIMARY KEY, active_id INTEGER, previous_id INTEGER, active_since INTEGER DEFAULT 0,
 last_evaluated_seq INTEGER DEFAULT 0, trainable_count INTEGER DEFAULT 0,
 last_auto_count INTEGER DEFAULT 0, evaluation_json TEXT, drift_json TEXT);
"""


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError("invalid_identifier")
    return value


def _number(value: Any, *, integer: bool = False) -> float | int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("invalid_measurement")
    if not math.isfinite(value) or not 0 <= value <= 1e12:
        raise ValueError("invalid_measurement")
    if integer and not isinstance(value, int):
        raise ValueError("invalid_measurement")
    return value


def _error(code: str = "learning_storage") -> TeeError:
    return TeeError(
        code,
        "Learning state is unavailable or the request is invalid.",
        fix="Use learning status; check the identifiers and project learning state.",
    )


class LearningService:
    """One service per TeeApp. Construction performs no filesystem work."""

    def __init__(self, project_root: Path, config: dict | None = None) -> None:
        self.path = Path(project_root) / ".tee" / "learning" / "state.sqlite"
        cfg = config if isinstance(config, dict) else {}
        malformed = config is not None and not isinstance(config, dict)
        malformed |= any(
            key in cfg and type(cfg[key]) is not bool for key in ("enabled", "auto_promote")
        )
        self.enabled = cfg.get("enabled", True) is True
        self.auto_promote = cfg.get("auto_promote", True) is True
        self._lock = threading.RLock()
        self._connection: sqlite3.Connection | None = None
        self._health = "invalid_config" if malformed else "ok"
        if malformed:
            self.enabled = False
        self._closed = False
        self._last_auto_monotonic: float | None = None

    def _writer(self) -> sqlite3.Connection:
        if self._closed:
            raise _error("learning_closed")
        if self._connection is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(
                self.path, timeout=1, isolation_level=None, check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=1000")
                conn.executescript(_SCHEMA)
                columns = {r[1] for r in conn.execute("PRAGMA table_info(snapshots)")}
                if "created_ms" not in columns:
                    conn.execute(
                        "ALTER TABLE snapshots ADD COLUMN created_ms INTEGER NOT NULL DEFAULT 0"
                    )
                conn.execute("INSERT OR IGNORE INTO meta VALUES ('schema','1')")
                if self._meta(conn, "schema", None) != 1:
                    raise ValueError("unsupported_schema")
                for domain in DOMAINS:
                    conn.execute("INSERT OR IGNORE INTO domains(domain) VALUES (?)", (domain,))
            except Exception:
                conn.close()
                raise
            self._connection = conn
        return self._connection

    @contextlib.contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._writer()
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise

    @contextlib.contextmanager
    def _reader(self) -> Iterator[sqlite3.Connection | None]:
        if not self.path.is_file():
            yield None
            return
        conn = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1)
        conn.row_factory = sqlite3.Row
        try:
            if self._meta(conn, "schema", None) != 1:
                raise ValueError("unsupported_schema")
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _meta(conn: sqlite3.Connection, key: str, default: Any) -> Any:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    @staticmethod
    def _set_meta(conn: sqlite3.Connection, key: str, value: Any) -> None:
        conn.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, json.dumps(value)))

    @staticmethod
    def _state(conn: sqlite3.Connection, domain: str) -> dict:
        row = conn.execute("SELECT * FROM domains WHERE domain=?", (domain,)).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def _snapshot(conn: sqlite3.Connection, snapshot_id: int | None) -> dict | None:
        if snapshot_id is None:
            return None
        row = conn.execute("SELECT * FROM snapshots WHERE id=?", (snapshot_id,)).fetchone()
        if row is None or row["drifted"]:
            return None
        out = dict(row)
        if len(out["model_json"].encode()) > MAX_MODEL_BYTES:
            raise ValueError("model_invalid")
        out["model"] = json.loads(out.pop("model_json"))
        if not isinstance(out["model"], dict) or out["model"].get("domain") != out["domain"]:
            raise ValueError("model_invalid")
        return out

    @staticmethod
    def _validate(
        domain: str,
        context: str,
        choice: str,
        version: str,
        success: bool | None,
        elapsed_ms: float,
        tokens: int | None,
        group_id: str | None,
        category: str,
    ) -> dict:
        if domain not in DOMAINS or category not in CATEGORIES:
            raise ValueError("invalid_category")
        if success is not None and type(success) is not bool:
            raise ValueError("invalid_label")
        return {
            "domain": domain,
            "context": _identifier(context),
            "choice": _identifier(choice),
            "version": _identifier(version),
            "success": None if category in UNLABELLED else success,
            "elapsed_ms": _number(elapsed_ms),
            "tokens": None if tokens is None else _number(tokens, integer=True),
            "group_id": _identifier(group_id) if group_id is not None else uuid.uuid4().hex,
            "category": category,
            "source": SOURCES[domain],
        }

    def observe(
        self,
        *,
        domain: str,
        context: str,
        choice: str,
        version: str,
        success: bool | None,
        elapsed_ms: float,
        tokens: int | None = None,
        group_id: str | None = None,
        category: str = "completed",
    ) -> str | None:
        """Fail-open instrumentation: invalid data or storage never changes tool behavior."""
        if not self.enabled or self._closed:
            return None
        try:
            row = self._validate(
                domain, context, choice, version, success, elapsed_ms, tokens, group_id, category
            )
            with self._lock:
                with self._transaction() as conn:
                    if self._meta(conn, "paused", False):
                        return None
                    event_id, due = self._insert(conn, row)
                self._health = "ok"
                if due:
                    self._evaluate_safely()
                return event_id
        except Exception:
            self._health = "observation_error"
            return None

    def _insert(
        self, conn: sqlite3.Connection, row: dict, feedback_of: str | None = None
    ) -> tuple[str, bool]:
        from tee.learning import model

        state = self._state(conn, row["domain"])
        snapshot = self._snapshot(conn, state.get("active_id"))
        probability = baseline = snapshot_id = None
        if (
            row["success"] is not None
            and snapshot
            and model.covered(snapshot["model"], row, MIN_SUPPORT)
        ):
            probability = float(model.predict(snapshot["model"], row)["success_probability"])
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("model_invalid")
            baseline, snapshot_id = snapshot["fixed_baseline"], snapshot["id"]
        event_id = "e_" + uuid.uuid4().hex
        columns = (
            "event_id",
            *row.keys(),
            "feedback_of",
            "prediction",
            "prediction_model",
            "fixed_baseline",
            "created_ms",
        )
        values = (
            event_id,
            *row.values(),
            feedback_of,
            probability,
            snapshot_id,
            baseline,
            int(time.time() * 1000),
        )
        cursor = conn.execute(
            "INSERT INTO events ("
            + ",".join(columns)
            + ") VALUES ("
            + ",".join("?" for _ in values)
            + ")",
            values,
        )
        seq = cursor.lastrowid
        conn.execute(
            "INSERT INTO groups VALUES (?,?,?,?) ON CONFLICT(domain,group_id) "
            "DO UPDATE SET last_seq=excluded.last_seq",
            (row["domain"], row["group_id"], seq, seq),
        )
        due = False
        if row["success"] is not None:
            count = state.get("trainable_count", 0) + 1
            scheduled = count - state.get("last_auto_count", 0) >= EVALUATE_EVERY
            wall_elapsed = time.time() - self._meta(conn, "last_auto_at", 0)
            mono_elapsed = (
                math.inf
                if self._last_auto_monotonic is None
                else time.monotonic() - self._last_auto_monotonic
            )
            due = (
                scheduled
                and count >= MIN_TRAIN + MIN_HOLDOUT
                and min(wall_elapsed, mono_elapsed) >= AUTO_INTERVAL_S
                and not self._meta(conn, "promotion_paused", False)
            )
            advance = scheduled and (due or count < MIN_TRAIN + MIN_HOLDOUT)
            conn.execute(
                "UPDATE domains SET trainable_count=?,last_auto_count=? WHERE domain=?",
                (count, count if advance else state.get("last_auto_count", 0), row["domain"]),
            )
            if due:
                self._set_meta(conn, "last_auto_at", time.time())
                self._last_auto_monotonic = time.monotonic()
            self._drift(conn, row["domain"], seq)
        self._prune_events(conn, seq)
        return event_id, due

    @staticmethod
    def _prune_events(conn: sqlite3.Connection, seq: int) -> None:
        if seq <= MAX_EVENTS:
            return
        expired = conn.execute(
            "SELECT seq,domain,group_id FROM events ORDER BY seq DESC LIMIT -1 OFFSET ?",
            (MAX_EVENTS,),
        ).fetchall()
        conn.executemany("DELETE FROM events WHERE seq=?", ((r["seq"],) for r in expired))
        # Normally one row expires. Inspect only its group instead of scanning
        # every retained group; keep first_seq while any of its rows remain.
        conn.executemany(
            "DELETE FROM groups WHERE domain=? AND group_id=? AND NOT EXISTS "
            "(SELECT 1 FROM events WHERE domain=? AND group_id=?)",
            ((d, g, d, g) for d, g in {(r["domain"], r["group_id"]) for r in expired}),
        )

    def _drift(self, conn: sqlite3.Connection, domain: str, seq: int) -> None:
        state = self._state(conn, domain)
        active = state.get("active_id")
        if active is None:
            return
        rows = conn.execute(
            "SELECT success,prediction,fixed_baseline FROM events WHERE domain=? "
            "AND prediction_model=? AND seq>? AND success IS NOT NULL "
            "ORDER BY seq DESC LIMIT 16",
            (domain, active, state["active_since"]),
        ).fetchall()
        if len(rows) < 16:
            return
        brier = sum((r["prediction"] - r["success"]) ** 2 for r in rows) / 16
        baseline = sum((r["fixed_baseline"] - r["success"]) ** 2 for r in rows) / 16
        if brier <= baseline + 0.08:
            return
        previous = self._snapshot(conn, state.get("previous_id"))
        restored = previous["id"] if previous else None
        conn.execute("UPDATE snapshots SET drifted=1 WHERE id=?", (active,))
        report = {
            "heuristic": "recent_16_brier",
            "count": 16,
            "brier": brier,
            "baseline_brier": baseline,
            "reverted_from": active,
            "restored": restored,
        }
        conn.execute(
            "UPDATE domains SET active_id=?,previous_id=NULL,active_since=?,"
            "drift_json=? WHERE domain=?",
            (restored, seq, json.dumps(report), domain),
        )
        self._set_meta(conn, "promotion_paused", True)

    def _evaluate_safely(self) -> None:
        try:
            self.evaluate()
        except Exception:
            self._health = "evaluation_error"

    @staticmethod
    def _split(rows: list[dict], watermark: int) -> tuple[list[dict], list[dict]]:
        groups: dict[str, list[dict]] = {}
        for row in rows:
            groups.setdefault(row["group_id"], []).append(row)
        complete = [
            g
            for g in groups.values()
            if g[0].get("group_first_seq", g[0]["seq"]) == g[0]["seq"]
            and g[-1].get("group_last_seq", g[-1]["seq"]) == g[-1]["seq"]
        ]
        eligible = [
            g
            for g in complete
            if g[0]["seq"] > watermark and any(r["success"] is not None for r in g)
        ]
        selected, count = [], 0
        for group in sorted(eligible, key=lambda g: g[0]["seq"], reverse=True):
            selected.append(group)
            count += sum(r["success"] is not None for r in group)
            if count >= MIN_HOLDOUT:
                break
        if count < MIN_HOLDOUT:
            return [], []
        boundary = min(group[0]["seq"] for group in selected)
        # Entire groups touching the holdout boundary are purged from training.
        # Late observations of an old group cannot leak across the split.
        train = [
            r
            for group in complete
            if group[-1]["seq"] < boundary
            for r in group
            if r["success"] is not None
        ]
        heldout = [r for group in selected for r in group if r["success"] is not None]
        return sorted(train, key=lambda r: r["seq"]), sorted(heldout, key=lambda r: r["seq"])

    @staticmethod
    def _training_window(rows: list[dict]) -> list[dict]:
        groups: dict[str, list[dict]] = {}
        for row in rows:
            groups.setdefault(row["group_id"], []).append(row)
        selected = []
        for group in sorted(groups.values(), key=lambda g: g[-1]["seq"], reverse=True):
            if len(selected) + len(group) > MAX_TRAIN_ROWS:
                break
            selected.extend(group)
        return sorted(selected, key=lambda row: row["seq"])

    def evaluate(self) -> dict:
        if not self.enabled:
            return {"evaluated": False, "reason": "disabled", "domains": {}}
        try:
            with self._lock:
                if not self.path.is_file():
                    return {"evaluated": False, "reason": "insufficient_data", "domains": {}}
                with self._transaction() as conn:
                    if self._meta(conn, "paused", False):
                        return {"evaluated": False, "reason": "paused", "domains": {}}
                    reports = {
                        domain: self._evaluate_domain(conn, domain) for domain in sorted(DOMAINS)
                    }
                    self._prune_snapshots(conn)
                    if any(r.get("evaluated", False) for r in reports.values()):
                        self._set_meta(conn, "last_auto_at", time.time())
                        self._last_auto_monotonic = time.monotonic()
                    return {
                        "evaluated": any(r.get("evaluated", False) for r in reports.values()),
                        "domains": reports,
                        "policy_speed_improvement_measured": False,
                    }
        except TeeError:
            raise
        except Exception as exc:
            self._health = "evaluation_error"
            raise _error() from exc

    def _evaluate_domain(self, conn: sqlite3.Connection, domain: str) -> dict:
        from tee.learning import model

        state = self._state(conn, domain)
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT e.*,g.first_seq AS group_first_seq,g.last_seq AS group_last_seq "
                "FROM events e JOIN groups g ON e.domain=g.domain AND e.group_id=g.group_id "
                "WHERE e.domain=? ORDER BY seq",
                (domain,),
            )
        ]
        for row in rows:
            if row["success"] is not None:
                row["success"] = bool(row["success"])
        train, heldout = self._split(rows, state.get("last_evaluated_seq", 0))
        train = self._training_window(train)
        if len(train) < MIN_TRAIN or len(heldout) < MIN_HOLDOUT:
            return {
                "evaluated": False,
                "reason": "insufficient_future_groups",
                "train": len(train),
                "holdout": len(heldout),
            }
        candidate = model.fit(train)
        encoded = json.dumps(candidate, separators=(",", ":"), allow_nan=False)
        if len(encoded.encode()) > MAX_MODEL_BYTES:
            raise ValueError("model_too_large")
        proposed = model.evaluate(candidate, heldout)
        baseline = model.baseline(train, heldout)
        incumbent = self._snapshot(conn, state.get("active_id"))
        incumbent_metrics = model.evaluate(incumbent["model"], heldout) if incumbent else None
        scores = [proposed, baseline] + ([incumbent_metrics] if incumbent_metrics else [])
        if any(not math.isfinite(float(m[k])) for m in scores for k in ("brier", "cost_log_mae")):
            raise ValueError("invalid_metrics")
        reasons = []
        if not all(model.covered(candidate, row, MIN_SUPPORT) for row in heldout):
            reasons.append("insufficient_coverage")
        if baseline["brier"] - proposed["brier"] < 0.01:
            reasons.append("no_reliability_gain")
        if proposed["cost_log_mae"] > baseline["cost_log_mae"] + 1e-6:
            reasons.append("cost_regression")
        if incumbent_metrics and (
            proposed["brier"] > incumbent_metrics["brier"] + 1e-9
            or proposed["cost_log_mae"] > incumbent_metrics["cost_log_mae"] + 1e-6
        ):
            reasons.append("incumbent_regression")
        if not self.auto_promote:
            reasons.append("auto_promote_disabled")
        if self._meta(conn, "promotion_paused", False):
            reasons.append("promotion_paused")
        promoted = not reasons
        high = rows[-1]["seq"]
        report = {
            "evaluated": True,
            "promoted": promoted,
            "reasons": reasons,
            "train": len(train),
            "holdout": len(heldout),
            "train_through_seq": train[-1]["seq"],
            "holdout_from_seq": heldout[0]["seq"],
            "holdout_through_seq": heldout[-1]["seq"],
            "candidate": proposed,
            "baseline": baseline,
            "incumbent": incumbent_metrics,
        }
        if promoted:
            mean = sum(r["success"] for r in train) / len(train)
            cursor = conn.execute(
                "INSERT INTO snapshots(domain,model_json,through_seq,evaluated_seq,"
                "fixed_baseline,created_ms) "
                "VALUES (?,?,?,?,?,?)",
                (domain, encoded, train[-1]["seq"], high, mean, int(time.time() * 1000)),
            )
            new_id = cursor.lastrowid
            conn.execute(
                "UPDATE domains SET previous_id=active_id,active_id=?,active_since=? "
                "WHERE domain=?",
                (new_id, high, domain),
            )
            report["snapshot_id"] = new_id
        conn.execute(
            "UPDATE domains SET last_evaluated_seq=?,evaluation_json=?,"
            "last_auto_count=trainable_count WHERE domain=?",
            (high, json.dumps(report, allow_nan=False), domain),
        )
        return report

    @staticmethod
    def _prune_snapshots(conn: sqlite3.Connection) -> None:
        protected = {
            r[0]
            for r in conn.execute(
                "SELECT active_id FROM domains UNION SELECT previous_id FROM domains"
            )
            if r[0] is not None
        }
        ids = [r[0] for r in conn.execute("SELECT id FROM snapshots ORDER BY id DESC")]
        keep = (
            protected | set(i for i in ids if i not in protected)
            if len(ids) <= MAX_SNAPSHOTS
            else protected
        )
        for snapshot_id in ids:
            if len(keep) >= MAX_SNAPSHOTS:
                break
            keep.add(snapshot_id)
        for snapshot_id in ids:
            if snapshot_id not in keep:
                conn.execute("DELETE FROM snapshots WHERE id=?", (snapshot_id,))

    def recent(self, limit: int = 10) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 50:
            raise _error("learning_argument")
        try:
            with self._lock, self._reader() as conn:
                if conn is None:
                    return []
                rows = conn.execute(
                    "SELECT event_id,domain,context,choice,version,success,elapsed_ms,tokens,"
                    "group_id,category,source,feedback_of,prediction,created_ms "
                    "FROM events ORDER BY seq DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                return [
                    dict(row)
                    | {"success": None if row["success"] is None else bool(row["success"])}
                    for row in rows
                ]
        except Exception as exc:
            self._health = "storage_error"
            raise _error() from exc

    def feedback(self, event_id: str, success: bool) -> dict:
        try:
            _identifier(event_id)
            if type(success) is not bool:
                raise ValueError("invalid_label")
            if not self.enabled:
                raise _error("learning_disabled")
            with self._lock:
                with self._transaction() as conn:
                    if self._meta(conn, "paused", False):
                        raise _error("learning_paused")
                    original = conn.execute(
                        "SELECT * FROM events WHERE event_id=?", (event_id,)
                    ).fetchone()
                    if original is None or original["domain"] == "reported":
                        raise _error("learning_event")
                    if conn.execute(
                        "SELECT 1 FROM events WHERE feedback_of=?", (event_id,)
                    ).fetchone():
                        raise _error("learning_duplicate_feedback")
                    row = self._validate(
                        "reported",
                        original["context"],
                        original["choice"],
                        original["version"],
                        success,
                        original["elapsed_ms"],
                        original["tokens"],
                        original["group_id"],
                        "feedback",
                    )
                    attached, due = self._insert(conn, row, event_id)
                if due:
                    self._evaluate_safely()
                return {
                    "event_id": attached,
                    "feedback_of": event_id,
                    "domain": "reported",
                    "success": success,
                }
        except TeeError:
            raise
        except Exception as exc:
            self._health = "feedback_error"
            raise _error("learning_argument") from exc

    def recommend(self, domain: str, context: str, candidates: list[dict]) -> dict:
        try:
            if (
                domain not in DOMAINS
                or not isinstance(candidates, list)
                or not 1 <= len(candidates) <= 32
            ):
                raise ValueError("invalid_candidates")
            _identifier(context)
            items = [
                {"choice": _identifier(c["choice"]), "version": _identifier(c["version"])}
                for c in candidates
            ]
            if any(set(c) != {"choice", "version"} for c in candidates) or len(
                {(c["choice"], c["version"]) for c in items}
            ) != len(items):
                raise ValueError("invalid_candidates")
        except Exception as exc:
            raise _error("learning_argument") from exc
        fallback = {"applied": False, "items": items}
        if not self.enabled:
            return {**fallback, "reason": "disabled"}
        if self._closed:
            return {**fallback, "reason": "closed"}
        if self._health != "ok":
            return {**fallback, "reason": "unhealthy"}
        try:
            from tee.learning import model

            with self._lock, self._reader() as conn:
                if conn is None:
                    return {**fallback, "reason": "untrained"}
                if self._meta(conn, "paused", False):
                    return {**fallback, "reason": "paused"}
                snapshot = self._snapshot(conn, self._state(conn, domain).get("active_id"))
                if not snapshot:
                    return {**fallback, "reason": "untrained"}
                now = int(time.time() * 1000)
                if not 0 <= now - snapshot["created_ms"] <= MAX_AGE_MS:
                    return {**fallback, "reason": "stale_or_missing_evidence"}
                for item in items:
                    latest = conn.execute(
                        "SELECT MAX(created_ms) FROM events WHERE domain=? AND context=? "
                        "AND choice=? AND version=? AND success IS NOT NULL",
                        (domain, context, item["choice"], item["version"]),
                    ).fetchone()[0]
                    if latest is None or not 0 <= now - latest <= MAX_AGE_MS:
                        return {**fallback, "reason": "stale_or_missing_evidence"}
                features = [{"domain": domain, "context": context, **item} for item in items]
                if not all(model.covered(snapshot["model"], row, MIN_SUPPORT) for row in features):
                    return {**fallback, "reason": "uncovered_candidate"}
                predictions = [model.predict(snapshot["model"], row) for row in features]
                ranked = []
                for item, prediction in zip(items, predictions, strict=True):
                    p, cost = (
                        float(prediction["success_probability"]),
                        float(prediction["elapsed_ms"]),
                    )
                    if (
                        not math.isfinite(p)
                        or not 0 <= p <= 1
                        or not math.isfinite(cost)
                        or cost < 0
                    ):
                        raise ValueError("model_invalid")
                    ranked.append({**item, "success_probability": p, "elapsed_ms": cost})
                ranked.sort(key=lambda item: (-item["success_probability"], item["elapsed_ms"]))
                return {
                    "applied": True,
                    "items": ranked,
                    "snapshot_id": snapshot["id"],
                    "basis": "predicted_reliability_then_cost",
                    "policy_speed_improvement_measured": False,
                }
        except Exception:
            self._health = "model_error"
            return {**fallback, "reason": "model_unavailable"}

    def control(self, action: str) -> dict:
        if not isinstance(action, str) or action not in {"pause", "resume", "rollback"}:
            raise _error("learning_argument")
        if not self.enabled:
            raise _error("learning_disabled")
        try:
            with self._lock, self._transaction() as conn:
                self._set_meta(conn, "paused", action != "resume")
                if action in {"resume", "rollback"}:
                    self._set_meta(conn, "promotion_paused", action != "resume")
                if action == "rollback":
                    high = conn.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
                    for domain in DOMAINS:
                        previous = self._snapshot(
                            conn, self._state(conn, domain).get("previous_id")
                        )
                        conn.execute(
                            "UPDATE domains SET active_id=?,previous_id=NULL,active_since=? "
                            "WHERE domain=?",
                            (previous["id"] if previous else None, high, domain),
                        )
            return {"action": action, **self.status()}
        except TeeError:
            raise
        except Exception as exc:
            self._health = "control_error"
            raise _error() from exc

    def status(self) -> dict:
        base = {
            "enabled": self.enabled,
            "auto_promote": self.auto_promote,
            "health": self._health,
            "event_limit": MAX_EVENTS,
            "snapshot_limit": MAX_SNAPSHOTS,
        }
        try:
            with self._lock, self._reader() as conn:
                if conn is None:
                    return {
                        **base,
                        "paused": False,
                        "promotion_paused": False,
                        "events": 0,
                        "snapshots": 0,
                        "domains": {},
                    }
                domains = {}
                for row in conn.execute("SELECT * FROM domains ORDER BY domain"):
                    value = dict(row)
                    domain = value.pop("domain")
                    for key in ("evaluation_json", "drift_json"):
                        raw = value.pop(key)
                        value[key.removesuffix("_json")] = json.loads(raw) if raw else None
                    snapshot = self._snapshot(conn, value.get("active_id"))
                    if snapshot:
                        from tee.learning import model

                        model.covered(
                            snapshot["model"],
                            {
                                "domain": domain,
                                "context": "health",
                                "choice": "health",
                                "version": "health",
                            },
                            MIN_SUPPORT,
                        )
                    domains[domain] = value
                if self._health != "invalid_config":
                    self._health = "ok"
                    base["health"] = "ok"
                return {
                    **base,
                    "paused": self._meta(conn, "paused", False),
                    "promotion_paused": self._meta(conn, "promotion_paused", False),
                    "events": conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                    "snapshots": conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0],
                    "domains": domains,
                }
        except Exception as exc:
            self._health = "storage_error"
            raise _error() from exc

    def close(self) -> None:
        """Release the per-app connection and refuse late background observations."""
        with self._lock:
            self._closed = True
            if self._connection is not None:
                self._connection.close()
                self._connection = None
