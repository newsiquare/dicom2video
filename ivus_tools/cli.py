from __future__ import annotations

import json
from typing import Any

import click


def echo_summary(report: dict[str, Any]) -> None:
    click.echo(json.dumps(report, indent=2, sort_keys=True))
