import logging

import click
from chaoslib.exceptions import ChaosException, InvalidSource
from chaoslib.experiment import ensure_experiment_is_valid
from chaoslib.loader import load_experiment
from chaoslib.notification import (
    ValidateFlowEvent,
    notify,
)
from chaoslib.settings import load_settings
from chaoslib.types import Experiment, Settings

from chaostoolkit.runtime import (
    RUNTIME_ARGUMENTS_META_KEY,
    RUNTIME_INVOCATION_CWD_META_KEY,
    PythonRuntimeError,
    get_python_runtime_info,
    in_runtime_child,
    supervised_runtime,
)

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
            source,
            settings,
            verify_tls=not no_verify_tls,
        )
    except InvalidSource as x:
        logger.error(str(x))
        logger.debug(x)
        ctx.exit(1)

    try:
        runtime = get_python_runtime_info(experiment)
        if runtime is not None and not in_runtime_child():
            with supervised_runtime(
                runtime,
                argv=ctx.meta[RUNTIME_ARGUMENTS_META_KEY],
                invocation_cwd=ctx.meta[RUNTIME_INVOCATION_CWD_META_KEY],
            ) as child:
                exit_code = child.wait()
            ctx.exit(exit_code)
    except PythonRuntimeError as x:
        logger.error(str(x))
        logger.debug(x)
        ctx.exit(1)

    return _execute_validate(ctx, experiment, settings)


def _execute_validate(
    ctx: click.Context,
    experiment: Experiment,
    settings: Settings | None,
) -> Experiment:
    """Validate an already-loaded experiment in the selected runtime."""

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
