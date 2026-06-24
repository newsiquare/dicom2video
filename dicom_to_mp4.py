from __future__ import annotations

from pathlib import Path

import click

from ivus_tools.batch import batch_convert_dicom_to_mp4
from ivus_tools.cli import echo_summary
from ivus_tools.conversion import convert_dicom_to_mp4


@click.command()
@click.option(
    "-i", "--input", "input_path", required=True, type=click.Path(path_type=Path)
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output MP4 path. Defaults to outputs/mp4/<input_stem>.mp4.",
)
@click.option(
    "--fps", type=float, default=None, help="Override DICOM-derived frame rate."
)
@click.option("--codec", default="mp4v", show_default=True, help="OpenCV fourcc codec.")
@click.option("--no-progress", is_flag=True, help="Disable progress bar output.")
@click.option(
    "--no-sidecar", is_flag=True, help="Disable sidecar metadata JSON output."
)
@click.option("--no-embed-metadata", is_flag=True, help="Skip MP4 metadata embedding.")
@click.option("--report", "report_path", type=click.Path(path_type=Path), default=None)
@click.option(
    "--no-report", is_flag=True, help="Disable conversion report JSON output."
)
def cli(
    input_path: Path,
    output_path: Path | None,
    fps: float | None,
    codec: str,
    no_progress: bool,
    no_sidecar: bool,
    no_embed_metadata: bool,
    report_path: Path | None,
    no_report: bool,
) -> None:
    resolved_output_path = (
        output_path or Path("outputs") / "mp4" / f"{input_path.stem}.mp4"
    )
    try:
        if input_path.is_dir():
            report = batch_convert_dicom_to_mp4(
                input_path,
                output_path or Path("outputs") / "mp4",
                fps=fps,
                codec=codec,
                recursive=True,
                show_progress=not no_progress,
                write_sidecar=not no_sidecar,
                embed_metadata=not no_embed_metadata,
                report_path=report_path,
                write_report=not no_report,
            )
        else:
            report = convert_dicom_to_mp4(
                input_path,
                resolved_output_path,
                fps=fps,
                codec=codec,
                show_progress=not no_progress,
                write_sidecar=not no_sidecar,
                embed_metadata=not no_embed_metadata,
                report_path=report_path,
                write_report=not no_report,
            )
    except (
        Exception
    ) as error:  # noqa: BLE001 - CLI converts exceptions to user messages.
        raise click.ClickException(str(error)) from error
    echo_summary(report)


if __name__ == "__main__":
    cli()
