from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Union

PathLike = Union[str, Path]


def default_report_path(
    command_name: str,
    output_path: Optional[PathLike] = None,
    output_dir: Optional[PathLike] = None,
) -> Path:
    if command_name == "batch_convert":
        if output_dir is None:
            raise ValueError("output_dir is required for batch conversion reports")
        return Path(output_dir) / "batch-conversion-report.json"

    if command_name == "dicom_to_png":
        if output_dir is None:
            raise ValueError("output_dir is required for DICOM to PNG reports")
        return Path(output_dir) / "conversion-report.json"

    if output_path is None:
        raise ValueError("output_path is required for video conversion reports")
    output = Path(output_path)
    return output.with_name(f"{output.stem}.conversion-report.json")


def write_report(path: PathLike, report: dict[str, Any]) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report_path
