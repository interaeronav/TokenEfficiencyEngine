"""Media arms for the web lane (A34 W4, research 49).

Images: only when the question needs them AND a local VLM answers - top-N
page images captioned server-side; otherwise a structured unavailable
note (never silent). Audio/video FILES: size-gated through the
cost-confirm idiom (media='confirm' accepts the big download), then the
extract lane's whisper transcription, budget-cut against the question.

Anti-goals enforced here and by test: streaming platforms are refused
before any fetch (ToS - direct files and owner-provided media only), and
paywalls are never bypassed (a 402/403 answers as the error it is).
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from tee.kernel import local_vlm
from tee.kernel.errors import TeeError

AV_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".mov", ".webm", ".mkv")
AV_FREE_BYTES = 10_000_000  # under this, transcribe without asking
AV_MAX_BYTES = 100_000_000  # over this, refuse even confirmed
IMAGE_CAP_BYTES = 5_000_000
TOP_N_IMAGES = 2

STREAMING_HOSTS = (
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "twitch.tv",
    "tiktok.com",
    "spotify.com",
    "soundcloud.com",
    "netflix.com",
    "dailymotion.com",
)

_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_ATTR = re.compile(r"""(\w+)\s*=\s*("([^"]*)"|'([^']*)'|([^\s>]+))""")
_WANTS_IMAGE = re.compile(
    r"\b(image|images|picture|photo|diagram|screenshot|logo|icon|figure|"
    r"chart|graph|drawing|texture|look|looks|color|colour|visual|appearance|shown?)\b",
    re.IGNORECASE,
)


def is_streaming_host(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in STREAMING_HOSTS)


def refuse_streaming(url: str) -> None:
    if is_streaming_host(url):
        raise TeeError(
            "web_streaming_blocked",
            "Streaming platforms are not fetchable (their ToS forbid ripping).",
            fix="Use a direct media file URL or owner-provided media through the extract lane.",
        )


def looks_av(url: str) -> bool:
    path = (urlsplit(url).path or "").lower()
    return path.endswith(AV_EXTENSIONS)


def question_wants_image(question: str) -> bool:
    return bool(_WANTS_IMAGE.search(question))


def collect_images(html: str, base_url: str) -> list[dict[str, str]]:
    """Visible <img> candidates as [{url, alt}], absolute http(s) only."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for tag in _IMG_TAG.findall(html[:400_000]):
        attrs = {
            m.group(1).lower(): (m.group(3) or m.group(4) or m.group(5) or "")
            for m in _ATTR.finditer(tag)
        }
        src = attrs.get("src", "")
        if not src or src.startswith("data:"):
            continue
        absolute = urljoin(base_url, src)
        if not absolute.startswith(("http://", "https://")) or absolute in seen:
            continue
        if absolute.lower().split("?")[0].endswith((".svg", ".ico")):
            continue  # not raster food for a VLM
        seen.add(absolute)
        out.append({"url": absolute, "alt": " ".join(attrs.get("alt", "").split())[:200]})
        if len(out) >= 20:
            break
    return out


def rank_images(images: list[dict[str, str]], question: str) -> list[dict[str, str]]:
    words = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if len(w) > 2}

    def score(image: dict[str, str]) -> int:
        alt_words = set(re.findall(r"[a-z0-9]+", image["alt"].lower()))
        return len(words & alt_words)

    return sorted(images, key=score, reverse=True)


def caption_images(
    fetch_bytes,
    images: list[dict[str, str]],
    question: str,
    *,
    top_n: int = TOP_N_IMAGES,
    describe=None,
) -> list[dict[str, str]]:
    """Fetch + caption the top-N images through the guarded fetcher; a
    per-image failure is reported in place, never silently dropped."""
    describe = describe or local_vlm.describe
    captions: list[dict[str, str]] = []
    for image in images[:top_n]:
        try:
            data = fetch_bytes(image["url"], IMAGE_CAP_BYTES)
            media_type = "image/png" if image["url"].lower().endswith(".png") else "image/jpeg"
            answer = describe(data, question, media_type=media_type, max_tokens=120)
            captions.append({"url": image["url"], "caption": answer})
        except TeeError as exc:
            captions.append({"url": image["url"], "error": exc.code})
    return captions


def transcribe_bytes(data: bytes, url: str) -> list[dict]:
    """Body bytes -> transcript facts via the extract lane's whisper path.
    Loud, exact-fix refusal when the [extract] extra is missing."""
    try:
        from tee.extract.audio import extract_audio
    except ImportError as exc:
        raise TeeError(
            "web_media_unavailable",
            "Transcription needs the [extract] extra (faster-whisper).",
            fix="pip install 'tee-engine[extract]' - or ingest the file "
            "through a machine that has it.",
        ) from exc
    suffix = Path(urlsplit(url).path).suffix or ".mp3"
    with tempfile.TemporaryDirectory(prefix="tee-web-av-") as tmp:
        source = Path(tmp) / f"media{suffix}"
        source.write_bytes(data)
        facts = extract_audio(source, Path(tmp))
    notes = [f for f in facts if f.get("kind") == "note"]
    segments = [f for f in facts if f.get("kind") == "transcript_segment"]
    if not segments:
        detail = notes[0]["note"] if notes else "no speech found"
        raise TeeError(
            "web_media_unavailable",
            f"Transcription produced no text ({detail[:160]}).",
            fix="Check the file has speech; the whisper install must be intact.",
        )
    return facts
