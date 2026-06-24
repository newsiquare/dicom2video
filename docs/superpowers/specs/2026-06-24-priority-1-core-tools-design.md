# IVUS Tools Priority 1 Core Tools Design

## Purpose

Build the first production-quality slice of IVUS Tools for IVUS cine DICOM preprocessing. This phase implements the core command-line workflows researchers need before MedSAM2, annotation, COCO, and nnU-Net integrations: DICOM to MP4, DICOM to PNG sequence, metadata extraction, and batch conversion.

The implementation must preserve frame ordering and original DICOM timing whenever timing metadata is present. PNG sequence export is a first-class workflow because it avoids MP4 compression artifacts for segmentation and tracking pipelines.

## Scope

Priority 1 includes:

- Convert multi-frame IVUS DICOM files to MP4.
- Export multi-frame IVUS DICOM files to zero-padded PNG sequences.
- Extract important DICOM metadata as JSON.
- Batch convert a folder of DICOM files to MP4 outputs.
- Show progress bars during long-running conversion work.
- Preserve original frame rate from DICOM metadata unless the user explicitly overrides it.
- Write selected DICOM tags into MP4 metadata by default when creating MP4 files.

Out of scope for this phase:

- MedSAM2 execution and mask tracking.
- COCO export.
- nnU-Net dataset export.
- DICOM de-identification beyond avoiding PatientID in MP4 metadata by default.
- Visual overlays or mask video rendering.

## Repository Shape

The project should move from placeholder root scripts toward a reusable Python package while preserving the documented CLI examples.

```text
ivus_tools/
    __init__.py
    dicom.py
    timing.py
    video.py
    metadata.py
    batch.py

dicom_to_mp4.py
dicom_to_png.py
png_to_mp4.py
extract_metadata.py
batch_convert.py
```

The root scripts remain thin CLI wrappers so existing usage keeps working:

```bash
python dicom_to_mp4.py -i study.dcm -o study.mp4
python dicom_to_png.py -i study.dcm -o frames/
python png_to_mp4.py -i frames/ -o video.mp4
python extract_metadata.py -i study.dcm
python batch_convert.py --input-dir dicom/ --output-dir mp4/
```

Shared behavior lives inside `ivus_tools/` so it can be tested directly and reused by future MedSAM2, annotation, and nnU-Net workflows.

## Architecture

`ivus_tools.dicom` owns DICOM loading and frame normalization. It reads DICOM with `pydicom`, retrieves `pixel_array`, preserves frame order, and converts frames to OpenCV-compatible `uint8` arrays. Single-frame and multi-frame inputs should be represented through the same iterator-style interface so the conversion code does not special-case frame counts.

`ivus_tools.timing` owns frame-rate detection. It exposes a single fps resolution function used by DICOM to MP4 and batch conversion. Keeping timing in one module prevents different commands from drifting in behavior.

`ivus_tools.video` owns MP4 writing. It accepts normalized frames, target fps, codec, and progress settings. OpenCV `VideoWriter` writes the visual stream. Because OpenCV does not reliably write MP4 metadata, DICOM tag embedding is handled as a post-processing step through `ffmpeg` when available.

`ivus_tools.metadata` owns JSON metadata extraction and MP4 metadata tag selection. It returns plain Python dictionaries so CLI scripts can print JSON, write sidecar JSON files, or pass selected tags to video embedding.

`ivus_tools.batch` owns directory traversal and repeated conversion. It should keep batch concerns separate from single-file conversion logic.

## Frame Rate Rules

Frame timing accuracy is mandatory. The fps resolver uses this order:

1. CLI `--fps` override when provided.
2. DICOM `CineRate`.
3. DICOM `RecommendedDisplayFrameRate`.
4. DICOM `FrameTime`, converted with `1000 / FrameTime` because DICOM `FrameTime` is stored in milliseconds.
5. Fallback default only when no supported timing metadata exists.

When the fallback is used, the CLI should emit a warning that no DICOM timing metadata was found. The implementation must not assume 30 fps when `CineRate`, `RecommendedDisplayFrameRate`, or `FrameTime` is available.

The resolved fps should be included in metadata output and sidecar JSON so downstream workflows can audit timing decisions.

