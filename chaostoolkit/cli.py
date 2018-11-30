# -*- coding: utf-8 -*-
from datetime import date, datetime
import decimal
import io
import json
import logging
import os
import sys
from typing import List
import uuid

from chaoslib import __version__ as chaoslib_version
from chaoslib.exceptions import ChaosException, DiscoveryFailed, InvalidSource
from chaoslib.discovery import discover as disco
from chaoslib.experiment import ensure_experiment_is_valid, run_experiment
from chaoslib.info import list_extensions
from chaoslib.loader import load_experiment
from chaoslib.notification import notify, DiscoverFlowEvent, InitFlowEvent, \
    RunFlowEvent, ValidateFlowEvent
from chaoslib.settings import load_settings, CHAOSTOOLKIT_CONFIG_PATH
from chaoslib.types import Activity, Discovery, Experiment, Journal
import click
from click_plugins import with_plugins
import logzero
from logzero import logger
from pkg_resources import iter_entry_points

from chaostoolkit import __version__
from chaostoolkit.check import check_newer_version


__all__ = ["cli"]


def encoder(o: object) -> str:
    """
    Perform some additional encoding for types JSON doesn't support natively.

    We don't try to respect any ECMA specification here as we want to retain
    as much information as we can.
    """
    if isinstance(o, (date, datetime)):
        # we do not meddle with the timezone and assume the date was stored
        # with the right information of timezone as +-HH:MM
        return o.isoformat()
    elif isinstance(o, decimal.Decimal):
        return str(o)
    elif isinstance(o, uuid.UUID):
        return str(o)

    raise TypeError(
        "Object of type '{}' is not JSON serializable".format(type(o)))


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
@click.option('--settings', default=CHAOSTOOLKIT_CONFIG_PATH,
              show_default=True, help="Path to the settings file.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool = False,
        no_version_check: bool = False, change_dir: str = None,
        no_log_file: bool = False, log_file: str = "chaostoolkit.log",
        settings: str = CHAOSTOOLKIT_CONFIG_PATH):
    if verbose:
        logzero.loglevel(logging.DEBUG, update_custom_handlers=False)
        fmt = "%(color)s[%(asctime)s %(levelname)s] "\
              "[%(module)s:%(lineno)d]%(end_color)s %(message)s"
    else:
        logzero.loglevel(logging.INFO, update_custom_handlers=False)
        fmt = "%(color)s[%(asctime)s %(levelname)s]%(end_color)s %(message)s"

    if not no_log_file:
        # let's ensure we log at DEBUG level
        logger.setLevel(logging.DEBUG)
        logzero.logfile(
            click.format_filename(log_file), mode='a',
            loglevel=logging.DEBUG)

    logzero.formatter(
        formatter=logzero.LogFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S"),
        update_custom_handlers=False)

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


@cli.command()
@click.option('--journal-path', default="./journal.json",
              help='Path where to save the journal from the execution.')
@click.option('--dry', is_flag=True,
              help='Run the experiment without executing activities.')
@click.option('--no-validation', is_flag=True,
              help='Do not validate the experiment before running.')
@click.argument('source')
@click.pass_context
def run(ctx: click.Context, source: str, journal_path: str = "./journal.json",
        dry: bool = False, no_validation: bool = False,
        fail_fast: bool = True) -> Journal:
    """Run the experiment loaded from SOURCE, either a local file or a
       HTTP resource."""
    settings = load_settings(ctx.obj["settings_path"])
    try:
        experiment = load_experiment(click.format_filename(source), settings)
    except InvalidSource as x:
        logger.error(str(x))
        logger.debug(x)
        sys.exit(1)

    notify(settings, RunFlowEvent.RunStarted, experiment)

    if not no_validation:
        try:
            ensure_experiment_is_valid(experiment)
        except ChaosException as x:
            logger.error(str(x))
            logger.debug(x)
            sys.exit(1)

    experiment["dry"] = dry

    journal = run_experiment(experiment)

    with io.open(journal_path, "w") as r:
        json.dump(journal, r, indent=2, ensure_ascii=False, default=encoder)

    if journal["status"] == "completed":
        notify(settings, RunFlowEvent.RunCompleted, journal)
    else:
        notify(settings, RunFlowEvent.RunFailed, journal)

        if journal.get("deviated", False):
            notify(settings, RunFlowEvent.RunDeviated, journal)

        # when set (default) we exit this command immediatly if the execution
        # failed, was aborted or interrupted
        # when unset, plugins can continue the processing. In that case, they
        # are responsible to set the process exit code accordingly.
        if fail_fast:
            sys.exit(1)

    return journal


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def validate(ctx: click.Context, path: str) -> Experiment:
    """Validate the experiment at PATH."""
    settings = load_settings(ctx.obj["settings_path"])
    experiment = load_experiment(click.format_filename(path))
    try:
        notify(settings, ValidateFlowEvent.ValidateStarted, experiment)
        ensure_experiment_is_valid(experiment)
        notify(settings, ValidateFlowEvent.ValidateCompleted, experiment)
        logger.info("experiment syntax and semantic look valid")
    except ChaosException as x:
        notify(settings, ValidateFlowEvent.ValidateFailed, experiment, x)
        logger.error(str(x))
        logger.debug(x)
        sys.exit(1)

    return experiment


@cli.command()
@click.argument('target')
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
              help='Path where to save the experiment.',
              show_default=True)
@click.pass_context
def init(ctx: click.Context, discovery_path: str = "./discovery.json",
         experiment_path: str = "./experiment.json") -> Experiment:
    """
    Initialize a new experiment from discovered capabilities.
    """
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

    with open(experiment_path, "w") as e:
        e.write(json.dumps(base_experiment, indent=4, default=encoder))

    click.echo(
        "\nExperiment created and saved in '{e}'".format(e=experiment_path))

    notify(settings, InitFlowEvent.InitCompleted, base_experiment)
    return base_experiment


# keep this after the cli group declaration for plugins to override defaults
with_plugins(iter_entry_points('chaostoolkit.cli_plugins'))(cli)


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
        question = "Argument's value for '{a}'".format(a=arg_name)
        m = s(question, fg='yellow')
        arg_value = click.prompt(
            m, default=arg_default, show_default=True)

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
