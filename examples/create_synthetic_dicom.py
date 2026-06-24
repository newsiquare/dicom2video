from __future__ import annotations

from pathlib import Path
from typing import Union

import click
import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage

PathLike = Union[str, Path]


def _synthetic_frames(frame_count: int, rows: int, columns: int) -> np.ndarray:
    y_axis, x_axis = np.ogrid[:rows, :columns]
    center_y = rows / 2.0
    center_x = columns / 2.0
    radius = np.sqrt((y_axis - center_y) ** 2 + (x_axis - center_x) ** 2)
    max_radius = max(rows, columns) / 2.0
    base = np.clip(255 - (radius / max_radius * 220), 0, 255)

    frames: list[np.ndarray] = []
    for index in range(frame_count):
        phase = index / max(frame_count - 1, 1)
        ring = np.sin(radius / 2.0 + phase * np.pi * 2.0) * 28.0
        catheter_shadow = ((x_axis - center_x) > 0) & (
            np.abs(y_axis - center_y) < rows * 0.08
        )
        frame = base + ring + phase * 20.0
        frame = np.where(catheter_shadow, frame * 0.45, frame)
        frames.append(np.clip(frame, 0, 255).astype(np.uint8))
    return np.stack(frames)


def create_synthetic_dicom(
    output_path: PathLike,
    frames: int = 24,
    rows: int = 128,
    columns: int = 128,
    fps: float = 20.0,
) -> Path:
    if frames <= 0:
        raise ValueError("frames must be greater than zero")
    if rows <= 0 or columns <= 0:
        raise ValueError("rows and columns must be greater than zero")
    if fps <= 0:
        raise ValueError("fps must be greater than zero")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pixel_frames = _synthetic_frames(frames, rows, columns)

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

    dataset = FileDataset(str(output), {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.Modality = "US"
    dataset.Manufacturer = "IVUS Tools"
    dataset.ManufacturerModelName = "Synthetic-IVUS-Generator"
    dataset.StudyDate = "20260624"
    dataset.StudyTime = "120000"
    dataset.InstitutionName = "Synthetic IVUS Lab"
    dataset.PatientID = "SYNTHETIC"
    dataset.Rows = rows
    dataset.Columns = columns
    dataset.NumberOfFrames = str(frames)
    dataset.FrameTime = 1000.0 / fps
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.PixelData = pixel_frames.tobytes()
    dataset.save_as(output, enforce_file_format=True)
    return output


@click.command()
@click.option(
    "-o", "--output", "output_path", required=True, type=click.Path(path_type=Path)
)
@click.option("--frames", "frame_count", default=24, show_default=True, type=int)
@click.option("--rows", default=128, show_default=True, type=int)
@click.option("--columns", default=128, show_default=True, type=int)
@click.option("--fps", default=20.0, show_default=True, type=float)
def cli(
    output_path: Path, frame_count: int, rows: int, columns: int, fps: float
) -> None:
    path = create_synthetic_dicom(output_path, frame_count, rows, columns, fps)
    click.echo(f"Created synthetic IVUS DICOM: {path}")


if __name__ == "__main__":
    cli()
