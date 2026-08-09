try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata

from click_plugins import with_plugins

from chaostoolkit.commands.root import cli
from chaostoolkit.commands.root import discover_cli as discover_cli
from chaostoolkit.commands.root import info_cli as info_cli
from chaostoolkit.commands.root import init_cli as init_cli
from chaostoolkit.commands.root import run_cli as run_cli
from chaostoolkit.commands.root import settings_cli as settings_cli
from chaostoolkit.commands.root import validate_cli as validate_cli

__all__ = ["cli"]


# Keep this after importing the CLI group so plugins can override built-ins.
# Knowing which version of importlib is installed is dark magic because
# everyone wants a different version that may not be compatible with others.
# It is easier to support both entry_points APIs here.
# https://github.com/python/importlib_metadata/issues/411#issuecomment-1494336052
try:
    with_plugins(
        importlib_metadata.entry_points().get("chaostoolkit.cli_plugins")
    )(cli)
except AttributeError:
    with_plugins(
        importlib_metadata.entry_points(group="chaostoolkit.cli_plugins")
    )(cli)
