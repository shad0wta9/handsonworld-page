#!/usr/bin/env python3
"""Rebuild the teaser control timeline from the original 720x540 pose frames."""

from pathlib import Path
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
POSE = ROOT / "paper_frames" / "demo_cfg1_1.5_with_hawor_renderer_pose_case2_rfix"
OUT = Path(__file__).resolve().parent / "static" / "videos" / "teaser-control-signal.mp4"
FPS, WIDTH, HEIGHT, FRAME_COUNT = 24, 720, 540, 2373

# Colored-inset runs measured from the synchronized 98.88 s teaser. Each run
# corresponds to one original pose sequence; all other frames are transitions.
RUNS = [
    (244, 440, 1),
    (565, 808, 2),
    (933, 1128, 3),
    (1253, 1448, 4),
    (1543, 1738, 5),
    (1863, 2058, 6),
    (2183, 2326, 7),
]


def font(size: int):
    for name in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
    ):
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default(size=size)


def no_control():
    image = Image.new("RGB", (WIDTH, HEIGHT), (137, 137, 137))
    draw = ImageDraw.Draw(image)
    draw.rectangle((5, 5, WIDTH - 6, HEIGHT - 6), outline="white", width=6)
    text = "No control"
    text_font = font(60)
    box = draw.textbbox((0, 0), text, font=text_font)
    draw.text(((WIDTH - (box[2] - box[0])) / 2,
               (HEIGHT - (box[3] - box[1])) / 2 - box[1]),
              text, font=text_font, fill="white")
    return image


def pose_frames(demo: int):
    folder = POSE / f"demo_{demo}" / "pose_frames"
    return [Image.open(path).convert("RGB") for path in sorted(folder.glob("*.png"))]


def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-", "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT),
    ]
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert process.stdin is not None
    placeholder = no_control()
    run_index = 0
    source = None
    for output_index in range(FRAME_COUNT):
        while run_index < len(RUNS) and output_index > RUNS[run_index][1]:
            run_index += 1
            source = None
        if run_index < len(RUNS) and RUNS[run_index][0] <= output_index <= RUNS[run_index][1]:
            start, end, demo = RUNS[run_index]
            if source is None:
                source = pose_frames(demo)
            position = (output_index - start) / (end - start) * (len(source) - 1)
            left = int(position)
            fraction = position - left
            frame = source[left]
            if fraction > 0 and left + 1 < len(source):
                frame = Image.blend(frame, source[left + 1], fraction)
        else:
            frame = placeholder
        process.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("Failed to encode teaser control signal")


if __name__ == "__main__":
    main()
