from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pydicom


@dataclass(frozen=True)
class FrameRateResult:
    fps: float
    source: str
    used_fallback: bool = False
    warning: Optional[str] = None


def _positive_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        fps = float(value)
    except (TypeError, ValueError):
        return None
    if fps <= 0:
        return None
    return fps


def resolve_fps(
    dataset: pydicom.Dataset,
    override_fps: Optional[float] = None,
    fallback_fps: float = 30.0,
) -> FrameRateResult:
    override = _positive_float(override_fps)
    if override is not None:
        return FrameRateResult(fps=override, source="override")

    cine_rate = _positive_float(getattr(dataset, "CineRate", None))
    if cine_rate is not None:
        return FrameRateResult(fps=cine_rate, source="CineRate")

    recommended_rate = _positive_float(
        getattr(dataset, "RecommendedDisplayFrameRate", None)
    )
    if recommended_rate is not None:
        return FrameRateResult(
            fps=recommended_rate, source="RecommendedDisplayFrameRate"
        )

    frame_time = _positive_float(getattr(dataset, "FrameTime", None))
    if frame_time is not None:
        return FrameRateResult(fps=1000.0 / frame_time, source="FrameTime")

    fallback = _positive_float(fallback_fps) or 30.0
    return FrameRateResult(
        fps=fallback,
        source="fallback",
        used_fallback=True,
        warning="No DICOM frame timing metadata found; using fallback fps.",
    )
