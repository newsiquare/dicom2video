from __future__ import annotations

import json

from ivus_tools.reports import default_report_path, write_report


def test_default_report_path_for_dicom_to_mp4(tmp_path) -> None:
    output_path = tmp_path / "study.mp4"

    report_path = default_report_path("dicom_to_mp4", output_path=output_path)

    assert report_path == tmp_path / "study.conversion-report.json"


def test_default_report_path_for_dicom_to_png(tmp_path) -> None:
    output_dir = tmp_path / "frames"

    report_path = default_report_path("dicom_to_png", output_dir=output_dir)

    assert report_path == output_dir / "conversion-report.json"


def test_default_report_path_for_batch_conversion(tmp_path) -> None:
    output_dir = tmp_path / "mp4"

    report_path = default_report_path("batch_convert", output_dir=output_dir)

    assert report_path == output_dir / "batch-conversion-report.json"


def test_write_report_saves_json(tmp_path) -> None:
    report_path = tmp_path / "nested" / "report.json"
    report = {"command": "dicom_to_mp4", "success_count": 1, "failure_count": 0}

    write_report(report_path, report)

    assert json.loads(report_path.read_text()) == report
