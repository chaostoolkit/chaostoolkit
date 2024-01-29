import logging

import click

from chaoslib.exceptions import ChaosException, InvalidSource
from chaoslib.experiment import ensure_experiment_is_valid
from chaoslib.loader import load_experiment
from chaoslib.notification import (
    ValidateFlowEvent,
    notify,
)
from chaoslib.types import Experiment
from chaoslib.settings import load_settings

logger = logging.getLogger("chaostoolkit")


@click.command()
@click.option(
    "--no-verify-tls", is_flag=True, help="Do not verify TLS certificate."
)
@click.argument("source")
@click.pass_context
def validate(
    ctx: click.Context, source: str, no_verify_tls: bool = False
) -> Experiment:
    """Validate the experiment at SOURCE."""
    settings = load_settings(ctx.obj["settings_path"])

    try:
        experiment = load_experiment(
            source, settings, verify_tls=not no_verify_tls
        )
    except InvalidSource as x:
        logger.error(str(x))
        logger.debug(x)
        ctx.exit(1)

    try:
        notify(settings, ValidateFlowEvent.ValidateStarted, experiment)
        ensure_experiment_is_valid(experiment)
        notify(settings, ValidateFlowEvent.ValidateCompleted, experiment)
        logger.info("experiment syntax and semantic look valid")
    except ChaosException as x:
        notify(settings, ValidateFlowEvent.ValidateFailed, experiment, x)
        logger.error(str(x))
        logger.debug(x)
        ctx.exit(1)

    return experiment
