from __future__ import annotations

from pathlib import Path

import click

from ivus_tools.batch import batch_convert_dicom_to_mp4
from ivus_tools.cli import echo_summary


@click.command()
@click.option("--input-dir", required=True, type=click.Path(path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(path_type=Path))
@click.option(
    "--fps", type=float, default=None, help="Override DICOM-derived frame rate."
)
@click.option("--codec", default="mp4v", show_default=True, help="OpenCV fourcc codec.")
@click.option(
    "--recursive", is_flag=True, help="Convert DICOM files in nested directories."
)
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
    input_dir: Path,
    output_dir: Path,
    fps: float | None,
    codec: str,
    recursive: bool,
    no_progress: bool,
    no_sidecar: bool,
    no_embed_metadata: bool,
    report_path: Path | None,
    no_report: bool,
) -> None:
    try:
        report = batch_convert_dicom_to_mp4(
            input_dir,
            output_dir,
            fps=fps,
            codec=codec,
            recursive=recursive,
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
