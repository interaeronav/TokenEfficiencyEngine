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


def test_over_budget_without_lists_hard_truncates():
    payload = {"ok": True, "blob": "z" * 100_000}
    out = enforce_budget(payload, max_tokens=500)
    assert "preview" in out
    assert estimate_tokens(out) <= 600  # preview + notice fit near the cap


def test_response_log_alerts_on_fat_medians():
    log = ResponseLog(alert_tokens=100)
    for _ in range(3):
        log.record("fat_tool", {"blob": "x" * 3_000})
        log.record("thin_tool", {"ok": True})
    report = log.report()
    assert "alert" in report["fat_tool"]
    assert "alert" not in report["thin_tool"]
    assert report["fat_tool"]["calls"] == 3
