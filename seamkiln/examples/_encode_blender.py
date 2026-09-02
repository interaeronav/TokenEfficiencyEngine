"""Frames -> mp4 through Blender's own FFMPEG. Runs INSIDE Blender.

    blender --background --factory-startup --python _encode_blender.py -- \
        FRAMES_DIR OUT.mp4 FPS AUDIO.wav|- WIDTH HEIGHT
"""

import sys
from pathlib import Path

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1 :]
FRAMES, OUT, FPS = Path(ARGS[0]), Path(ARGS[1]), int(ARGS[2])
AUDIO = Path(ARGS[3]) if len(ARGS) > 3 and ARGS[3] != "-" else None
RES = (int(ARGS[4]), int(ARGS[5])) if len(ARGS) > 5 else (1920, 1080)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
files = sorted(FRAMES.glob("*.png"))
if not files:
    raise SystemExit(f"no frames in {FRAMES}")

scene.sequence_editor_create()
# Blender 5.x renamed sequence_editor.sequences to .strips. Presence is tested
# with `is None`, not truthiness: an EMPTY strip collection is falsy, and `or`
# reached for a name this build does not have after the render had already
# cost nine minutes.
book = getattr(scene.sequence_editor, "strips", None)
if book is None:
    book = scene.sequence_editor.sequences
strip = book.new_image(name="shot", filepath=str(files[0]), channel=1, frame_start=1)
for f in files[1:]:
    strip.elements.append(f.name)

if AUDIO is not None and AUDIO.exists():
    book.new_sound(name="track", filepath=str(AUDIO), channel=2, frame_start=1)
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.ffmpeg.audio_bitrate = 192
    scene.render.ffmpeg.audio_mixrate = 48000

scene.frame_start, scene.frame_end = 1, len(files)
scene.render.fps = FPS
scene.render.resolution_x, scene.render.resolution_y = RES
# Blender 5.x splits IMAGE from VIDEO output; FFMPEG only appears in the
# file_format enum once media_type is VIDEO. The capability check that said
# FFMPEG was available queried the CLASS RNA, which is unfiltered - the only
# honest check is against the object you are actually going to set.
if hasattr(scene.render.image_settings, "media_type"):
    scene.render.image_settings.media_type = "VIDEO"
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.ffmpeg.ffmpeg_preset = "GOOD"
scene.render.ffmpeg.gopsize = 12
# The stills are already display-referred sRGB, so the encode must NOT put a
# second view transform on top of them.
scene.view_settings.view_transform = "Standard"
OUT.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(OUT.with_suffix(""))
bpy.ops.render.render(animation=True)
print("ENCODED", len(files), "frames ->", OUT)
