# -*- coding: utf-8 -*-
import io
import json
import os
from typing import List
from typing import Any, Dict, List
import uuid

from chaoslib import __version__ as chaoslib_version, merge_vars, convert_vars
from chaoslib.control import load_global_controls
from chaoslib.exceptions import ChaosException, DiscoveryFailed, InvalidSource
from chaoslib.discovery import discover as disco
from chaoslib.discovery.discover import portable_type_name_to_python_type
from chaoslib.experiment import ensure_experiment_is_valid, run_experiment
from chaoslib.info import list_extensions
from chaoslib.loader import load_experiment
from chaoslib.notification import notify, DiscoverFlowEvent, InitFlowEvent, \
    RunFlowEvent, ValidateFlowEvent
from chaoslib.settings import load_settings, locate_settings_entry, \
    save_settings, CHAOSTOOLKIT_CONFIG_PATH
from chaoslib.types import Activity, Discovery, Experiment, Journal, \
    Schedule, Strategy
import click
from click_plugins import with_plugins
try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata
from logzero import logger
import yaml

from chaostoolkit import __version__, encoder
from chaostoolkit.check import check_newer_version
from chaostoolkit.logging import configure_logger


__all__ = ["cli"]


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', is_flag=True, help='Display debug level traces.')
@click.option('--no-version-check', is_flag=True,
              help='Do not search for an updated version of the chaostoolkit.')
@click.option('--change-dir',
              help='Change directory before running experiment.')
@click.option('--no-log-file', is_flag=True,
              help='Disable logging to file entirely.')
@click.option('--log-file', default="chaostoolkit.log", show_default=True,
              help="File path where to write the command's log.")
@click.option('--log-format', default="string", show_default=False,
              help="Console logging format: string, json.",
              type=click.Choice(['string', 'json']))
@click.option('--settings', default=CHAOSTOOLKIT_CONFIG_PATH,
              show_default=True, help="Path to the settings file.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool = False,
        no_version_check: bool = False, change_dir: str = None,
        no_log_file: bool = False, log_file: str = "chaostoolkit.log",
        log_format: str = "string", settings: str = CHAOSTOOLKIT_CONFIG_PATH):

    if no_log_file:
        configure_logger(
            verbose=verbose, log_format=log_format,
            context_id=str(uuid.uuid4()))
    else:
        configure_logger(
            verbose=verbose, log_file=log_file, log_format=log_format,
            context_id=str(uuid.uuid4()))

    subcommand = ctx.invoked_subcommand

    # make it nicer for going through the log file
    logger.debug("#" * 79)
    logger.debug("Running command '{}'".format(subcommand))

    ctx.obj = {}
    ctx.obj["settings_path"] = click.format_filename(settings)
    logger.debug("Using settings file '{}'".format(ctx.obj["settings_path"]))

    if not no_version_check:
        check_newer_version(command=subcommand)

    if change_dir:
        logger.warning("Moving to {d}".format(d=change_dir))
        os.chdir(change_dir)


def validate_vars(ctx: click.Context, param: click.Option,
                  value: List[str]) -> Dict[str, Any]:
    """
    Process all `--var key=value` and return a dictionnary of them with the
    value converted to the appropriate type.
    """
    try:
        convert_vars(value)
    except ValueError as x:
        raise click.BadParameter(str(x))


@cli.command()
@click.option('--journal-path', default="./journal.json",
              help='Path where to save the journal from the execution.')
@click.option('--dry', is_flag=True,
              help='Run the experiment without executing activities.')
@click.option('--no-validation', is_flag=True,
              help='Do not validate the experiment before running.')
@click.option('--no-verify-tls', is_flag=True,
              help='Do not verify TLS certificate.')
@click.option('--rollback-strategy', default="default", show_default=False,
              help="Rollback runtime strategy. Default is to never play them "
                   "on interruption or failed hypothesis.",
              type=click.Choice(['default', 'always', 'never', 'deviated']))
@click.option('--var', multiple=True, callback=validate_vars,
              help='Specify substitution values for configuration only. Can '
                   'be provided multiple times. The pattern must be '
                   'key=value or key:type=value. In that latter case, the '
                   'value will be casted as the specified type. Supported '
                   'types are: int, float, bytes. No type specified means '
                   'a utf-8 decoded string.')
@click.option('--var-file', multiple=True, type=click.Path(exists=True),
              help='Specify files that contain configuration and secret '
                   'substitution values. Either as a json/yaml payload where '
                   'each key has a value mapping to a configuration entry. '
                   'Or a .env file defining environment variables. '
                   'Can be provided multiple times.')
