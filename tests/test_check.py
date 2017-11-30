# -*- coding: utf-8 -*-
from unittest.mock import patch

import semver

from chaostoolkit import __version__
from chaostoolkit.check import check_newer_version


class FakeResponse:
    def __init__(self, status=200, url=None, version=None):
        self.status_code = status
        self.url = url
        self.text = '<a href="" id="latest">{v}</a>'.format(v=version)


@patch("chaostoolkit.check.requests", autospec=True)
def test_version_is_not_newer(requests):
    requests.get.return_value = FakeResponse(
        200,
        "http://someplace/usage/latest/",
        __version__
    )

    latest_version = check_newer_version()
    assert latest_version is None


@patch("chaostoolkit.check.requests", autospec=True)
def test_version_is_newer(requests):
    newer_version = semver.bump_minor(__version__)
    requests.get.return_value = FakeResponse(
        200,
        "http://someplace//usage/latest/",
        newer_version
    )

    latest_version = check_newer_version()
    assert latest_version == newer_version