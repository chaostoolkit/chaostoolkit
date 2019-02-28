# -*- coding: utf-8 -*-
import re

from logzero import logger
import requests

from chaostoolkit import __version__

__all__ = ["check_newer_version"]

LATEST_RELEASE_URL = "https://releases.chaostoolkit.org/latest"
CHANGELOG_URL = "https://github.com/chaostoolkit/chaostoolkit/blob/master/CHANGELOG.md"  # nopep8


def check_newer_version(command: str):
    """
    Query for the latest release of the chaostoolkit to compare it
    with the current's version. If the former is higher then issue a warning
    inviting the user to upgrade its environment.
    """
    try:
        command = command.strip()
        r = requests.get(LATEST_RELEASE_URL, timeout=(2, 30),
                         params={"current": __version__, "command": command})
        if r.status_code == 200:
            payload = r.json()
            latest_version = payload["version"]
            if payload.get("up_to_date") is False:
                options = '--pre -U' if 'rc' in latest_version else '-U'
                logger.warning(
                    "\nThere is a new version ({v}) of the chaostoolkit "
                    "available.\n"
                    "You may upgrade by typing:\n\n"
                    "$ pip install {opt} chaostoolkit\n\n"
                    "Please review changes at {u}\n".format(
                        u=CHANGELOG_URL, v=latest_version, opt=options))
                return latest_version
    except Exception:
        pass
