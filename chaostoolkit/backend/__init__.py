# -*- coding: utf-8 -*-
import importlib
from typing import Any, Dict

from logzero import logger

from chaostoolkit.types import Backend

__all__ = ["load_backend_module"]


def load_backend_module(backend_config: Dict[str, Any]) -> Backend:
    """
    Import the backend module matching the `backend_config["name"]` key. 

    Currently supported:

    * `"kubernetes"`: the :mod:`chaostoolkit.backend.k8s` module
    * `"noop"`: the :mod:`chaostoolkit.backend.noop` module

    Use the noop module when you want to test your plan first in a dry run.
    """
    name = backend_config.get("name")

    if name == "kubernetes":
        name = "chaostoolkit.backend.k8s"
    elif name == "noop":
        name = "chaostoolkit.backend.noop"

    return importlib.import_module(name)
