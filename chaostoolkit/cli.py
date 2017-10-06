# -*- coding: utf-8 -*-
import io
import json
import logging
import os
import sys

import click
import logzero
from logzero import logger

from chaoslib.exceptions import ChaosException
from chaoslib.experiment import ensure_experiment_is_valid, load_experiment,\
    run_experiment
from chaoslib.types import Experiment

from chaostoolkit import __version__

__all__ = ["cli"]


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', is_flag=True, help='Display debug level traces')
def cli(verbose: bool = False):
    if verbose:
        logzero.loglevel(logging.DEBUG)
        fmt = "%(color)s[%(asctime)s %(levelname)s] "\
              "[%(module)s:%(lineno)d]%(end_color)s %(message)s"
    else:
        logzero.loglevel(logging.INFO)
        fmt = "%(color)s[%(asctime)s %(levelname)s]%(end_color)s %(message)s"

    logzero.setup_default_logger(
        formatter=logzero.LogFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S"))


@cli.command()
@click.option('--report-path', default="./chaos-report.json",
              help='Path where to save the report from the plan execution')
@click.option('--dry', is_flag=True,
              help='Run the plan using the noop backend')
@click.option('--no-validation', is_flag=True,
              help='Do not perform validation of the experiment')
@click.argument('path', type=click.Path(exists=True))
def run(path: str, report_path: str = "./chaos-report.json", dry: bool = False,
        no_validation: bool = False):
    """Run the plan given at PATH."""
    experiment = load_experiment(click.format_filename(path))
    if not no_validation:
        try:
            ensure_experiment_is_valid(experiment)
        except ChaosException as x:
            logger.error(str(x))
            logger.debug(x)
            sys.exit(1)

    journal = run_experiment(experiment)

    with io.open(report_path, "w") as r:
        json.dump(journal, r, indent=2, ensure_ascii=False)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def validate(path: str):
    """Validate un the experiment at PATH."""
    experiment = load_experiment(click.format_filename(path))
    try:
        ensure_experiment_is_valid(experiment)
        logger.info("experiment syntax and semantic look valid")
    except ChaosException as x:
        logger.error(str(x))
        sys.exit(1)
