from __future__ import annotations

import json

import numpy as np
from click.testing import CliRunner

from batch_convert import cli as batch_convert_cli
from dicom_to_mp4 import cli as dicom_to_mp4_cli
from dicom_to_png import cli as dicom_to_png_cli
from extract_metadata import cli as extract_metadata_cli
from png_to_mp4 import cli as png_to_mp4_cli


def test_cli_help_commands() -> None:
    runner = CliRunner()

    for command in [
        dicom_to_mp4_cli,
        dicom_to_png_cli,
        png_to_mp4_cli,
        extract_metadata_cli,
        batch_convert_cli,
    ]:
        result = runner.invoke(command, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output


def test_extract_metadata_cli_prints_json(make_test_dicom) -> None:
    dicom_path = make_test_dicom(
        np.zeros((2, 4, 5), dtype=np.uint8),
        FrameTime=50,
        StudyTime="101112",
        InstitutionName="Research Hospital",
        ManufacturerModelName="IVUS-9000",
    )
    runner = CliRunner()

    result = runner.invoke(extract_metadata_cli, ["-i", str(dicom_path)])

    assert result.exit_code == 0
    metadata = json.loads(result.output)
    assert metadata["NumberOfFrames"] == 2
    assert metadata["ResolvedFrameRate"] == 20.0
    assert metadata["StudyTime"] == "101112"
