from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Optional, Union

from tqdm import tqdm

from ivus_tools.conversion import convert_dicom_to_mp4
from ivus_tools.reports import default_report_path
from ivus_tools.reports import write_report as save_report

PathLike = Union[str, Path]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_dicom_files(input_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(
        path
        for path in input_dir.glob(pattern)
        if path.is_file() and path.suffix.lower() in {".dcm", ".dicom"}
    )


def batch_convert_dicom_to_mp4(
    input_dir: PathLike,
    output_dir: PathLike,
    fps: Optional[float] = None,
    codec: str = "mp4v",
    recursive: bool = False,
    show_progress: bool = True,
    write_sidecar: bool = True,
    embed_metadata: bool = True,
    report_path: Optional[PathLike] = None,
    write_report: bool = True,
) -> dict[str, Any]:
    started_at = _utc_now()
    start = perf_counter()
    source_dir = Path(input_dir)
    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    dicom_files = _find_dicom_files(source_dir, recursive=recursive)
    if not dicom_files:
        raise ValueError(f"No DICOM files found in: {source_dir}")

    entries: list[dict[str, Any]] = []
    iterator = tqdm(
        dicom_files, desc="Converting DICOM files", disable=not show_progress
    )
    for dicom_path in iterator:
        output_path = destination_dir / f"{dicom_path.stem}.mp4"
        try:
            result = convert_dicom_to_mp4(
                dicom_path,
                output_path,
                fps=fps,
                codec=codec,
                show_progress=False,
                write_sidecar=write_sidecar,
                embed_metadata=embed_metadata,
            )
            entries.append(
                {
                    "status": "success",
                    "input_path": str(dicom_path),
                    "output_path": str(output_path),
                    "frames_processed": result["frames_processed"],
                    "resolved_fps": result["resolved_fps"],
                    "fps_source": result["fps_source"],
                }
            )
        except Exception as error:  # noqa: BLE001 - batch reports per-file failures.
            entries.append(
                {
                    "status": "failure",
                    "input_path": str(dicom_path),
                    "output_path": str(output_path),
                    "error": str(error),
                }
            )

    success_count = sum(1 for entry in entries if entry["status"] == "success")
    failure_count = len(entries) - success_count
    report = {
        "command": "batch_convert",
        "start_time": started_at,
        "end_time": _utc_now(),
        "elapsed_seconds": round(perf_counter() - start, 6),
        "input_dir": str(source_dir),
        "output_dir": str(destination_dir),
        "success_count": success_count,
        "failure_count": failure_count,
        "files": entries,
        "warnings": [],
    }
    if write_report:
        destination = (
            Path(report_path)
            if report_path is not None
            else default_report_path(
                "batch_convert",
                output_dir=destination_dir,
            )
        )
        report["report_path"] = str(destination)
        save_report(destination, report)
    return report
