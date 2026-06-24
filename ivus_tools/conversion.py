from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Optional, Union

import numpy as np
from PIL import Image
from tqdm import tqdm

from ivus_tools.dicom import iter_frames, load_dicom
from ivus_tools.metadata import extract_metadata, select_mp4_metadata
from ivus_tools.reports import default_report_path
from ivus_tools.reports import write_report as save_report
from ivus_tools.timing import resolve_fps
from ivus_tools.video import embed_mp4_metadata, write_mp4

PathLike = Union[str, Path]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def export_dicom_to_png(
    input_path: PathLike,
    output_dir: PathLike,
    digits: int = 5,
    show_progress: bool = True,
    report_path: Optional[PathLike] = None,
    write_report: bool = True,
) -> dict[str, Any]:
    started_at = _utc_now()
    start = perf_counter()
    dataset = load_dicom(input_path)
    frames = list(iter_frames(dataset))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    frame_names: list[str] = []
    iterator = tqdm(frames, desc="Exporting PNG frames", disable=not show_progress)
    for index, frame in enumerate(iterator):
        frame_name = f"{index:0{digits}d}.png"
        Image.fromarray(frame).save(output / frame_name)
        frame_names.append(frame_name)

    ended_at = _utc_now()
    report = {
        "command": "dicom_to_png",
        "start_time": started_at,
        "end_time": ended_at,
        "elapsed_seconds": round(perf_counter() - start, 6),
        "input_path": str(Path(input_path)),
        "output_dir": str(output),
        "frames_processed": len(frame_names),
        "first_frame": frame_names[0] if frame_names else None,
        "last_frame": frame_names[-1] if frame_names else None,
        "success_count": 1,
        "failure_count": 0,
        "warnings": [],
    }

    if write_report:
        destination = (
            Path(report_path)
            if report_path is not None
            else default_report_path(
                "dicom_to_png",
                output_dir=output,
            )
        )
        report["report_path"] = str(destination)
        save_report(destination, report)

    return report


def _sidecar_path(output_path: PathLike) -> Path:
    output = Path(output_path)
    return output.with_name(f"{output.stem}.metadata.json")


def convert_dicom_to_mp4(
    input_path: PathLike,
    output_path: PathLike,
    fps: Optional[float] = None,
    codec: str = "libx264",
    show_progress: bool = True,
    write_sidecar: bool = True,
    embed_metadata: bool = True,
    report_path: Optional[PathLike] = None,
    write_report: bool = True,
) -> dict[str, Any]:
    started_at = _utc_now()
    start = perf_counter()
    dataset = load_dicom(input_path)
    fps_result = resolve_fps(dataset, override_fps=fps)
    frames = list(iter_frames(dataset))
    iterator = tqdm(frames, desc="Writing MP4 frames", disable=not show_progress)
    write_mp4(
        [np.asarray(frame) for frame in iterator],
        output_path,
        fps_result.fps,
        codec=codec,
    )

    mp4_tags = select_mp4_metadata(dataset)
    mp4_metadata_status = embed_mp4_metadata(
        output_path, mp4_tags, enabled=embed_metadata
    )
    warnings = []
    if fps_result.warning:
        warnings.append(fps_result.warning)
    if mp4_metadata_status.get("warning"):
        warnings.append(str(mp4_metadata_status["warning"]))

    sidecar = None
    if write_sidecar:
        sidecar = _sidecar_path(output_path)
        metadata = extract_metadata(dataset, fps_result)
        metadata["mp4_metadata"] = mp4_tags
        metadata["MP4MetadataStatus"] = mp4_metadata_status["status"]
        save_report(sidecar, metadata)

    report = {
        "command": "dicom_to_mp4",
        "start_time": started_at,
        "end_time": _utc_now(),
        "elapsed_seconds": round(perf_counter() - start, 6),
        "input_path": str(Path(input_path)),
        "output_path": str(Path(output_path)),
        "frames_processed": len(frames),
        "resolved_fps": fps_result.fps,
        "fps_source": fps_result.source,
        "codec": codec,
        "sidecar_metadata_path": str(sidecar) if sidecar is not None else None,
        "mp4_metadata": mp4_metadata_status,
        "success_count": 1,
        "failure_count": 0,
        "warnings": warnings,
    }
    if write_report:
        destination = (
            Path(report_path)
            if report_path is not None
            else default_report_path(
                "dicom_to_mp4",
                output_path=output_path,
            )
        )
        report["report_path"] = str(destination)
        save_report(destination, report)
    return report


def convert_png_to_mp4(
    input_dir: PathLike,
    output_path: PathLike,
    fps: float,
    codec: str = "mp4v",
    show_progress: bool = True,
    report_path: Optional[PathLike] = None,
    write_report: bool = True,
) -> dict[str, Any]:
    started_at = _utc_now()
    start = perf_counter()
    directory = Path(input_dir)
    png_paths = sorted(directory.glob("*.png"))
    if not png_paths:
        raise ValueError(f"No PNG files found in: {directory}")

    iterator = tqdm(png_paths, desc="Writing MP4 frames", disable=not show_progress)
    frames = [np.asarray(Image.open(path).convert("RGB")) for path in iterator]
    write_mp4(frames, output_path, fps, codec=codec)

    report = {
        "command": "png_to_mp4",
        "start_time": started_at,
        "end_time": _utc_now(),
        "elapsed_seconds": round(perf_counter() - start, 6),
        "input_dir": str(directory),
        "output_path": str(Path(output_path)),
        "frames_processed": len(frames),
        "resolved_fps": float(fps),
        "fps_source": "provided",
        "codec": codec,
        "success_count": 1,
        "failure_count": 0,
        "warnings": [],
    }
    if write_report:
        destination = (
            Path(report_path)
            if report_path is not None
            else default_report_path(
                "png_to_mp4",
                output_path=output_path,
            )
        )
        report["report_path"] = str(destination)
        save_report(destination, report)
    return report
