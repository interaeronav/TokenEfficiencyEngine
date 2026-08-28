"""SSRF validator spec for the web lane (A34 W0) - written before the fetcher.

Contract (research 49, mitigation 2): http/https only, no userinfo, ports
80/443 unless opted in, resolve-then-pin with every resolved address checked
against loopback / private / link-local / ULA / multicast / unspecified,
and rule-6 refusals that name the exact fix. No test here touches the
network: hostname resolution goes through an injectable resolver; IP
literals (including decimal/hex/short forms) resolve locally by definition.
"""

from __future__ import annotations

import pytest

from tee.kernel.errors import TeeError
from tee.web import guard


def _blocked(url: str, **kwargs) -> TeeError:
    with pytest.raises(TeeError) as excinfo:
        guard.validate_url(url, **kwargs)
    return excinfo.value


# --- scheme / shape ---------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/file",
        "file:///etc/passwd",
        "gopher://example.com/",
        "ws://example.com/",
        "javascript:alert(1)",
    ],
)
def test_non_http_schemes_refused(url: str) -> None:
    err = _blocked(url)
    assert err.code == "web_scheme_blocked"
    assert "http" in (err.fix or "")


def test_userinfo_refused() -> None:
    err = _blocked("http://user:pass@example.com/")
    assert err.code == "web_userinfo_blocked"
    assert err.fix


def test_missing_host_refused() -> None:
    assert _blocked("http:///nohost").code == "web_url_invalid"


def test_nonstandard_port_refused_with_config_fix() -> None:
    err = _blocked("http://93.184.216.34:8080/")
    assert err.code == "web_port_blocked"
    assert "[web]" in (err.fix or "")


def test_opted_in_port_allowed() -> None:
    target = guard.validate_url("http://93.184.216.34:8080/", ports=(80, 443, 8080))
    assert target.port == 8080


# --- IP-literal matrix (resolves locally, no DNS) ---------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://127.1/",  # short form of 127.0.0.1
        "http://2130706433/",  # decimal-encoded 127.0.0.1
        "http://0x7f000001/",  # hex-encoded 127.0.0.1
        "http://0.0.0.0/",
        "http://10.0.0.5/",
        "http://172.16.0.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://224.0.0.1/",  # multicast
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[fc00::1]/",
        "http://[::ffff:127.0.0.1]/",  # v4-mapped loopback
    ],
)
def test_private_and_special_addresses_refused(url: str) -> None:
    err = _blocked(url)
    assert err.code == "web_private_blocked"
    assert "allow_local" in (err.fix or "")


def test_allow_local_admits_loopback() -> None:
    target = guard.validate_url("http://127.0.0.1:8080/", allow_local=True, ports=(80, 443, 8080))
    assert target.ip == "127.0.0.1"


# --- hostname resolution: resolve-then-pin ----------------------------------


def test_hostname_pins_resolved_public_ip() -> None:
    target = guard.validate_url(
        "https://example.com/x", resolve=lambda host, port: ["93.184.216.34"]
    )
    assert (target.scheme, target.host, target.port) == ("https", "example.com", 443)
    assert target.ip == "93.184.216.34"
    assert target.url == "https://example.com/x"


def test_hostname_resolving_private_refused() -> None:
    err = _blocked("http://internal.corp/", resolve=lambda host, port: ["10.1.2.3"])
    assert err.code == "web_private_blocked"


def test_mixed_public_private_resolution_refused() -> None:
    # DNS answers that mix a public and a private address are a classic
    # rebinding/split-horizon smell: refuse the lot.
    err = _blocked(
        "http://evil.example/", resolve=lambda host, port: ["93.184.216.34", "127.0.0.1"]
    )
    assert err.code == "web_private_blocked"


def test_resolution_failure_is_one_cheap_error() -> None:
    def resolve(host: str, port: int) -> list[str]:
        raise OSError("no such host")

    err = _blocked("http://nxdomain.example/", resolve=resolve)
    assert err.code == "web_dns_failed"
    assert err.fix


def test_every_refusal_names_a_fix() -> None:
    cases = [
        ("ftp://a/", {}),
        ("http://u:p@a/", {}),
        ("http://93.184.216.34:8080/", {}),
        ("http://127.0.0.1/", {}),
        ("http://x/", {"resolve": lambda host, port: ["192.168.0.9"]}),
    ]
    for url, kwargs in cases:
        err = _blocked(url, **kwargs)
        assert err.fix, f"refusal for {url} carries no fix"
