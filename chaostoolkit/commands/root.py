import logging
import os
import uuid

import click
from chaoslib.log import configure_logger
from chaoslib.settings import CHAOSTOOLKIT_CONFIG_PATH

from chaostoolkit import __version__
from chaostoolkit.check import (
    check_newer_version,
)
from chaostoolkit.commands.discover import discover as discover_cli
from chaostoolkit.commands.info import info as info_cli
from chaostoolkit.commands.init import init as init_cli
from chaostoolkit.commands.run import run as run_cli
from chaostoolkit.commands.settings import settings as settings_cli
from chaostoolkit.commands.skills import skills as skills_cli
from chaostoolkit.commands.validate import validate as validate_cli
from chaostoolkit.runtime import (
    RUNTIME_ARGUMENTS_META_KEY,
    RUNTIME_INVOCATION_CWD_META_KEY,
    in_runtime_child,
)

__all__ = ["cli"]

logger = logging.getLogger("chaostoolkit")


class RuntimeAwareGroup(click.Group):
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        ctx.meta[RUNTIME_ARGUMENTS_META_KEY] = tuple(args)
        ctx.meta[RUNTIME_INVOCATION_CWD_META_KEY] = os.getcwd()
        return super().parse_args(ctx, args)


@click.group(cls=RuntimeAwareGroup)
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
    change_dir: str | None = None,
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

    if not no_version_check and not in_runtime_child():
        check_newer_version(command=subcommand)

    if change_dir:
        logger.warning(f"Moving to {change_dir}")
        os.chdir(change_dir)


cli.add_command(discover_cli)
cli.add_command(info_cli)
cli.add_command(init_cli)
cli.add_command(run_cli)
cli.add_command(settings_cli)
cli.add_command(skills_cli)
cli.add_command(validate_cli)
