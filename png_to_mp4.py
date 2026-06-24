from __future__ import annotations

from pathlib import Path

import click

from ivus_tools.cli import echo_summary
from ivus_tools.conversion import convert_png_to_mp4


@click.command()
@click.option(
    "-i", "--input", "input_dir", required=True, type=click.Path(path_type=Path)
)
@click.option(
    "-o", "--output", "output_path", required=True, type=click.Path(path_type=Path)
)
@click.option(
    "--fps",
    default=30.0,
    show_default=True,
    type=float,
    help="Frame rate for PNG sequence.",
)
@click.option("--codec", default="mp4v", show_default=True, help="OpenCV fourcc codec.")
@click.option("--no-progress", is_flag=True, help="Disable progress bar output.")
@click.option("--report", "report_path", type=click.Path(path_type=Path), default=None)
@click.option(
    "--no-report", is_flag=True, help="Disable conversion report JSON output."
)
def cli(
    input_dir: Path,
    output_path: Path,
    fps: float,
    codec: str,
    no_progress: bool,
    report_path: Path | None,
    no_report: bool,
) -> None:
    try:
        report = convert_png_to_mp4(
            input_dir,
            output_path,
            fps=fps,
            codec=codec,
            show_progress=not no_progress,
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