@click.option('--hypothesis-strategy', default="default",
              type=click.Choice([
                  "default", "before-method-only", "after-method-only",
                  "during-method-only", "continously"
              ], case_sensitive=True),
              help='Strategy to execute the hypothesis during the run.')
@click.option('--hypothesis-frequency', default=1.0, type=float,
              help='Pace at which running the hypothesis. '
                   'Only applies when strategy is either: '
                   'during-method-only or continously')
@click.option('--fail-fast', is_flag=True, default=False,
              help='When running in the during-method-onlyt or continous '
                   'strategies, indicate the hypothesis can fail the '
                   'experiment as soon as it deviates once. Otherwise, keeps '
                   'running until the end of the experiment.')
@click.argument('source')
@click.pass_context
def run(ctx: click.Context, source: str, journal_path: str = "./journal.json",
        dry: bool = False, no_validation: bool = False,
        no_exit: bool = False, no_verify_tls: bool = False,
        rollback_strategy: str = "default",
        var: Dict[str, Any] = None, var_file: List[str] = None,
        hypothesis_strategy: str = "default",
        hypothesis_frequency: float = 1.0, fail_fast: bool = False) -> Journal:
    """Run the experiment loaded from SOURCE, either a local file or a
       HTTP resource. SOURCE can be formatted as JSON or YAML."""
    settings = load_settings(ctx.obj["settings_path"]) or {}
    has_deviated = False
    has_failed = False

    experiment_vars = merge_vars(var, var_file)

    load_global_controls(settings)

    try:
        experiment = load_experiment(
            source, settings, verify_tls=not no_verify_tls)
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

    experiment["dry"] = dry
    settings.setdefault(
        "runtime", {}).setdefault("rollbacks", {}).setdefault(
            "strategy", rollback_strategy)
    hypothesis_strategy = Strategy.from_string(hypothesis_strategy)
    schedule = Schedule(
        continous_hypothesis_frequency=hypothesis_frequency,
        fail_fast=fail_fast)

    journal = run_experiment(
        experiment, settings=settings, strategy=hypothesis_strategy,
        schedule=schedule)
    has_deviated = journal.get("deviated", False)
    has_failed = journal["status"] != "completed"

    with io.open(journal_path, "w") as r:
        json.dump(
            journal, r, indent=2, ensure_ascii=False, default=encoder)

    if journal["status"] == "completed":
        notify(settings, RunFlowEvent.RunCompleted, journal)
    elif has_failed:
        notify(settings, RunFlowEvent.RunFailed, journal)

        if has_deviated:
            notify(settings, RunFlowEvent.RunDeviated, journal)

    if (has_failed or has_deviated) and not no_exit:
        ctx.exit(1)

    return journal


@cli.command()
@click.option('--no-verify-tls', is_flag=True,
              help='Do not verify TLS certificate.')
@click.argument('source')
@click.pass_context
def validate(ctx: click.Context, source: str,
             no_verify_tls: bool = False) -> Experiment:
    """Validate the experiment at SOURCE."""
    settings = load_settings(ctx.obj["settings_path"])

    try:
        experiment = load_experiment(
            source, settings, verify_tls=not no_verify_tls)
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


@cli.group()
def settings():
    """
    Read, write or remove from your settings file.
    """
    pass


cli.add_command(settings)


@settings.command('show')
@click.option('--format', 'fmt', default="yaml", show_default=False,
              help="Output format.",
              type=click.Choice(['json', 'yaml']))
@click.pass_context
def show_settings(ctx: click.Context, fmt: str = "json"):
    """
    Show the entire content of the settings file.

    Be aware this will not obfuscate secret data.
    """
    if not os.path.isfile(ctx.obj["settings_path"]):
        click.abort(
            "No settings file found at {}".format(ctx.obj["settings_path"]))

    settings = load_settings(ctx.obj["settings_path"]) or {}
    if fmt == "json":
        click.echo(json.dumps(settings, indent=2))
    elif fmt == "yaml":
        click.echo(yaml.dump(settings, indent=2))


settings.add_command(show_settings)


