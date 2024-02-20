import logging
import os
import uuid

import click
from chaoslib.log import configure_logger

from chaostoolkit import __version__
from chaostoolkit.check import (
    check_newer_version,
)
from chaoslib.settings import CHAOSTOOLKIT_CONFIG_PATH
from click_plugins import with_plugins

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata


from chaostoolkit.commands.discover import discover as discover_cli
from chaostoolkit.commands.info import info as info_cli
from chaostoolkit.commands.init import init as init_cli
from chaostoolkit.commands.run import run as run_cli
from chaostoolkit.commands.settings import settings as settings_cli
from chaostoolkit.commands.validate import validate as validate_cli

__all__ = ["cli"]

logger = logging.getLogger("chaostoolkit")


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", is_flag=True, help="Display debug level traces.")
@click.option(
    "--no-version-check",
    is_flag=True,
    help="Do not search for an updated version of the chaostoolkit.",
)
@click.option(
    "--change-dir", help="Change directory before running experiment."
)
@click.option(
    "--no-log-file", is_flag=True, help="Disable logging to file entirely."
)
@click.option(
    "--log-file",
    default="chaostoolkit.log",
    show_default=True,
    help="File path where to write the command's log.",
)
@click.option(
    "--log-file-level",
    default="debug",
    show_default=False,
    help="File logging level: debug, info, warning, error",
    type=click.Choice(["debug", "info", "warning", "error"]),
)
@click.option(
    "--log-format",
    default="string",
    show_default=False,
    help="Console logging format: string, json.",
    type=click.Choice(["string", "json"]),
)
@click.option(
    "--settings",
    default=CHAOSTOOLKIT_CONFIG_PATH,
    show_default=True,
    help="Path to the settings file.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: bool = False,
    no_version_check: bool = False,
    change_dir: str = None,
    no_log_file: bool = False,
    log_file: str = "chaostoolkit.log",
    log_file_level: str = "info",
    log_format: str = "string",
    settings: str = CHAOSTOOLKIT_CONFIG_PATH,
):
    if no_log_file:
        configure_logger(
            verbose=verbose, log_format=log_format, context_id=str(uuid.uuid4())
        )
    else:
        configure_logger(
            verbose=verbose,
            log_file=log_file,
            log_file_level=log_file_level,
            log_format=log_format,
            context_id=str(uuid.uuid4()),
        )

    subcommand = ctx.invoked_subcommand

    # make it nicer for going through the log file
    logger.debug("#" * 79)
    logger.debug(f"Running command '{subcommand}'")

    ctx.obj = {}
    ctx.obj["settings_path"] = click.format_filename(settings)
    logger.debug("Using settings file '{}'".format(ctx.obj["settings_path"]))

    if not no_version_check:
        check_newer_version(command=subcommand)

    if change_dir:
        logger.warning(f"Moving to {change_dir}")
        os.chdir(change_dir)


cli.add_command(discover_cli)
cli.add_command(info_cli)
cli.add_command(init_cli)
cli.add_command(run_cli)
cli.add_command(settings_cli)
cli.add_command(validate_cli)


# keep this after the cli group declaration for plugins to override defaults
# knowing which version of importlib is actually installed is dark magic because
# everyone wants a different versions that may not compatible
# between each other. Easier to just see what works and what doesn't here.
# https://github.com/python/importlib_metadata/issues/411#issuecomment-1494336052
try:
    with_plugins(
        importlib_metadata.entry_points().get("chaostoolkit.cli_plugins")
    )(cli)
except AttributeError:
    with_plugins(
        importlib_metadata.entry_points(group="chaostoolkit.cli_plugins")
    )(cli)
