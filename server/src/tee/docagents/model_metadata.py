"""Explicit, dated worker metadata; aliases never imply provider capacity or cost."""

from __future__ import annotations

import math
from datetime import date
from typing import Any
from urllib.parse import urlsplit

from tee.kernel.errors import TeeError


def _fail(message: str) -> None:
    raise TeeError(
        "docagent_model_metadata",
        message,
        fix="Review docagent_metadata against the selected route and provider source.",
    )


def _https(value: Any) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 2048:
        return False
    try:
        url = urlsplit(value)
        return (
            url.scheme == "https" and bool(url.hostname) and not url.username and not url.password
        )
    except ValueError:
        return False


def aider_metadata(profile: dict[str, Any], *, today: date | None = None) -> dict | None:
    """Validate owner-configured facts without fetching URLs or changing a route."""
    value = profile.get("docagent_metadata")
    if value is None:
        return None  # Ordinary Aider unknown-model diagnostics remain enabled.
    required = {
        "schema",
        "model",
        "url",
        "upstream_model",
        "upstream_url",
        "verified_on",
        "valid_until",
        "capacity_source",
        "price_source",
        "currency",
        "max_input_tokens",
        "max_output_tokens",
        "context_window",
        "price_in_per_mtok",
        "price_out_per_mtok",
        "request_output_tokens",
    }
    if (
        not isinstance(value, dict)
        or set(value) != required
        or type(value.get("schema")) is not int
        or value["schema"] != 1
    ):
        _fail(
            "Provide the complete docagent_metadata schema 1 contract; unknown fields are refused."
        )
    if value["model"] != profile.get("model") or value["url"] != profile.get("url"):
        _fail("Model metadata belongs to a different model or endpoint.")
    if not isinstance(value["upstream_model"], str) or not 1 <= len(value["upstream_model"]) <= 256:
        _fail("Name the actual upstream model behind the alias.")
    if not all(_https(value[name]) for name in ("upstream_url", "capacity_source", "price_source")):
        _fail(
            "Supply HTTPS provenance URLs without credentials; they are recorded, never fetched."
        )
    try:
        checked = date.fromisoformat(value["verified_on"])
        expires = date.fromisoformat(value["valid_until"])
    except (TypeError, ValueError):
        _fail("Metadata needs verified_on and valid_until ISO dates.")
    current = today or date.today()
    if not checked <= current <= expires or not 0 <= (expires - checked).days <= 30:
        _fail("Model metadata is stale, future-dated or valid for more than 30 days.")
    for name in (
        "max_input_tokens",
        "max_output_tokens",
        "context_window",
        "request_output_tokens",
    ):
        if type(value[name]) is not int or not 1 <= value[name] <= 10_000_000:
            _fail("Model capacities and request output budget must be positive bounded integers.")
    if max(value["max_input_tokens"], value["max_output_tokens"]) > value["context_window"]:
        _fail("Individual model limits cannot exceed the documented context window.")
    if not 128 <= value["request_output_tokens"] <= min(8192, value["max_output_tokens"]):
        _fail(
            "Documentation output budget must be 128-8192 tokens within the provider output limit."
        )
    if value["currency"] != "USD":
        _fail(
            "Aider displays USD; supply verified USD rates instead of relabelling another currency."
        )
    for name in ("price_in_per_mtok", "price_out_per_mtok"):
        rate = value[name]
        if type(rate) not in (int, float) or not math.isfinite(rate) or not 0 <= rate <= 1_000_000:
            _fail("Token prices must be explicit finite nonnegative USD rates per million tokens.")
        if profile.get("paid") and rate == 0:
            _fail("Zero proxy defaults are not an acceptable paid-model price.")
    return {
        "info": {
            "max_tokens": value["max_output_tokens"],
            "max_input_tokens": value["max_input_tokens"],
            "max_output_tokens": value["max_output_tokens"],
            "input_cost_per_token": value["price_in_per_mtok"] / 1_000_000,
            "output_cost_per_token": value["price_out_per_mtok"] / 1_000_000,
            "litellm_provider": "openai",  # The unchanged wire route is OpenAI-compatible.
            "mode": "chat",
        },
        "settings": {
            "edit_format": "diff",
            "extra_params": {"max_tokens": value["request_output_tokens"]},
        },
        "provenance": {
            **value,
            "price_basis": (
                "published uncached list rates; excludes discounts, credits and invoice adjustments"
            ),
        },
    }
