# -*- coding: utf-8 -*-
import re

from logzero import logger
import requests
import semver

from chaostoolkit import __version__

__all__ = ["check_newer_version"]

LATEST_RELEASE_URL = "http://chaostoolkit.org/usage/latest/"
VERSION_REGEX = re.compile('id="latest">([0-9]+\\.[0-9]+\\.[0-9]+)</')


def check_newer_version():
    """
    Query GitHub for the latest release of the chaostoolkit to compare it
    with the current's version. If the former is higher then issue a warning
    inviting the user to upgrade its environment.
    """
    try:
        r = requests.get(LATEST_RELEASE_URL, timeout=(1, 30),
                         headers={
                             "Referer": "#currentversion={v}".format(
                                 v=__version__)})
        if r.status_code == 200:
            m = VERSION_REGEX.search(r.text)
            if m:
                latest_version = m.group(1)
                if semver.compare(latest_version, __version__) == 1:
                    logger.warn(
                        "\nThere is a new version ({v}) of the chaostoolkit "
                        "available.\n"
                        "You may upgrade by typing:\n\n"
                        "$ pip install -U chaostoolkit\n\n"
                        "Please review changes at {u}\n".format(
                            u=r.url, v=latest_version))

                    return latest_version
    except Exception:
        pass