@settings.command('set')
@click.argument('key', nargs=1)
@click.argument('value', nargs=1)
@click.pass_context
def set_settings_value(ctx: click.Context, key: str, value: str = None):
    """
    Set a settings value.
    The value must be a valid JSON string so that it can be interpreted
    with the appropriate type.

    The key must be dotted path to its location in the settings file.
    """
    if not os.path.isfile(ctx.obj["settings_path"]):
        ctx.exit(1)

    settings = load_settings(ctx.obj["settings_path"]) or {}
    item = locate_settings_entry(settings, key)
    if not item:
        ctx.exit(1)
    parent, entry, key_tail, index = item

    value = json.loads(value)
    if key_tail is not None:
        parent[key_tail] = value
    elif index is not None:
        parent[index] = value
    save_settings(settings, ctx.obj["settings_path"])


settings.add_command(set_settings_value)


@settings.command('remove')
@click.argument('key', nargs=1)
@click.pass_context
def remove_settings_value(ctx: click.Context, key: str):
    """
    Remove a settings key and its children.

    The key must be dotted path to its location in the settings file.
    """
    if not os.path.isfile(ctx.obj["settings_path"]):
        ctx.exit(1)

    settings = load_settings(ctx.obj["settings_path"]) or {}
    item = locate_settings_entry(settings, key)
    if not item:
        ctx.exit(1)
    parent, entry, key_tail, index = item

    if key_tail is not None:
        parent.pop(key_tail, None)
    elif index is not None:
        parent.remove(parent[index])
    save_settings(settings, ctx.obj["settings_path"])


settings.add_command(remove_settings_value)


@settings.command('get')
@click.option('--format', 'fmt', default="yaml", show_default=False,
              help="Output format.",
              type=click.Choice(['string', 'json', 'yaml']))
@click.argument('key', nargs=1)
@click.pass_context
def get_settings_value(ctx: click.Context, key: str, fmt: str = "json"):
    """
    Show a settings value.

    The key must be dotted path to its location in the settings file.
    """
    if not os.path.isfile(ctx.obj["settings_path"]):
        ctx.exit(1)

    settings = load_settings(ctx.obj["settings_path"]) or {}
    item = locate_settings_entry(settings, key)
    if not item:
        ctx.exit(1)
    parent, entry, key_tail, index = item

    if fmt == "json":
        click.echo(json.dumps(entry, indent=2))
    elif fmt == "string":
        click.echo(str(entry))
    elif fmt == "yaml":
        click.echo(yaml.dump(entry, indent=2))


settings.add_command(get_settings_value)


@cli.command()
@click.argument('target',
                type=click.Choice(['core', 'settings', 'extensions']),
                metavar="TARGET")
@click.pass_context
def info(ctx: click.Context, target: str):
    """Display information about the Chaos Toolkit environment.

    Available targets are:

    * core: display the information about your version of the Chaos Toolkit

    * extensions: display the list of installed extensions and plugins

    * settings: display your current full settings
    """
    if target not in ["core", "settings", "extensions"]:
        raise click.BadArgumentUsage("Invalid target")

    if target == "core":
        fmt = "{:<20}{:<10}"
        click.secho(
            fmt.format("NAME", "VERSION"),
            fg='bright_blue')
        click.echo(fmt.format("CLI", __version__))
        click.echo(fmt.format("Core library", chaoslib_version))
    elif target == "extensions":
        fmt = "{:<40}{:<10}{:30}{:50}"
        click.secho(
            fmt.format("NAME", "VERSION", "LICENSE", "DESCRIPTION"),
            fg='bright_blue')
        extensions = list_extensions()
        for extension in extensions:
            summary = extension.summary.replace(
                "Chaos Toolkit Extension for ", "")[:50]
            click.echo(
                fmt.format(
                    extension.name, extension.version, extension.license,
                    summary))
    elif target == "settings":
        settings_path = ctx.obj["settings_path"]
        if not os.path.isfile(settings_path):
            click.echo("No settings file found at {}".format(settings_path))
            return

        with open(settings_path) as f:
            click.echo(f.read())


@cli.command()
@click.option('--no-system-info', is_flag=True,
              help='Do not discover system information.')
@click.option('--no-install', is_flag=True,
              help='Assume package already in PYTHONPATH.')
@click.option('--discovery-path', default="./discovery.json",
              help='Path where to save the the discovery outcome.',
              show_default=True)
