#!/usr/bin/env python
"""chaostoolkit builder and installer"""
import os.path

from setuptools import setup


def get_version_from_package() -> str:
    """
    Read the package version from the source without importing it.
    """
    path = os.path.join(os.path.dirname(__file__), "chaostoolkit/__init__.py")
    path = os.path.normpath(os.path.abspath(path))
    with open(path) as f:
        for line in f:
            if line.startswith("__version__"):
                token, version = line.split(" = ", 1)
                version = version.replace("\"", "").strip()
                return version


if __name__ == '__main__':
    setup(
        name="chaostoolkit",
        version=get_version_from_package()
    )
