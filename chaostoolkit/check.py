# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from logzero import logger
import requests
import semver

from chaostoolkit import __version__

__all__ = ["check_newer_version"]

GH_PROJECT_URL = "https://github.com/chaostoolkit/chaostoolkit"


def check_newer_version():
    """
    Query GitHub for the latest release of the chaostoolkit to compare it
    with the current's version. If the former is higher then issue a warning
    inviting the user to upgrade its environment.
    """
    try:
        r = requests.get(
            "{u}/releases/latest".format(u=GH_PROJECT_URL),
            timeout=(1, 30))
        if r.status_code == 200:
            _, latest_version = urlparse(r.url).path.rsplit('/', 1)
            if semver.compare(latest_version, __version__) == 1:
                logger.warn(
                    "\nThere is a new version of the chaostoolkit available.\n"
                    "You may install it by typing:\n\n"
                    "$ pip install -U chaostoolkit\n\n"
                    "Please review changes at {u}".format(u=r.url))

                return latest_version
    except Exception:
        pass
