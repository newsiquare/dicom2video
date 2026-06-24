from __future__ import annotations

import pydicom

from ivus_tools.timing import resolve_fps


def test_resolve_fps_prefers_override() -> None:
    dataset = pydicom.Dataset()
    dataset.CineRate = 18

    result = resolve_fps(dataset, override_fps=42.0)

    assert result.fps == 42.0
    assert result.source == "override"
    assert result.used_fallback is False


def test_resolve_fps_prefers_cine_rate_over_other_tags() -> None:
    dataset = pydicom.Dataset()
    dataset.CineRate = 20
    dataset.RecommendedDisplayFrameRate = 25
    dataset.FrameTime = 50

    result = resolve_fps(dataset)

    assert result.fps == 20.0
    assert result.source == "CineRate"


def test_resolve_fps_uses_recommended_display_frame_rate_before_frame_time() -> None:
    dataset = pydicom.Dataset()
    dataset.RecommendedDisplayFrameRate = 15
    dataset.FrameTime = 20

    result = resolve_fps(dataset)

    assert result.fps == 15.0
    assert result.source == "RecommendedDisplayFrameRate"


def test_resolve_fps_converts_frame_time_milliseconds() -> None:
    dataset = pydicom.Dataset()
    dataset.FrameTime = 40

    result = resolve_fps(dataset)

    assert result.fps == 25.0
    assert result.source == "FrameTime"


def test_resolve_fps_reports_fallback_when_timing_missing() -> None:
    dataset = pydicom.Dataset()

    result = resolve_fps(dataset, fallback_fps=12.5)

    assert result.fps == 12.5
    assert result.source == "fallback"
    assert result.used_fallback is True
    assert result.warning == "No DICOM frame timing metadata found; using fallback fps."
