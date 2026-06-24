from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Union

import cv2
import numpy as np

PathLike = Union[str, Path]


def _as_bgr(frame: np.ndarray) -> np.ndarray:
    array = np.asarray(frame)
    if array.ndim == 2:
        return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
    if array.ndim == 3 and array.shape[2] == 3:
        return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
    if array.ndim == 3 and array.shape[2] == 4:
        return cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)
    raise ValueError(f"Unsupported frame shape for MP4 writing: {array.shape}")


def write_mp4(
    frames: list[np.ndarray],
    output_path: PathLike,
    fps: float,
    codec: str = "mp4v",
) -> None:
    if not frames:
        raise ValueError("Cannot write MP4 from an empty frame list")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    first_frame = _as_bgr(frames[0])
    if codec == "libx264":
        _write_mp4_with_ffmpeg(frames, output, fps, first_frame)
        return

    height, width = first_frame.shape[:2]
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*codec),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not initialize MP4 writer for: {output}")

    try:
        writer.write(first_frame)
        for frame in frames[1:]:
            writer.write(_as_bgr(frame))
    finally:
        writer.release()


def _write_mp4_with_ffmpeg(
    frames: list[np.ndarray], output_path: Path, fps: float, first_frame: np.ndarray
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required for libx264 MP4 writing.")

    height, width = first_frame.shape[:2]
    command = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(float(fps)),
        "-i",
        "-",
        "-c:v",
        "libx264",
        "-crf",
        "0",
        "-preset",
        "veryslow",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stdin is None:
        raise RuntimeError("Could not open ffmpeg stdin for MP4 writing.")

    try:
        process.stdin.write(first_frame.tobytes())
        for frame in frames[1:]:
            process.stdin.write(_as_bgr(frame).tobytes())
    finally:
        process.stdin.close()

    return_code = process.wait()
    if return_code != 0:
        stderr = ""
        if process.stderr is not None:
            stderr = process.stderr.read().decode(errors="replace").strip()
        raise RuntimeError(stderr or "ffmpeg libx264 MP4 writing failed.")


def embed_mp4_metadata(
    mp4_path: PathLike,
    metadata: dict[str, str],
    enabled: bool = True,
) -> dict[str, object]:
    tag_keys = sorted(metadata)
    if not enabled:
        return {"status": "disabled", "tag_keys": tag_keys, "warning": None}
    if not metadata:
        return {"status": "no_tags", "tag_keys": [], "warning": None}

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return {
            "status": "skipped",
            "tag_keys": tag_keys,
            "warning": "ffmpeg not found; MP4 metadata embedding skipped.",
        }

    source = Path(mp4_path)
    with NamedTemporaryFile(suffix=source.suffix, delete=False) as temporary:
        temporary_path = Path(temporary.name)

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-movflags",
        "+faststart+use_metadata_tags",
    ]
    for key, value in metadata.items():
        command.extend(["-metadata", f"{key}={value}"])
    command.extend(["-codec", "copy", str(temporary_path)])

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        temporary_path.unlink(missing_ok=True)
        return {
            "status": "skipped",
            "tag_keys": tag_keys,
            "warning": completed.stderr.strip() or "ffmpeg metadata embedding failed.",
        }

    temporary_path.replace(source)
    return {"status": "embedded", "tag_keys": tag_keys, "warning": None}
