# Priority 1 Core Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement IVUS DICOM to MP4, DICOM to PNG, PNG to MP4, metadata extraction, and batch conversion with progress bars, timing preservation, MP4 metadata embedding, sidecar metadata, and durable JSON reports.

**Architecture:** Root scripts are thin Click CLI wrappers. Reusable logic lives in `ivus_tools/` modules for DICOM frame loading, fps resolution, metadata extraction, video writing, reports, and batch orchestration. Tests use synthetic DICOM datasets and small NumPy arrays.

**Tech Stack:** Python 3.10+, pydicom, numpy, opencv-python, pillow, tqdm, click, pytest.

## Global Constraints

- Preserve frame ordering for all DICOM and PNG sequence workflows.
- Preserve original DICOM timing when `CineRate`, `RecommendedDisplayFrameRate`, or `FrameTime` exists; only use fallback fps when no timing tag exists.
- Show progress bars by default and support `--no-progress`.
- Embed `StudyTime`, `InstitutionName`, and `ManufacturerModelName` into MP4 metadata by default when `ffmpeg` is available.
- Never embed `PatientID` into MP4 metadata by default.
- Save durable JSON conversion reports by default and support `--report PATH` and `--no-report`.
- Use type hints on public functions.

---

### Task 1: Tests And Fixtures

**Files:**

- Create: `tests/conftest.py`
- Create: `tests/test_timing.py`
- Create: `tests/test_metadata.py`
- Create: `tests/test_png_export.py`
- Create: `tests/test_reports.py`

**Interfaces:**

- Produces synthetic DICOM fixture helper `make_test_dicom(path, frames, **tags)`.
- Consumes future functions `resolve_fps`, `extract_metadata`, `select_mp4_metadata`, `export_dicom_to_png`, `default_report_path`, and `write_report`.

- [ ] Write failing tests for fps priority, metadata fields, MP4 metadata tag selection, PNG frame order, and report writing.
- [ ] Run `pytest tests/test_timing.py tests/test_metadata.py tests/test_png_export.py tests/test_reports.py -q` and confirm failures are due to missing `ivus_tools` modules.

### Task 2: Core Package

**Files:**

- Create: `ivus_tools/__init__.py`
- Create: `ivus_tools/timing.py`
- Create: `ivus_tools/dicom.py`
- Create: `ivus_tools/metadata.py`
- Create: `ivus_tools/reports.py`

**Interfaces:**

- Produces `FrameRateResult`, `resolve_fps(dataset, override_fps=None, fallback_fps=30.0)`, `load_dicom(path)`, `iter_frames(dataset)`, `extract_metadata(dataset, fps_result=None)`, `select_mp4_metadata(dataset)`, `default_report_path(command_name, output_path, output_dir=None)`, and `write_report(path, report)`.

- [ ] Implement the minimal core package to satisfy Task 1 tests.
- [ ] Run `pytest tests/test_timing.py tests/test_metadata.py tests/test_png_export.py tests/test_reports.py -q` and confirm passing tests for implemented core behavior.

### Task 3: Conversion Workflows

**Files:**

- Create: `ivus_tools/video.py`
- Create: `ivus_tools/conversion.py`
- Create: `ivus_tools/batch.py`

**Interfaces:**

- Produces `export_dicom_to_png`, `convert_dicom_to_mp4`, `convert_png_to_mp4`, and `batch_convert_dicom_to_mp4`.

- [ ] Add conversion functions using OpenCV, Pillow, tqdm, sidecar metadata, optional ffmpeg metadata remuxing, and JSON reports.
- [ ] Add tests for PNG export and report behavior.
- [ ] Run the focused pytest command and confirm passing.

### Task 4: CLI Wrappers

**Files:**

- Modify: `dicom_to_mp4.py`
- Modify: `dicom_to_png.py`
- Modify: `png_to_mp4.py`
- Modify: `extract_metadata.py`
- Modify: `batch_convert.py`

**Interfaces:**

- Consumes package conversion functions and exposes documented root script commands.

- [ ] Replace placeholder scripts with Click commands.
- [ ] Print completion summaries and write JSON reports by default.
- [ ] Run `python dicom_to_mp4.py --help`, `python dicom_to_png.py --help`, `python png_to_mp4.py --help`, `python extract_metadata.py --help`, and `python batch_convert.py --help`.

### Task 5: Dependencies And Documentation

**Files:**

- Modify: `requirements.txt`
- Modify: `README.md`
- Modify: `setup.py`
- Modify: `Dockerfile` if needed.

**Interfaces:**

- Documents installation, usage, fps preservation, metadata sidecars, MP4 embedded tags, reports, and MedSAM2 PNG sequence guidance.

- [ ] Add required dependencies.
- [ ] Update setup metadata enough for package discovery.
- [ ] Update README usage and behavior notes.
- [ ] Run `pytest -q` and CLI help checks.
