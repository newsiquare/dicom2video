from __future__ import annotations

import numpy as np
import pydicom
from pydicom.dataset import Dataset

from ivus_tools.dicom import iter_frames


def test_iter_frames_treats_single_rgb_image_as_one_frame() -> None:
    dataset = Dataset()
    dataset.Rows = 4
    dataset.Columns = 5
    dataset.SamplesPerPixel = 3
    dataset.PhotometricInterpretation = "RGB"
    dataset.PlanarConfiguration = 0
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.file_meta = Dataset()
    dataset.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    pixel_array = np.zeros((4, 5, 3), dtype=np.uint8)
    pixel_array[:, :, 0] = 200
    dataset.PixelData = pixel_array.tobytes()

    frames = list(iter_frames(dataset))

    assert len(frames) == 1
    assert frames[0].shape == (4, 5, 3)
    assert int(frames[0][0, 0, 0]) == 200