## Progress Bars

Long-running commands must show progress with `tqdm` by default:

- DICOM to MP4 shows frame write progress.
- DICOM to PNG shows frame export progress.
- PNG sequence to MP4 shows image write progress.
- Batch conversion shows file-level progress.

Commands should provide a quiet mode such as `--no-progress` for scripting and CI output. Batch conversion may suppress nested per-frame progress by default while keeping file-level progress visible.

## Completion Result Summary

After each conversion or batch command finishes, the CLI must print a concise result summary so users can immediately verify what was produced.

Single-file conversion summaries should include:

- Input path.
- Output path.
- Number of frames processed.
- Resolved fps and fps source when video is created from DICOM.
- Sidecar metadata JSON path when written.
- MP4 embedded metadata status when MP4 is created.

PNG export summaries should include the output directory and first/last zero-padded frame filenames. Batch conversion summaries should list each completed input and output pair, plus total success and failure counts. Failures should be reported with the input path and error message while allowing later files to continue when possible.

The same result summary should also be saved as a machine-readable JSON report by default. Terminal output is for immediate inspection; the JSON report is the durable record for research bookkeeping, pipeline audits, and later troubleshooting.

Recommended report naming:

- DICOM to MP4: write next to the MP4 as `study.conversion-report.json`.
- PNG sequence to MP4: write next to the MP4 as `video.conversion-report.json`.
- DICOM to PNG: write inside the output frame directory as `conversion-report.json`.
- Batch conversion: write inside the batch output directory as `batch-conversion-report.json`.

Commands should provide `--report PATH` to choose an explicit report path and `--no-report` to disable report writing. When a default report path already exists, the command should overwrite it for single-output commands and overwrite `batch-conversion-report.json` for batch commands because the report represents the latest run for that output location.

The conversion report should include:

- Command name and tool version when available.
- Start time, end time, and elapsed seconds.
- Input path or paths.
- Output path or paths.
- Number of frames processed.
- Resolved fps and fps source when applicable.
- Codec when MP4 is created.
- Sidecar metadata JSON path when written.
- MP4 embedded metadata status and embedded tag keys when applicable.
- Success and failure counts.
- Per-file status entries for batch conversion.
- Warning messages, including missing timing metadata or missing `ffmpeg`.

## MP4 Metadata Requirements

When creating MP4 files from DICOM, the toolkit should write these selected DICOM tags into the MP4 metadata by default when values exist:

- `StudyTime` as `study_time`.
- `InstitutionName` as `institution_name`.
- `ManufacturerModelName` as `manufacturer_model_name`.

These tags are intentionally limited to useful acquisition/context metadata. `PatientID` must not be embedded into MP4 metadata by default. `PatientID` may appear in metadata extraction JSON because that command is explicitly for metadata inspection, but embedding patient identifiers into a portable video file should require a future explicit opt-in option.

Because MP4 metadata support depends on the writer and container tooling, the implementation should:

- Write MP4 frames with OpenCV.
- If `ffmpeg` is available, remux the MP4 with the selected metadata tags.
- If `ffmpeg` is unavailable, keep the MP4 video output and emit a warning that embedded MP4 metadata was skipped.
- Always write a sidecar JSON metadata file next to MP4 outputs unless the user disables it.

The sidecar naming convention is:

```text
study.mp4
study.metadata.json
```

The sidecar JSON is the reliable research record. MP4 embedded metadata is a convenience for file inspection and lightweight provenance.

## Metadata Extraction

The metadata extraction command outputs JSON containing at least:

- `NumberOfFrames`
- `Rows`
- `Columns`
- `FrameTime`
- `CineRate`
- `RecommendedDisplayFrameRate`
- `Manufacturer`
- `ManufacturerModelName`
- `StudyDate`
- `StudyTime`
- `InstitutionName`
- `PatientID`
- `ResolvedFrameRate`
- `FrameRateSource`

Missing DICOM tags should appear as `null` in JSON rather than causing command failure. This makes batch metadata inspection predictable across heterogeneous IVUS exports.

## CLI Design

`dicom_to_mp4.py` options:

