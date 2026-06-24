from __future__ import annotations

import json

import numpy as np
from PIL import Image

from ivus_tools.batch import batch_convert_dicom_to_mp4
from ivus_tools.conversion import convert_dicom_to_mp4, convert_png_to_mp4


def test_convert_dicom_to_mp4_writes_video_sidecar_and_report(
    tmp_path, make_test_dicom
) -> None:
    frames = np.stack(
        [
            np.full((8, 8), 20, dtype=np.uint8),
            np.full((8, 8), 120, dtype=np.uint8),
        ]
    )
    dicom_path = make_test_dicom(
        frames,
        FrameTime=50,
        StudyTime="101112",
        InstitutionName="Research Hospital",
        ManufacturerModelName="IVUS-9000",
        PatientID="patient-1",
    )
    output_path = tmp_path / "study.mp4"

    result = convert_dicom_to_mp4(
        dicom_path,
        output_path,
        show_progress=False,
        embed_metadata=False,
    )

    sidecar_path = tmp_path / "study.metadata.json"
    report_path = tmp_path / "study.conversion-report.json"
    assert output_path.exists()
    assert sidecar_path.exists()
    assert report_path.exists()
    assert result["frames_processed"] == 2
    assert result["resolved_fps"] == 20.0
    assert result["fps_source"] == "FrameTime"
    assert result["mp4_metadata"]["status"] == "disabled"
    assert result["mp4_metadata"]["tag_keys"] == [
        "institution_name",
        "manufacturer_model_name",
        "study_time",
    ]
    assert "PatientID" not in json.loads(sidecar_path.read_text()).get(
        "mp4_metadata", {}
    )
    assert json.loads(report_path.read_text())["output_path"] == str(output_path)


def test_convert_png_to_mp4_writes_report(tmp_path) -> None:
    frame_dir = tmp_path / "frames"
    frame_dir.mkdir()
    Image.fromarray(np.full((8, 8), 10, dtype=np.uint8)).save(frame_dir / "00000.png")
    Image.fromarray(np.full((8, 8), 200, dtype=np.uint8)).save(frame_dir / "00001.png")
    output_path = tmp_path / "video.mp4"

    result = convert_png_to_mp4(
        frame_dir,
        output_path,
        fps=12.0,
        show_progress=False,
    )

    assert output_path.exists()
    assert (tmp_path / "video.conversion-report.json").exists()
    assert result["frames_processed"] == 2
    assert result["resolved_fps"] == 12.0
    assert result["fps_source"] == "provided"


def test_batch_convert_dicom_to_mp4_continues_and_reports_failures(
    tmp_path, make_test_dicom
) -> None:
    input_dir = tmp_path / "dicom"
    output_dir = tmp_path / "mp4"
    input_dir.mkdir()
    make_test_dicom(np.zeros((1, 8, 8), dtype=np.uint8), filename="a.dcm", FrameTime=40)
    source_path = tmp_path / "a.dcm"
    source_path.rename(input_dir / "a.dcm")
    (input_dir / "broken.dcm").write_text("not a dicom")

    result = batch_convert_dicom_to_mp4(
        input_dir,
        output_dir,
        show_progress=False,
        embed_metadata=False,
    )

    assert result["success_count"] == 1
    assert result["failure_count"] == 1
    assert (output_dir / "a.mp4").exists()
    assert (output_dir / "batch-conversion-report.json").exists()
    assert [entry["status"] for entry in result["files"]] == ["success", "failure"]
