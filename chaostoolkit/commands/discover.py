import json
import logging

import click
from chaoslib.discovery import discover as disco
from chaoslib.exceptions import DiscoveryFailed
from chaoslib.notification import (
    DiscoverFlowEvent,
    notify,
)
from chaoslib.types import Discovery
from chaoslib.settings import load_settings

from chaostoolkit import encoder


logger = logging.getLogger("chaostoolkit")


@click.command()
@click.option(
    "--no-system-info", is_flag=True, help="Do not discover system information."
)
@click.option(
    "--no-install", is_flag=True, help="Assume package already in PYTHONPATH."
)
@click.option(
    "--discovery-path",
    default="./discovery.json",
    help="Path where to save the the discovery outcome.",
    show_default=True,
)
@click.argument("package")
@click.pass_context
def discover(
    ctx: click.Context,
    package: str,
    discovery_path: str = "./discovery.json",
    no_system_info: bool = False,
    no_install: bool = False,
) -> Discovery:
    """Discover capabilities and experiments."""
    settings = load_settings(ctx.obj["settings_path"])
    try:
        notify(settings, DiscoverFlowEvent.DiscoverStarted, package)
        discovery = disco(
            package_name=package,
            discover_system=not no_system_info,
            download_and_install=not no_install,
        )
    except DiscoveryFailed as err:
        notify(settings, DiscoverFlowEvent.DiscoverFailed, package, err)
        logger.debug(f"Failed to discover {package}", exc_info=err)
        logger.fatal(str(err))
        return

    with open(discovery_path, "w") as d:
        d.write(json.dumps(discovery, indent=2, default=encoder))
    logger.info(f"Discovery outcome saved in {discovery_path}")

    notify(settings, DiscoverFlowEvent.DiscoverCompleted, discovery)
    return discovery