@click.argument('package')
@click.pass_context
def discover(ctx: click.Context, package: str,
             discovery_path: str = "./discovery.json",
             no_system_info: bool = False,
             no_install: bool = False) -> Discovery:
    """Discover capabilities and experiments."""
    settings = load_settings(ctx.obj["settings_path"])
    try:
        notify(settings, DiscoverFlowEvent.DiscoverStarted, package)
        discovery = disco(
            package_name=package, discover_system=not no_system_info,
            download_and_install=not no_install)
    except DiscoveryFailed as err:
        notify(settings, DiscoverFlowEvent.DiscoverFailed, package, err)
        logger.debug("Failed to discover {}".format(package), exc_info=err)
        logger.fatal(str(err))
        return

    with open(discovery_path, "w") as d:
        d.write(json.dumps(discovery, indent=2, default=encoder))
    logger.info("Discovery outcome saved in {p}".format(
        p=discovery_path))

    notify(settings, DiscoverFlowEvent.DiscoverCompleted, discovery)
    return discovery


@cli.command()
@click.option('--discovery-path', default="./discovery.json",
              help='Path to the discovery outcome.',
              show_default=True, type=click.Path(exists=False))
@click.option('--experiment-path', default="./experiment.json",
              type=click.Path(exists=False),
              help='Path where to save the experiment (.yaml or .json)',
              show_default=True)
@click.pass_context
def init(ctx: click.Context, discovery_path: str = "./discovery.json",
         experiment_path: str = "./experiment.json") -> Experiment:
    """Initialize a new experiment from discovered capabilities."""
    settings = load_settings(ctx.obj["settings_path"])
    notify(settings, InitFlowEvent.InitStarted)
    click.secho(
        "You are about to create an experiment.\n"
        "This wizard will walk you through each step so that you can build\n"
        "the best experiment for your needs.\n"
        "\n"
        "An experiment is made up of three elements:\n"
        "- a steady-state hypothesis [OPTIONAL]\n"
        "- an experimental method\n"
        "- a set of rollback activities [OPTIONAL]\n"
        "\n"
        "Only the method is required. Also your experiment will\n"
        "not run unless you define at least one activity (probe or action)\n"
        "within it",
        fg="blue")

    discovery = None
    if discovery_path and os.path.exists(discovery_path):
        with open(discovery_path) as d:
            discovery = json.loads(d.read())
    else:
        click.echo("No discovery was found, let's create an empty experiment")

    base_experiment = {
        "version": "1.0.0",
        "title": "",
        "description": "N/A",
        "tags": []
    }

    s = click.style

    title = click.prompt(s("Experiment's title", fg='green'), type=str)
    base_experiment["title"] = title

    click.secho(
        "\nA steady state hypothesis defines what 'normality' "
        "looks like in your system\n"
        "The steady state hypothesis is a collection of "
        "conditions that are used,\n"
        "at the beginning of an experiment, to decide if the "
        "system is in a recognised\n"
        "'normal' state. The steady state conditions are then "
        "used again when your experiment\n"
        " is complete to detect where your system may have "
        "deviated in an interesting,\n"
        "weakness-detecting way\n"
        "\n"
        "Initially you may not know what your steady state "
        "hypothesis is\n"
        "and so instead you might create an experiment "
        "without one\n"
        "This is why the stead state hypothesis is optional.", fg="blue")
    m = s('Do you want to define a steady state hypothesis now?',
          dim=True)
    if click.confirm(m):
        hypo = {}

        title = click.prompt(s("Hypothesis's title", fg='green'), type=str)
        hypo["title"] = title
        hypo["probes"] = []

        if discovery:
            activities = []
            for a in discovery["activities"]:
                if a["type"] == "probe":
                    activities.append((a["name"], a))

            click.secho(
                "\nYou may now define probes that will determine\n"
                "the steady-state of your system.",
                fg="blue")
            add_activities(activities, hypo["probes"], with_tolerance=True)

        base_experiment["steady-state-hypothesis"] = hypo

    if discovery:
        base_experiment["method"] = []
        click.secho(
            "\nAn experiment's method contains actions "
            "and probes. Actions\n"
            "vary real-world events in your system to determine if your\n"
            "steady-state hypothesis is maintained when those events occur.\n"
            "\n"
            "An experimental method can also contain probes to gather"
            " additional\n"
            "information about your system as your method is executed.",
            fg="blue")

        m = s('Do you want to define an experimental method?', dim=True)
        if click.confirm(m):
            activities = [(a["name"], a) for a in discovery["activities"]]
            add_activities(activities, base_experiment["method"])

        click.secho(
            "\nAn experiment may optionally define a set of remedial"
            " actions\nthat are used to rollback the system to a given"
            " state.",
            fg="blue")
        m = s('Do you want to add some rollbacks now?', dim=True)
        if click.confirm(m):
            rollbacks = []
            activities = []
            for a in discovery["activities"]:
                if a["type"] == "action":
                    activities.append((a["name"], a))
            add_activities(activities, rollbacks)
            base_experiment["rollbacks"] = rollbacks

    if is_yaml(experiment_path):
        output = yaml.dump(base_experiment,
                           indent=4,
                           default_flow_style=False,
                           sort_keys=False)
    else:
        output = json.dumps(base_experiment, indent=4, default=encoder)

    with open(experiment_path, "w") as e:
        e.write(output)

    click.echo(
        "\nExperiment created and saved in '{e}'".format(e=experiment_path))

    notify(settings, InitFlowEvent.InitCompleted, base_experiment)
    return base_experiment


