# -*- coding: utf-8 -*-
import tempfile
import logging

import logzero
import pytest


@pytest.fixture(scope='function')
def log_file():
    with tempfile.NamedTemporaryFile() as f:
        yield f
