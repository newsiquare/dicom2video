from __future__ import annotations

import numpy as np
import pydicom

from ivus_tools.metadata import extract_metadata, select_mp4_metadata
from ivus_tools.timing import resolve_fps


def test_extract_metadata_includes_required_fields(make_test_dicom) -> None:
    frames = np.zeros((2, 3, 4), dtype=np.uint8)
    dicom_path = make_test_dicom(
        frames,
        FrameTime=50,
        Manufacturer="Acme",
        ManufacturerModelName="IVUS-9000",
        StudyDate="20260624",
        StudyTime="123456",
        InstitutionName="Research Hospital",
        PatientID="patient-1",
    )
    dataset = pydicom.dcmread(dicom_path)
    fps = resolve_fps(dataset)

    metadata = extract_metadata(dataset, fps)

    assert metadata == {
        "NumberOfFrames": 2,
        "Rows": 3,
        "Columns": 4,
        "FrameTime": 50.0,
        "CineRate": None,
        "RecommendedDisplayFrameRate": None,
        "Manufacturer": "Acme",
        "ManufacturerModelName": "IVUS-9000",
        "StudyDate": "20260624",
        "StudyTime": "123456",
        "InstitutionName": "Research Hospital",
        "PatientID": "patient-1",
        "ResolvedFrameRate": 20.0,
        "FrameRateSource": "FrameTime",
    }


def test_select_mp4_metadata_includes_required_tags_and_excludes_patient_id() -> None:
    dataset = pydicom.Dataset()
    dataset.StudyTime = "101112"
    dataset.InstitutionName = "Research Hospital"
    dataset.ManufacturerModelName = "IVUS-9000"
    dataset.PatientID = "patient-1"

    metadata = select_mp4_metadata(dataset)

    assert metadata == {
        "study_time": "101112",
        "institution_name": "Research Hospital",
        "manufacturer_model_name": "IVUS-9000",
    }
    assert "PatientID" not in metadata
    assert "patient_id" not in metadata