# keep this after the cli group declaration for plugins to override defaults
with_plugins(
    importlib_metadata.entry_points().get('chaostoolkit.cli_plugins'))(cli)


def is_yaml(experiment_path: str) -> bool:
    _, ext = os.path.splitext(experiment_path)
    return ext.lower() in (".yaml", ".yml")


def add_activities(activities: List[Activity], pool: List[Activity],
                   with_tolerance: bool = False):
    """
    Add activities to the given pool.
    """
    base_activity = {
        "type": None,
        "name": None,
        "provider": {
            "type": "python",
            "module": None,
            "func": None,
            "arguments": {}
        }
    }

    s = click.style
    echo = click.echo
    if len(activities) > 20:
        echo = click.echo_via_pager

    click.echo(s(
        'Add an activity', fg='green'))
    echo("\n".join([
        "{i}) {t}".format(
            i=idx+1, t=name) for (idx, (name, a)) in enumerate(
                activities)]))
    activity_index = click.prompt(s(
        "Activity (0 to escape)", fg='green'), type=int)
    if not activity_index:
        return

    activity_index = activity_index - 1
    if activity_index > len(activities):
        click.secho("Please pick up a valid activity", fg="red", err=True)
        add_activities(activities, pool)
        return

    selected = activities[activity_index][1]
    selected_doc = selected.get("doc")
    if selected_doc:
        click.secho("\n{}".format(selected_doc), fg="blue")
    m = s('Do you want to use this {a}?'.format(a=selected['type']), dim=True)
    if not click.confirm(m):
        m = s('Do you want to select another activity?', dim=True)
        if not click.confirm(m):
            return
        add_activities(activities, pool)

    activity = base_activity.copy()
    activity["name"] = selected["name"]
    activity["type"] = selected["type"]
    if with_tolerance:
        click.secho(
            "\nA steady-state probe requires a tolerance value, "
            "within which\n"
            "your system is in a reognised `normal` state.\n",
            fg="blue")
        tolerance_value = click.prompt(
            s("What is the tolerance for this probe?", fg='green'))
        activity["tolerance"] = tolerance_value
    activity["provider"] = {"type": "python"}
    activity["provider"]["module"] = selected["mod"]
    activity["provider"]["func"] = selected["name"]
    activity["provider"]["arguments"] = {}

    click.secho(
        "\nYou now need to fill the arguments for this activity. Default\n"
        "values will be shown between brackets. You may simply press return\n"
        "to use it or not set any value.", fg="blue")
    for arg in selected.get("arguments", []):
        arg_name = arg["name"]
        if arg_name in ("secrets", "configuration"):
            continue

        # None is a bit of a problem because for the prompt it means
        # no defaults. When the user doesn't want to set a value, then
        # the prompt keeps asking. So, we pretend the default for None
        # is actually the empty string.
        arg_default = None
        if "default" in arg:
            arg_default = arg["default"]
            if arg_default is None:
                arg_default = ""
        arg_type = portable_type_name_to_python_type(arg["type"])
        question = "Argument's value for '{a}'".format(a=arg_name)
        m = s(question, fg='yellow')
        arg_value = click.prompt(
            m, default=arg_default, show_default=True, type=arg_type)

        # now, if the user didn't input anything and the default was
        # None, we override it back to None
        if "default" in arg:
            arg_default = arg["default"]
            if arg_default is None and arg_value == "":
                arg_value = None

        activity["provider"]["arguments"][arg["name"]] = arg_value
    pool.append(activity)

    m = s('Do you want to select another activity?', dim=True)
    if not click.confirm(m):
        return
    add_activities(activities, pool)
