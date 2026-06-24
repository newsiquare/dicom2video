from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pydicom
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage


@pytest.fixture
def make_test_dicom(tmp_path: Path):
    def _make_test_dicom(
        frames: np.ndarray,
        filename: str = "study.dcm",
        **tags: Any,
    ) -> Path:
        path = tmp_path / filename
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

        dataset = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
        dataset.is_little_endian = True
        dataset.is_implicit_VR = False

        pixel_frames = np.asarray(frames, dtype=np.uint8)
        if pixel_frames.ndim == 2:
            rows, columns = pixel_frames.shape
            number_of_frames = 1
        else:
            number_of_frames, rows, columns = pixel_frames.shape
            dataset.NumberOfFrames = str(number_of_frames)

        dataset.SOPClassUID = SecondaryCaptureImageStorage
        dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        dataset.Modality = "US"
        dataset.Rows = rows
        dataset.Columns = columns
        dataset.SamplesPerPixel = 1
        dataset.PhotometricInterpretation = "MONOCHROME2"
        dataset.BitsAllocated = 8
        dataset.BitsStored = 8
        dataset.HighBit = 7
        dataset.PixelRepresentation = 0
        dataset.PixelData = pixel_frames.tobytes()

        for key, value in tags.items():
            setattr(dataset, key, value)

        dataset.save_as(path)
        return path

    return _make_test_dicom
