import json
import logging
from typing import Any, Dict, List, Optional

import click
from chaoslib import __version__ as chaoslib_version
from chaoslib import convert_vars, merge_vars
from chaoslib.control import load_global_controls
from chaoslib.exceptions import ChaosException, InvalidSource
from chaoslib.experiment import ensure_experiment_is_valid, run_experiment
from chaoslib.loader import load_experiment
from chaoslib.notification import (
    RunFlowEvent,
    notify,
)
from chaoslib.settings import (
    load_settings,
)
from chaoslib.types import (
    Dry,
    Journal,
    Schedule,
)

from chaostoolkit import encoder
from chaostoolkit.check import (
    check_hypothesis_strategy_spelling,
)

DEFAULT_ROLLBACK_STRATEGY = "default"
DEFAULT_HYPOTHESIS_STRATEGY = "default"
logger = logging.getLogger("chaostoolkit")


def validate_vars(
    ctx: click.Context, param: click.Option, value: List[str]
) -> Dict[str, Any]:
    """
    Process all `--var key=value` and return a dictionary of them with the
    value converted to the appropriate type.
    """
    try:
        return convert_vars(value)
    except ValueError as x:
        raise click.BadParameter(str(x))


@click.command()
@click.option(
    "--journal-path",
    default="./journal.json",
    help="Path where to save the journal from the execution.",
)
@click.option(
    "--dry",
    type=click.Choice(["probes", "actions", "activities", "pause"]),
    show_default=False,
    help="Run the experiment without executing the chosen strategy.",
)
@click.option(
    "--no-validation",
    is_flag=True,
    help="Do not validate the experiment before running.",
)
@click.option(
    "--no-verify-tls", is_flag=True, help="Do not verify TLS certificate."
)
@click.option(
    "--rollback-strategy",
    show_default=False,
    help="Rollback runtime strategy. Default is to never play them "
    "on interruption or failed hypothesis.",
    type=click.Choice(["default", "always", "never", "deviated"]),
)
@click.option(
    "--var",
    multiple=True,
    callback=validate_vars,
    help="Specify substitution values for configuration only. Can "
    "be provided multiple times. The pattern must be "
    "key=value or key:type=value. In that latter case, the "
    "value will be casted as the specified type. Supported "
    "types are: int, float, bytes. No type specified means "
    "a utf-8 decoded string.",
)
@click.option(
    "--var-file",
    multiple=True,
    type=click.Path(exists=True),
    help="Specify files that contain configuration and secret "
    "substitution values. Either as a json/yaml payload where "
    "each key has a value mapping to a configuration entry. "
    "Or a .env file defining environment variables. "
    "Can be provided multiple times.",
)
@click.option(
    "--control-file",
    multiple=True,
    type=click.Path(exists=True),
    help="Specify files that can contain controls definitions "
    "that will be loaded as global controls at startup. So before "
    "the experiment was even loaded.",
)
@click.option(
    "--hypothesis-strategy",
    type=click.Choice(
        [
            "default",
            "before-method-only",
            "after-method-only",
            "during-method-only",
            "continuously",
            "continously",
        ],
        case_sensitive=True,
    ),
    help="Strategy to execute the hypothesis during the run.",
)
@click.option(
    "--hypothesis-frequency",
    default=1.0,
    type=float,
    help="Pace at which running the hypothesis. "
    "Only applies when strategy is either: "
    "during-method-only or continuously",
)
@click.option(
    "--fail-fast",
    is_flag=True,
    default=False,
    help="When running in the during-method-only or continuous "
    "strategies, indicate the hypothesis can fail the "
    "experiment as soon as it deviates once. Otherwise, keeps "
    "running until the end of the experiment.",
)
@click.argument("source")
@click.pass_context
def run(
    ctx: click.Context,
    source: str,
    journal_path: str = "./journal.json",
    dry: Optional[str] = None,
    no_validation: bool = False,
    no_exit: bool = False,
    no_verify_tls: bool = False,
    rollback_strategy: str = None,
    var: Dict[str, Any] = None,
    var_file: List[str] = None,
    control_file: List[str] = None,
    hypothesis_strategy: Optional[str] = None,
    hypothesis_frequency: float = 1.0,
    fail_fast: bool = False,
) -> Journal:
    """Run the experiment loaded from SOURCE, either a local file or a
    HTTP resource. SOURCE can be formatted as JSON or YAML."""
    settings = load_settings(ctx.obj["settings_path"]) or {}
    has_deviated = False
    has_failed = False

    experiment_vars = merge_vars(var, var_file)

    try:
        load_global_controls(settings, control_file)
    except TypeError:
        logger.debug("Failed to load controls", exc_info=True)
        logger.warning(
            "Passing control files only work with chaostoolkit-lib 1.33+, you "
            f"run {chaoslib_version}. The control files will be ignored."
            "Please upgrade with `pip install -U chaostoolkit-lib`"
        )
        load_global_controls(settings)

    try:
        experiment = load_experiment(
            source, settings, verify_tls=not no_verify_tls
        )
    except InvalidSource as x:
        logger.error(str(x))
        logger.debug(x)
        ctx.exit(1)

    notify(settings, RunFlowEvent.RunStarted, experiment)

    if not no_validation:
        try:
            ensure_experiment_is_valid(experiment)
        except ChaosException as x:
            logger.error(str(x))
            logger.debug(x)
            ctx.exit(1)

    experiment["dry"] = Dry.from_string(dry)

    # we first check the settings for the runtime settings
    runtime = settings.setdefault("runtime", {})
    runtime.setdefault("rollbacks", {}).setdefault(
        "strategy", DEFAULT_ROLLBACK_STRATEGY
    )
    runtime.setdefault("hypothesis", {}).setdefault(
        "strategy", DEFAULT_HYPOTHESIS_STRATEGY
    )

    # we allow to override via the experiment
    experiment_runtime = experiment.get("runtime")
    if experiment_runtime:
        runtime["rollbacks"]["strategy"] = experiment_runtime.get(
            "rollbacks", {}
        ).get("strategy", DEFAULT_ROLLBACK_STRATEGY)
        runtime["hypothesis"]["strategy"] = experiment_runtime.get(
            "hypothesis", {}
        ).get("strategy", DEFAULT_HYPOTHESIS_STRATEGY)

    # finally the cli takes precedence over both of the above
    if hypothesis_strategy is None:
        hypothesis_strategy = runtime["hypothesis"]["strategy"]
    else:
        runtime["hypothesis"]["strategy"] = hypothesis_strategy

    if rollback_strategy is None:
        rollback_strategy = runtime["rollbacks"]["strategy"]
    else:
        runtime["rollbacks"]["strategy"] = rollback_strategy

    logger.debug(
        f"Runtime strategies: hypothesis - {hypothesis_strategy} "
        f"/ rollbacks - {rollback_strategy}"
    )

    ssh_strategy = check_hypothesis_strategy_spelling(hypothesis_strategy)

    schedule = Schedule(
        continuous_hypothesis_frequency=hypothesis_frequency,
        fail_fast=fail_fast,
    )

    journal = run_experiment(
        experiment,
        settings=settings,
        strategy=ssh_strategy,
        schedule=schedule,
        experiment_vars=experiment_vars,
    )
    has_deviated = journal.get("deviated", False)
    has_failed = journal["status"] != "completed"
    if "dry" in journal["experiment"]:
        journal["experiment"]["dry"] = dry
    with open(journal_path, "w") as r:
        json.dump(journal, r, indent=2, ensure_ascii=False, default=encoder)

    if journal["status"] == "completed":
        notify(settings, RunFlowEvent.RunCompleted, journal)
    elif has_failed:
        notify(settings, RunFlowEvent.RunFailed, journal)

    if has_deviated:
        notify(settings, RunFlowEvent.RunDeviated, journal)

    if (has_failed or has_deviated) and not no_exit:
        ctx.exit(1)

    return journal
