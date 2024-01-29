import os

import click

from chaoslib import __version__ as chaoslib_version
from chaoslib.info import list_extensions
from chaostoolkit import __version__


@click.command()
@click.argument(
    "target",
    type=click.Choice(["core", "settings", "extensions"]),
    metavar="TARGET",
)
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
        click.secho(fmt.format("NAME", "VERSION"), fg="bright_blue")
        click.echo(fmt.format("CLI", __version__))
        click.echo(fmt.format("Core library", chaoslib_version))
    elif target == "extensions":
        fmt = "{:<40}{:<10}{:30}{:50}"
        click.secho(
            fmt.format("NAME", "VERSION", "LICENSE", "DESCRIPTION"),
            fg="bright_blue",
        )
        extensions = list_extensions()
        for extension in extensions:
            summary = extension.summary.replace(
                "Chaos Toolkit Extension for ", ""
            )[:50]
            click.echo(
                fmt.format(
                    extension.name,
                    extension.version,
                    extension.license,
                    summary,
                )
            )
    elif target == "settings":
        settings_path = ctx.obj["settings_path"]
        if not os.path.isfile(settings_path):
            click.echo(f"No settings file found at {settings_path}")
            return

        with open(settings_path) as f:
            click.echo(f.read())
