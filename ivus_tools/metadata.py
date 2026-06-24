from __future__ import annotations

from typing import Any, Optional

import pydicom

from ivus_tools.dicom import count_frames
from ivus_tools.timing import FrameRateResult, resolve_fps


def _string_value(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    if text == "":
        return None
    return text


def _float_value(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_value(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_metadata(
    dataset: pydicom.Dataset,
    fps_result: Optional[FrameRateResult] = None,
) -> dict[str, Any]:
    resolved_fps = fps_result or resolve_fps(dataset)
    return {
        "NumberOfFrames": count_frames(dataset),
        "Rows": _int_value(getattr(dataset, "Rows", None)),
        "Columns": _int_value(getattr(dataset, "Columns", None)),
        "FrameTime": _float_value(getattr(dataset, "FrameTime", None)),
        "CineRate": _float_value(getattr(dataset, "CineRate", None)),
        "RecommendedDisplayFrameRate": _float_value(
            getattr(dataset, "RecommendedDisplayFrameRate", None)
        ),
        "Manufacturer": _string_value(getattr(dataset, "Manufacturer", None)),
        "ManufacturerModelName": _string_value(
            getattr(dataset, "ManufacturerModelName", None)
        ),
        "StudyDate": _string_value(getattr(dataset, "StudyDate", None)),
        "StudyTime": _string_value(getattr(dataset, "StudyTime", None)),
        "InstitutionName": _string_value(getattr(dataset, "InstitutionName", None)),
        "PatientID": _string_value(getattr(dataset, "PatientID", None)),
        "ResolvedFrameRate": resolved_fps.fps,
        "FrameRateSource": resolved_fps.source,
    }


def select_mp4_metadata(dataset: pydicom.Dataset) -> dict[str, str]:
    selected = {
        "study_time": _string_value(getattr(dataset, "StudyTime", None)),
        "institution_name": _string_value(getattr(dataset, "InstitutionName", None)),
        "manufacturer_model_name": _string_value(
            getattr(dataset, "ManufacturerModelName", None)
        ),
    }
    return {key: value for key, value in selected.items() if value is not None}
