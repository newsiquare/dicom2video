from __future__ import annotations

import json

import pydicom
from click.testing import CliRunner

from dicom_to_mp4 import cli as dicom_to_mp4_cli
from dicom_to_png import cli as dicom_to_png_cli
from examples.create_synthetic_dicom import create_synthetic_dicom


def test_synthetic_example_dicom_supports_cli_workflow(tmp_path) -> None:
    dicom_path = tmp_path / "synthetic_ivus.dcm"
    frame_dir = tmp_path / "frames"
    mp4_path = tmp_path / "synthetic_ivus.mp4"

    create_synthetic_dicom(dicom_path, frames=4, rows=16, columns=16, fps=20.0)

    dataset = pydicom.dcmread(dicom_path)
    assert dataset.NumberOfFrames == "4"
    assert dataset.FrameTime == 50.0
    assert dataset.PatientID == "SYNTHETIC"
    assert dataset.StudyTime == "120000"
    assert dataset.InstitutionName == "Synthetic IVUS Lab"
    assert dataset.ManufacturerModelName == "Synthetic-IVUS-Generator"

    runner = CliRunner()
    png_result = runner.invoke(
        dicom_to_png_cli,
        ["-i", str(dicom_path), "-o", str(frame_dir), "--no-progress"],
    )
    assert png_result.exit_code == 0
    assert (frame_dir / "00000.png").exists()
    assert (frame_dir / "00003.png").exists()
    assert (frame_dir / "conversion-report.json").exists()

    mp4_result = runner.invoke(
        dicom_to_mp4_cli,
        [
            "-i",
            str(dicom_path),
            "-o",
            str(mp4_path),
            "--no-progress",
            "--no-embed-metadata",
        ],
    )
    assert mp4_result.exit_code == 0
    assert mp4_path.exists()

    report = json.loads(
        (tmp_path / "synthetic_ivus.conversion-report.json").read_text()
    )
    assert report["frames_processed"] == 4
    assert report["resolved_fps"] == 20.0
    assert report["fps_source"] == "FrameTime"
