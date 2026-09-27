import contextlib
import logging
import sys

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

from chaostoolkit import agent
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
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["text", "agent"]),
    default="text",
    show_default=True,
    help="Output on stdout. With agent, a single JSON report is written. "
    "Only the first error found is reported.",
)
@click.argument("source")
@click.pass_context
def validate(
    ctx: click.Context,
    source: str,
    no_verify_tls: bool = False,
    output_format: str = "text",
) -> Experiment:
    """Validate the experiment at SOURCE."""
    settings = load_settings(ctx.obj["settings_path"])
    for_agent = output_format == "agent"

    try:
        experiment = load_experiment(
            source,
            settings,
            verify_tls=not no_verify_tls,
        )
    except InvalidSource as x:
        logger.error(str(x))
        logger.debug(x)
        if for_agent:
            agent.emit(agent.validate_report(source, stage="load", exc=x))
        ctx.exit(1)

    try:
        runtime = get_python_runtime_info(experiment)
        if runtime is not None and not in_runtime_child():
            runtime_kwargs = {"capture_stdout": True} if for_agent else {}
            with supervised_runtime(
                runtime,
                argv=ctx.meta[RUNTIME_ARGUMENTS_META_KEY],
                invocation_cwd=ctx.meta[RUNTIME_INVOCATION_CWD_META_KEY],
                **runtime_kwargs,
            ) as child:
                if for_agent:
                    exit_code = agent.relay_child_report(
                        child, "validate", source
                    )
                else:
                    exit_code = child.wait()
            ctx.exit(exit_code)
    except PythonRuntimeError as x:
        logger.error(str(x))
        logger.debug(x)
        if for_agent:
            agent.emit(
                agent.validate_report(
                    source, experiment, stage="runtime", exc=x
                )
            )
        ctx.exit(1)

    return _execute_validate(
        ctx, experiment, settings, source=source, for_agent=for_agent
    )


def _execute_validate(
    ctx: click.Context,
    experiment: Experiment,
    settings: Settings | None,
    source: str = "",
    for_agent: bool = False,
) -> Experiment:
    """Validate an already-loaded experiment in the selected runtime."""

    try:
        notify(settings, ValidateFlowEvent.ValidateStarted, experiment)
        # validation imports activity modules: keep stdout for the report
        quiet = (
            contextlib.redirect_stdout(sys.stderr)
            if for_agent
            else contextlib.nullcontext()
        )
        with quiet:
            ensure_experiment_is_valid(experiment)
        notify(settings, ValidateFlowEvent.ValidateCompleted, experiment)
        logger.info("experiment syntax and semantic look valid")
    except ChaosException as x:
        notify(settings, ValidateFlowEvent.ValidateFailed, experiment, x)
        logger.error(str(x))
        logger.debug(x)
        if for_agent:
            agent.emit(
                agent.validate_report(
                    source, experiment, stage="validation", exc=x
                )
            )
        ctx.exit(1)

    if for_agent:
        agent.emit(agent.validate_report(source, experiment))

    return experiment
