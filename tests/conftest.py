import tempfile

import pytest


@pytest.fixture(scope="function")
def log_file():
    with tempfile.NamedTemporaryFile() as f:
        yield f
