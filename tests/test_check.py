# -*- coding: utf-8 -*-
from unittest.mock import patch

import semver

from chaostoolkit import __version__
from chaostoolkit.check import check_newer_version


class FakeResponse:
    def __init__(self, status=200, url=None, response=None):
        self.status_code = status
        self.url = url
        self.response = response

    def json(self):
        return self.response


@patch("chaostoolkit.check.requests", autospec=True)
def test_version_is_not_newer(requests):
    requests.get.return_value = FakeResponse(
        200,
        "https://releases.chaostoolkit.org/latest",
        {"version": __version__, "up_to_date": True}
    )

    latest_version = check_newer_version(command="init")
    assert latest_version is None


@patch("chaostoolkit.check.requests", autospec=True)
def test_version_is_newer(requests):
    version = __version__.replace("rc", "-rc")
    newer_version = semver.bump_minor(version)
    requests.get.return_value = FakeResponse(
        200,
        "http://someplace//usage/latest/",
        {"version": __version__, "up_to_date": False}
    )

    latest_version = check_newer_version(command="init")
    assert latest_version == __version__