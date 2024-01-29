import json
import os

import click
import yaml

from chaoslib.settings import (
    load_settings,
    locate_settings_entry,
    save_settings,
)


@click.group()
def settings():
    """
    Read, write or remove from your settings file.
    """
    pass


@settings.command("show")
@click.option(
    "--format",
    "fmt",
    default="yaml",
    show_default=False,
    help="Output format.",
    type=click.Choice(["json", "yaml"]),
)
@click.pass_context
def show_settings(ctx: click.Context, fmt: str = "json"):
    """
    Show the entire content of the settings file.

    Be aware this will not obfuscate secret data.
    """
    if not os.path.isfile(ctx.obj["settings_path"]):
        click.abort(
            "No settings file found at {}".format(ctx.obj["settings_path"])
        )

    settings = load_settings(ctx.obj["settings_path"]) or {}
    if fmt == "json":
        click.echo(json.dumps(settings, indent=2))
    elif fmt == "yaml":
        click.echo(yaml.dump(settings, indent=2))


settings.add_command(show_settings)


@settings.command("set")
@click.argument("key", nargs=1)
@click.argument("value", nargs=1)
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


@settings.command("remove")
@click.argument("key", nargs=1)
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


@settings.command("get")
@click.option(
    "--format",
    "fmt",
    default="yaml",
    show_default=False,
    help="Output format.",
    type=click.Choice(["string", "json", "yaml"]),
)
@click.argument("key", nargs=1)
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
