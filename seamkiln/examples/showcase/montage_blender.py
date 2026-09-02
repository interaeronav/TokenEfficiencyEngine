"""Cards and clips -> one mp4 with the clips' own soundtracks. Runs INSIDE Blender.

blender --background --factory-startup --python montage_blender.py -- PLAN.json OUT.mp4 W H
"""

import json
import sys
from pathlib import Path

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1 :]
PLAN = json.loads(Path(ARGS[0]).read_text())
OUT = Path(ARGS[1])
RES = (int(ARGS[2]), int(ARGS[3])) if len(ARGS) > 3 else (1920, 1080)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.sequence_editor_create()
book = getattr(scene.sequence_editor, "strips", None)
if book is None:
    book = scene.sequence_editor.sequences

fps = int(PLAN["fps"])
cursor = 1
channel = 1
for k, item in enumerate(PLAN["plan"]):
    if item["kind"] == "card":
        strip = book.new_image(
            name=f"card{k}", filepath=item["image"], channel=channel, frame_start=cursor
        )
        strip.frame_final_duration = int(item["frames"])
        length = int(item["frames"])
    else:
        files = sorted(Path(item["frames"]).glob("*.png"))
        if not files:
            raise SystemExit(f"no frames in {item['frames']}")
        strip = book.new_image(
            name=f"clip{k}", filepath=str(files[0]), channel=channel, frame_start=cursor
        )
        for f in files[1:]:
            strip.elements.append(f.name)
        length = len(files)
        audio = Path(item.get("audio", ""))
        if audio.exists():
            book.new_sound(name=f"sound{k}", filepath=str(audio), channel=3, frame_start=cursor)
    # a short fade in and out on every strip, so the cuts breathe
    fade = min(int(fps * 0.35), max(length // 4, 1))
    strip.blend_type = "ALPHA_OVER"
    strip.blend_alpha = 0.0
    strip.keyframe_insert("blend_alpha", frame=cursor)
    strip.blend_alpha = 1.0
    strip.keyframe_insert("blend_alpha", frame=cursor + fade)
    strip.keyframe_insert("blend_alpha", frame=cursor + length - fade - 1)
    strip.blend_alpha = 0.0
    strip.keyframe_insert("blend_alpha", frame=cursor + length - 1)
    cursor += length

scene.frame_start, scene.frame_end = 1, cursor - 1
scene.render.fps = fps
scene.render.resolution_x, scene.render.resolution_y = RES
if hasattr(scene.render.image_settings, "media_type"):
    scene.render.image_settings.media_type = "VIDEO"
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.ffmpeg.ffmpeg_preset = "GOOD"
scene.render.ffmpeg.gopsize = 12
scene.render.ffmpeg.audio_codec = "AAC"
scene.render.ffmpeg.audio_bitrate = 192
scene.render.ffmpeg.audio_mixrate = 48000
scene.view_settings.view_transform = "Standard"
OUT.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(OUT.with_suffix(""))
bpy.ops.render.render(animation=True)
print("MONTAGE", cursor - 1, "frames ->", OUT, flush=True)
