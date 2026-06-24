from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Union

import numpy as np
import pydicom

PathLike = Union[str, Path]


def load_dicom(path: PathLike) -> pydicom.Dataset:
    dicom_path = Path(path)
    if not dicom_path.exists():
        raise FileNotFoundError(f"Input DICOM not found: {dicom_path}")
    dataset = pydicom.dcmread(dicom_path)
    if "PixelData" not in dataset:
        raise ValueError(f"DICOM file has no pixel data: {dicom_path}")
    return dataset


def normalize_frame(frame: np.ndarray) -> np.ndarray:
    array = np.asarray(frame)
    if array.dtype == np.uint8:
        return array

    array = array.astype(np.float32)
    minimum = float(np.min(array))
    maximum = float(np.max(array))
    if maximum <= minimum:
        return np.zeros(array.shape, dtype=np.uint8)
    return ((array - minimum) / (maximum - minimum) * 255.0).astype(np.uint8)


def iter_frames(dataset: pydicom.Dataset) -> Iterator[np.ndarray]:
    pixel_array = dataset.pixel_array
    if pixel_array.ndim == 2:
        yield normalize_frame(pixel_array)
        return

    for frame in pixel_array:
        yield normalize_frame(frame)


def count_frames(dataset: pydicom.Dataset) -> int:
    number_of_frames = getattr(dataset, "NumberOfFrames", None)
    if number_of_frames is not None:
        return int(number_of_frames)
    return 1
