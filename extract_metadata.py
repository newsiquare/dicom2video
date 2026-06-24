from __future__ import annotations

import json
from pathlib import Path

import click

from ivus_tools.dicom import load_dicom
from ivus_tools.metadata import extract_metadata
from ivus_tools.timing import resolve_fps


@click.command()
@click.option(
    "-i", "--input", "input_path", required=True, type=click.Path(path_type=Path)
)
@click.option(
    "-o", "--output", "output_path", type=click.Path(path_type=Path), default=None
)
def cli(input_path: Path, output_path: Path | None) -> None:
    try:
        dataset = load_dicom(input_path)
        metadata = extract_metadata(dataset, resolve_fps(dataset))
    except (
        Exception
    ) as error:  # noqa: BLE001 - CLI converts exceptions to user messages.
        raise click.ClickException(str(error)) from error

    text = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    if output_path is None:
        click.echo(text, nl=False)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text)
    click.echo(str(output_path))


if __name__ == "__main__":
    cli()
