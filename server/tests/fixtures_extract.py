"""Synthetic Phase 7 fixtures, generated in-repo (7.8) - no licensing risk.

A DXF plan with real DIMENSION entities, a vector-PDF plan, patterned "scene"
frames encoded to video, a DJI-format SRT, and an espeak-synthesized client
brief for the audio lane.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# The canonical fixture house: 8 m x 6 m outer shell + one interior wall.
HOUSE_W, HOUSE_D = 8.0, 6.0
WALL_MM = 200


def make_dxf(path: Path, *, unitless: bool = False) -> Path:
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 0 if unitless else 4  # 4 = mm
    msp = doc.modelspace()
    for layer in ("WALLS", "ROOMS", "DOORS"):
        doc.layers.add(layer)

    w, d = HOUSE_W * 1000, HOUSE_D * 1000
    outer = msp.add_lwpolyline(
        [(0, 0), (w, 0), (w, d), (0, d)], close=True, dxfattribs={"layer": "WALLS"}
    )
    outer.dxf.const_width = WALL_MM
    inner = msp.add_lwpolyline([(w / 2, 0), (w / 2, d)], dxfattribs={"layer": "WALLS"})
    inner.dxf.const_width = WALL_MM

    msp.add_lwpolyline(
        [(0, 0), (w / 2, 0), (w / 2, d), (0, d)], close=True, dxfattribs={"layer": "ROOMS"}
    )
    msp.add_lwpolyline(
        [(w / 2, 0), (w, 0), (w, d), (w / 2, d)], close=True, dxfattribs={"layer": "ROOMS"}
    )
    msp.add_text("Living Room", dxfattribs={"layer": "ROOMS", "insert": (2000, 3000)})
    msp.add_text("Bedroom 1", dxfattribs={"layer": "ROOMS", "insert": (6000, 3000)})
    msp.add_point((w / 2, d / 3), dxfattribs={"layer": "DOORS"})

    dim = msp.add_linear_dim(base=(0, -600), p1=(0, 0), p2=(w, 0))
    dim.render()
    dim2 = msp.add_linear_dim(base=(-600, 0), p1=(0, 0), p2=(0, d), angle=90)
    dim2.render()

    doc.saveas(str(path))
    return path


def make_pdf(path: Path) -> Path:
    """Vector plan sheet: two axis-aligned wall pairs + dimension strings.
    fpdf works in mm; 1 drawing mm = 0.1 m (a 1:100 plan)."""
    from fpdf import FPDF

    pdf = FPDF(orientation="landscape", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("helvetica", size=8)
    pdf.set_line_width(0.3)

    ox, oy = 40, 40
    w_mm, d_mm = HOUSE_W * 10, HOUSE_D * 10  # 80 x 60 on paper
    gap = 2.0  # 0.2 m wall thickness on paper

    def wall_pair_h(y: float) -> None:
        pdf.line(ox, y, ox + w_mm, y)
        pdf.line(ox, y + gap, ox + w_mm, y + gap)

    def wall_pair_v(x: float) -> None:
        pdf.line(x, oy, x, oy + d_mm)
        pdf.line(x + gap, oy, x + gap, oy + d_mm)

    wall_pair_h(oy)
    wall_pair_h(oy + d_mm)
    wall_pair_v(ox)
    wall_pair_v(ox + w_mm)

    # dimension lines with strings (the scale-fit anchors)
    pdf.line(ox, oy + d_mm + 12, ox + w_mm, oy + d_mm + 12)
    pdf.text(ox + w_mm / 2 - 4, oy + d_mm + 10, "8000")
    pdf.line(ox + w_mm + 12, oy, ox + w_mm + 12, oy + d_mm)
    pdf.text(ox + w_mm + 14, oy + d_mm / 2, "6000")

    pdf.text(ox + 2, oy - 4, "A-101  GROUND FLOOR PLAN")
    pdf.output(str(path))
    return path


def make_scene_frames(directory: Path, scenes: int = 3, per_scene: int = 10) -> Path:
    from PIL import Image, ImageDraw

    directory.mkdir(parents=True, exist_ok=True)
    index = 0
    for scene in range(scenes):
        for _ in range(per_scene):
            img = Image.new("RGB", (320, 240), (30 + scene * 20, 40, 60))
            draw = ImageDraw.Draw(img)
            if scene == 0:
                draw.ellipse((40, 40, 180, 180), fill=(220, 90, 60))
            elif scene == 1:
                for x in range(0, 320, 24):
                    draw.line((x, 0, x, 240), fill=(90, 220, 120), width=6)
            else:
                draw.rectangle((160, 30, 300, 210), fill=(90, 120, 230))
            index += 1
            img.save(directory / f"s{index:03d}.png")
    return directory


def make_video(path: Path, frames_dir: Path) -> Path:
    from tee.extract.video import ffmpeg_exe

    proc = subprocess.run(
        [
            ffmpeg_exe(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            "5",
            "-i",
            str(frames_dir / "s%03d.png"),
            "-pix_fmt",
            "yuv420p",
            "-y",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr
    return path


DJI_SRT = """1
00:00:00,000 --> 00:00:01,000
[latitude: -22.570000] [longitude: 17.083000] [rel_alt: 30.0 abs_alt: 1720.5]

2
00:00:01,000 --> 00:00:02,000
[latitude: -22.570100] [longitude: 17.083100] [rel_alt: 30.2 abs_alt: 1720.7]

3
00:00:02,000 --> 00:00:03,000
[latitude: -22.570200] [longitude: 17.083200] [rel_alt: 30.4 abs_alt: 1720.9]

4
00:00:03,000 --> 00:00:04,000
[latitude: -22.570200] [longitude: 17.083400] [rel_alt: 30.6 abs_alt: 1721.1]

5
00:00:04,000 --> 00:00:05,000
[latitude: -22.570200] [longitude: 17.083600] [rel_alt: 30.8 abs_alt: 1721.3]
"""

BRIEF_TEXT = (
    "The house should have four bedrooms. "
    "The master bedroom faces east. "
    "Keep the budget under two hundred thousand."
)


def make_audio(path: Path) -> Path | None:
    espeak = shutil.which("espeak-ng")
    if espeak is None:
        return None
    subprocess.run(
        [espeak, "-w", str(path), "-s", "140", BRIEF_TEXT],
        check=True,
        timeout=60,
    )
    return path