- `-i, --input`: input DICOM path.
- `-o, --output`: output MP4 path.
- `--fps`: optional explicit fps override.
- `--codec`: MP4 codec, default `mp4v`.
- `--no-progress`: disable progress bar.
- `--no-sidecar`: disable sidecar metadata JSON.
- `--no-embed-metadata`: skip MP4 metadata embedding.

`dicom_to_png.py` options:

- `-i, --input`: input DICOM path.
- `-o, --output`: output frame directory.
- `--digits`: zero-padding width, default `5`.
- `--no-progress`: disable progress bar.

`png_to_mp4.py` options:

- `-i, --input`: input PNG directory.
- `-o, --output`: output MP4 path.
- `--fps`: required or defaulted to a documented fallback because PNG directories do not inherently store timing.
- `--codec`: MP4 codec, default `mp4v`.
- `--no-progress`: disable progress bar.

`extract_metadata.py` options:

- `-i, --input`: input DICOM path.
- `-o, --output`: optional output JSON path. If omitted, print to stdout.

`batch_convert.py` options:

- `--input-dir`: input directory containing DICOM files.
- `--output-dir`: output MP4 directory.
- `--fps`: optional explicit fps override for all files.
- `--codec`: MP4 codec, default `mp4v`.
- `--recursive`: include nested directories.
- `--no-progress`: disable progress bars.
- `--no-sidecar`: disable sidecar metadata JSON.
- `--no-embed-metadata`: skip MP4 metadata embedding.

## Error Handling

Commands should fail with clear messages for:

- Missing input files.
- Non-readable DICOM files.
- DICOM files without pixel data.
- Output directories that cannot be created.
- MP4 writer initialization failure.
- Empty PNG input directories.

Missing optional DICOM metadata is not an error. Missing `ffmpeg` is not an error when video writing succeeds; it only disables MP4 tag embedding with a warning.

## Testing Strategy

Tests should be written before implementation. Synthetic DICOM datasets should be generated in tests with `pydicom` and small NumPy arrays so no patient data or large binary fixtures are required.

Minimum Priority 1 tests:

- FPS resolver prefers explicit override over DICOM tags.
- FPS resolver prefers `CineRate` over `RecommendedDisplayFrameRate` and `FrameTime`.
- FPS resolver converts `FrameTime` milliseconds into fps.
- DICOM to PNG preserves frame order and creates zero-padded filenames.
- Metadata extraction includes required fields and uses `null` for missing tags.
- MP4 metadata selection includes `StudyTime`, `InstitutionName`, and `ManufacturerModelName` but excludes `PatientID`.
- Batch conversion creates one MP4 path per input DICOM.

Video file content tests can remain lightweight. The core behavioral tests should target frame ordering, fps selection, metadata dictionaries, and command argument wiring. Full MP4 encoding can be covered by a small smoke test if OpenCV is available in CI.

## Documentation Requirements

README updates for this phase should include:

- Installation.
- DICOM to MP4 usage.
- DICOM to PNG sequence usage.
- PNG sequence to MP4 usage.
- Metadata extraction usage.
- Batch conversion usage.
- Explanation of fps preservation priority.
- Explanation of sidecar metadata JSON and embedded MP4 tags.
- MedSAM2 workflow note explaining why PNG sequences are preferred over MP4.

Screenshots and GIF examples can be placeholders in this phase only if real sample assets are not available yet, but the README should document where examples will live, such as `examples/`.

## Acceptance Criteria

The Priority 1 phase is complete when:

- All four priority commands run from the documented root scripts.
- DICOM to MP4 preserves DICOM-derived fps unless `--fps` is provided.
- DICOM to MP4 shows a frame progress bar by default.
- Conversion commands print a completion result summary listing produced outputs and key processing details.
- Conversion commands save the completion result summary as a JSON report by default.
- DICOM to PNG writes ordered zero-padded PNG frames and shows progress by default.
- Metadata extraction outputs the required JSON fields.
- Batch conversion converts a directory of DICOM files and shows file-level progress.
- MP4 outputs embed `StudyTime`, `InstitutionName`, and `ManufacturerModelName` when `ffmpeg` is available.
- MP4 conversion writes sidecar metadata JSON by default.
- Automated tests cover fps resolution, metadata selection, metadata extraction, and frame ordering.
