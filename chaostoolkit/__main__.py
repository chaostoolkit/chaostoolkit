# -*- coding: utf-8 -*-
import click

from chaostoolkit import __version__
from chaostoolkit.plan import run_plan


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@cli.command()
@click.option('--report-path',
              help='Path where to save the report from the plan execution')
@click.option('--dry', is_flag=True,
              help='Run the plan using the noop backend')
@click.argument('path', type=click.Path(exists=True))
def run(report_path: str, dry: bool, path: str):
    """Run the plan given at PATH and return the resulting report."""
    report = run_plan(click.format_filename(path), dry_run=dry)


if __name__ == '__main__':
    cli()
