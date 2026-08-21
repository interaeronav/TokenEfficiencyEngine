from tee.kernel.budget import ResponseLog, enforce_budget, estimate_tokens


def test_estimate_tokens_scales_with_size():
    small = estimate_tokens({"a": 1})
    large = estimate_tokens({"a": "x" * 10_000})
    assert small < 10
    assert large > 2_000


def test_within_budget_payload_unchanged():
    payload = {"ok": True, "items": [1, 2, 3]}
    assert enforce_budget(payload, max_tokens=1_000) == payload


def test_over_budget_trims_largest_list_and_names_the_narrowing():
    payload = {"ok": True, "items": [{"x": "y" * 50} for _ in range(500)]}
    out = enforce_budget(payload, max_tokens=1_000, narrow_hint="use limit=")
    assert len(out["items"]) < 500
    assert "use limit=" in out["truncated"]
    assert estimate_tokens(out) <= 1_000


def test_over_budget_without_collections_returns_parseable_skeleton():
    payload = {"ok": True, "checkpoint": "cp7", "revision": 12, "blob": "z" * 100_000}
    out = enforce_budget(payload, max_tokens=500)
    # scalars survive (checkpoint ids and stamps must never be lost)
    assert out["ok"] is True
    assert out["checkpoint"] == "cp7"
    assert out["revision"] == 12
    assert len(out["blob"]) < 1_000  # long strings clipped
    assert "truncated" in out
    assert estimate_tokens(out) <= 600


def test_over_budget_dict_fields_are_trimmed():
    payload = {
        "ok": True,
        "checkpoint": "cp1",
        "details": {f"e{i}": {"x": "y" * 60} for i in range(600)},
    }
    out = enforce_budget(payload, max_tokens=1_000, narrow_hint="fetch via tee_entity_detail")
    assert estimate_tokens(out) <= 1_000
    assert out["checkpoint"] == "cp1"
    assert 0 < len(out["details"]) < 600
    assert "details" in out["truncated"]
    assert "tee_entity_detail" in out["truncated"]


def test_truncation_notice_reports_every_trimmed_field():
    payload = {
        "ok": True,
        "alpha": [{"x": "y" * 50} for _ in range(400)],
        "beta": [{"x": "y" * 50} for _ in range(300)],
    }
    out = enforce_budget(payload, max_tokens=800)
    dropped_alpha = 400 - len(out["alpha"])
    dropped_beta = 300 - len(out["beta"])
    if dropped_alpha:
        assert f"{dropped_alpha} from 'alpha'" in out["truncated"]
    if dropped_beta:
        assert f"{dropped_beta} from 'beta'" in out["truncated"]
    assert estimate_tokens(out) <= 800


def test_response_log_alerts_on_fat_medians():
    log = ResponseLog(alert_tokens=100)
    for _ in range(3):
        log.record("fat_tool", {"blob": "x" * 3_000})
        log.record("thin_tool", {"ok": True})
    report = log.report()
    assert "alert" in report["fat_tool"]
    assert "alert" not in report["thin_tool"]
    assert report["fat_tool"]["calls"] == 3
