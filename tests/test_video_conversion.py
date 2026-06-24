from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np
import pytest
from PIL import Image

from ivus_tools.batch import batch_convert_dicom_to_mp4
from ivus_tools.conversion import convert_dicom_to_mp4, convert_png_to_mp4
from ivus_tools.video import embed_mp4_metadata, write_mp4


def test_write_mp4_with_libx264_uses_aligned_ffmpeg_command(
    tmp_path, monkeypatch
) -> None:
    command_calls = []
    written_chunks = []

    class FakeStdin:
        def write(self, chunk: bytes) -> None:
            written_chunks.append(chunk)

        def close(self) -> None:
            pass

    class FakeProcess:
        def __init__(self, command, stdin, stderr):
            command_calls.append(command)
            self.stdin = FakeStdin()
            self.returncode = 0

        def wait(self) -> int:
            return self.returncode

    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(subprocess, "Popen", FakeProcess)
    output_path = tmp_path / "video.mp4"

    write_mp4(
        [np.zeros((8, 10), dtype=np.uint8), np.full((8, 10), 255, dtype=np.uint8)],
        output_path,
        fps=20.0,
        codec="libx264",
    )

    command = command_calls[0]
    assert command == [
        "/usr/bin/ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        "10x8",
        "-r",
        "20.0",
        "-i",
        "-",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        str(output_path),
    ]
    assert len(written_chunks) == 2


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


def test_batch_convert_recursively_converts_extensionless_dicom_files(
    tmp_path, make_test_dicom
) -> None:
    input_dir = tmp_path / "dicom"
    nested_dir = input_dir / "run1"
    output_dir = tmp_path / "mp4"
    nested_dir.mkdir(parents=True)
    dicom_path = make_test_dicom(
        np.zeros((1, 8, 8), dtype=np.uint8), filename="PDSTXFUV", FrameTime=40
    )
    dicom_path.rename(nested_dir / "PDSTXFUV")

    result = batch_convert_dicom_to_mp4(
        input_dir,
        output_dir,
        recursive=True,
        show_progress=False,
        embed_metadata=False,
    )

    assert result["success_count"] == 1
    assert result["failure_count"] == 0
    assert (output_dir / "run1" / "PDSTXFUV.mp4").exists()


def test_embed_mp4_metadata_writes_probeable_custom_tags(tmp_path) -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("ffmpeg and ffprobe are required for MP4 metadata integration test")

    output_path = tmp_path / "metadata.mp4"
    frames = [np.full((8, 8), 90, dtype=np.uint8), np.full((8, 8), 140, dtype=np.uint8)]
    write_mp4(frames, output_path, fps=10.0)

    result = embed_mp4_metadata(
        output_path,
        {
            "study_time": "120000",
            "institution_name": "Synthetic IVUS Lab",
            "manufacturer_model_name": "Synthetic-IVUS-Generator",
        },
    )

    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format_tags=study_time,institution_name,manufacturer_model_name",
            "-of",
            "json",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    tags = json.loads(completed.stdout)["format"]["tags"]

    assert result["status"] == "embedded"
    assert tags == {
        "study_time": "120000",
        "institution_name": "Synthetic IVUS Lab",
        "manufacturer_model_name": "Synthetic-IVUS-Generator",
    }
