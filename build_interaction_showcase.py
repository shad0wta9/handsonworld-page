#!/usr/bin/env python3
"""Build the six independent interaction videos used on the project page."""

from pathlib import Path
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "static" / "videos" / "interactions"
OBJECT_GEN = ROOT / "paper_frames" / "demo_finetune2_epoch4_new_8_14_cfg1_1.5"
CHAR_GEN = ROOT / "paper_frames" / "demo_finetune3_epoch4_all14_cfg1_1.5"
CHAR_POSE = ROOT / "paper_frames" / "demo_cfg1_1.5_with_hawor_renderer_pose_case2_rfix"
FPS = 24

OBJECT_CASES = [
    ("demo_8", "lift-cauldron", "Lift cauldron", "#D55E00", (240, 183, 155, 152)),
    ("demo_9", "lift-potion", "Lift potion", "#0072B2", (395, 109, 77, 139)),
    ("demo_11", "add-herbs", "Add herbs", "#009E73", (0, 317, 98, 108)),
    ("demo_12", "place-crystal", "Place crystal in", "#CC79A7", (197, 136, 51, 77)),
]


def font(size: int):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def generated(root: Path, demo: str, number: int):
    return Image.open(root / demo / "generated_frames" / f"{number:04d}.png").convert("RGB")


def marked_initial(demo: str, label: str, color: str, box):
    image = generated(OBJECT_GEN, demo, 1)
    draw = ImageDraw.Draw(image, "RGBA")
    x, y, width, height = box
    draw.rounded_rectangle(
        (x, y, x + width, y + height), 8,
        fill=color + "2e", outline=color, width=5,
    )
    label_font = font(26)
    bounds = draw.textbbox((0, 0), label, font=label_font)
    text_width = bounds[2] - bounds[0]
    draw.rounded_rectangle(
        (18, 404, 622, 464), 10, fill=(8, 12, 18, 215),
    )
    draw.text(((640 - text_width) / 2, 418), label, font=label_font, fill=color)
    return image


def character_frame(demo: str, number: int):
    image = generated(CHAR_GEN, demo, number)
    return add_pose(image, demo, number)


def add_pose(image: Image.Image, demo: str, number: int):
    image = image.copy()
    pose = Image.open(
        CHAR_POSE / demo / "pose_frames" / f"{number:04d}.png"
    ).convert("RGB").resize((192, 144), Image.Resampling.LANCZOS)
    image.paste(pose, (432, 321))
    ImageDraw.Draw(image).rectangle((432, 321, 623, 464), outline="white", width=3)
    return image


def pose_frame(demo: str, number: int):
    return Image.open(
        CHAR_POSE / demo / "pose_frames" / f"{number:04d}.png"
    ).convert("RGB")


def encode(path: Path, frames):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    width, height = frames[0].size
    command = [
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(FPS), "-i", "-", "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path),
    ]
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert process.stdin is not None
    for frame in frames:
        process.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError(f"Encoding failed: {path}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for demo, slug, label, color, box in OBJECT_CASES:
        intro = marked_initial(demo, label, color, box)
        frames = [intro] * FPS
        frames.extend(generated(OBJECT_GEN, demo, i) for i in range(1, 98))
        encode(OUT / f"{slug}.mp4", frames)
        intro.save(OUT / f"{slug}.jpg", quality=91)
        control_intro = pose_frame(demo, 1)
        control_frames = [control_intro] * FPS
        control_frames.extend(pose_frame(demo, i) for i in range(1, 98))
        encode(OUT / f"{slug}-control.mp4", control_frames)
        control_intro.save(OUT / f"{slug}-control.jpg", quality=91)

    for demo, slug in (("demo_13", "character-tea"), ("demo_14", "character-blocks")):
        frames = [generated(CHAR_GEN, demo, i) for i in range(1, 98)]
        encode(OUT / f"{slug}.mp4", frames)
        frames[0].save(OUT / f"{slug}.jpg", quality=91)
        control_frames = [pose_frame(demo, i) for i in range(1, 98)]
        encode(OUT / f"{slug}-control.mp4", control_frames)
        control_frames[0].save(OUT / f"{slug}-control.jpg", quality=91)


if __name__ == "__main__":
    main()
