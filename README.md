# IVUS Tools

Research-oriented utilities for IVUS DICOM conversion and preprocessing.

IVUS Tools focuses on multi-frame intravascular ultrasound cine DICOM workflows:

- DICOM to MP4 conversion with original frame-rate preservation.
- DICOM to zero-padded PNG sequence export for annotation and MedSAM2 workflows.
- PNG sequence to MP4 conversion.
- DICOM metadata extraction.
- Batch DICOM to MP4 conversion.

## Installation

Python 3.10+ is required.

```bash
pip install -r requirements.txt
```

For editable development installs:

```bash
pip install -e .
```

MP4 metadata embedding uses `ffmpeg` when available. If `ffmpeg` is missing, video conversion still succeeds and the JSON report records that MP4 metadata embedding was skipped.

## DICOM To MP4

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  -o study.mp4
```

Useful options:

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  -o study.mp4 \
  --codec mp4v \
  --report study.conversion-report.json
```

The command writes:

```text
study.mp4
study.metadata.json
study.conversion-report.json
```

The terminal also prints the completion result summary.

## Frame Rate Preservation

DICOM to MP4 preserves original timing metadata using this priority:

1. `--fps` override when provided.
2. DICOM `CineRate`.
3. DICOM `RecommendedDisplayFrameRate`.
4. DICOM `FrameTime`, converted as `1000 / FrameTime`.
5. Fallback fps only when no supported timing metadata exists.

The resolved fps and source are saved in the sidecar metadata JSON and conversion report.

## MP4 Metadata

When `ffmpeg` is available, DICOM to MP4 embeds these DICOM tags into the MP4 container by default:

- `StudyTime` as `study_time`
- `InstitutionName` as `institution_name`
- `ManufacturerModelName` as `manufacturer_model_name`

`PatientID` is not embedded into MP4 metadata by default. The fuller metadata record is stored in the sidecar JSON.

Disable MP4 metadata embedding with:

```bash
python dicom_to_mp4.py -i study.dcm -o study.mp4 --no-embed-metadata
```

## DICOM To PNG Sequence

```bash
python dicom_to_png.py \
  -i study.dcm \
  -o frames/
```

Frames are written in original order with zero-padded filenames:

```text
00000.png
00001.png
00002.png
```

The command writes `frames/conversion-report.json` by default.

## PNG Sequence To MP4

```bash
python png_to_mp4.py \
  -i frames/ \
  -o video.mp4 \
  --fps 20
```

PNG directories do not carry DICOM frame timing, so provide `--fps` when you need a specific playback rate. If omitted, the command uses the documented default shown in `--help`.

## Metadata Extraction

```bash
python extract_metadata.py -i study.dcm
```

Write JSON to a file:

```bash
python extract_metadata.py \
  -i study.dcm \
  -o metadata.json
```

The extracted fields include frame dimensions, frame timing tags, manufacturer details, study date/time, institution name, patient ID, resolved fps, and fps source.

## Batch Conversion

```bash
python batch_convert.py \
  --input-dir dicom/ \
  --output-dir mp4/
```

Batch conversion shows file-level progress, continues after per-file failures when possible, and writes:

```text
mp4/batch-conversion-report.json
```

Each report includes success/failure counts and per-file status entries.

## Progress And Reports

Long-running commands show progress bars by default. Disable progress output with:

```bash
--no-progress
```

Conversion commands save durable JSON reports by default. Use `--report PATH` to choose a report path or `--no-report` to disable report writing.

## MedSAM2 Workflow

For MedSAM2, prefer PNG sequences over MP4:

```text
DICOM -> PNG Sequence -> MedSAM2 -> Tracking -> Masks -> Video Overlay
```

PNG sequences avoid MP4 compression artifacts and preserve frame ordering for segmentation and tracking pipelines.

Example assets can be placed under `examples/` as the project adds public sample data, screenshots, and GIFs.
