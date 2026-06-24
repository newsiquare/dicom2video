from __future__ import annotations

from pathlib import Path

import click

from ivus_tools.cli import echo_summary
from ivus_tools.conversion import export_dicom_to_png


@click.command()
@click.option(
    "-i", "--input", "input_path", required=True, type=click.Path(path_type=Path)
)
@click.option(
    "-o", "--output", "output_dir", required=True, type=click.Path(path_type=Path)
)
@click.option(
    "--digits", default=5, show_default=True, type=int, help="Zero-padding width."
)
@click.option("--no-progress", is_flag=True, help="Disable progress bar output.")
@click.option("--report", "report_path", type=click.Path(path_type=Path), default=None)
@click.option(
    "--no-report", is_flag=True, help="Disable conversion report JSON output."
)
def cli(
    input_path: Path,
    output_dir: Path,
    digits: int,
    no_progress: bool,
    report_path: Path | None,
    no_report: bool,
) -> None:
    try:
        report = export_dicom_to_png(
            input_path,
            output_dir,
            digits=digits,
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
