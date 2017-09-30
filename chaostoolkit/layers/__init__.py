# -*- coding: utf-8 -*-
import importlib
from typing import Any, Dict, List

from logzero import logger

from chaostoolkit.types import Layer, TargetLayers

__all__ = ["load_layers"]

MAPPING = {
    "kubernetes": "chaostoolkit.layers.platforms.k8s",
    "noop": "chaostoolkit.layers.noop",
    "spring": "chaostoolkit.layers.applications.spring"
}


def load_layers(target_layers: TargetLayers) -> Dict[str, Layer]:
    """
    Import all target layer modules from a config such as:

    ... json::
        {
            "platforms": [
                { "key": "kubernetes" }
            ],
            "applications": [
                { "key": "spring" }
            ]
        }

    Currently supported platforms:

    * `"kubernetes"`: the :mod:`chaostoolkit.layers.platforms.k8s` module
    * `"noop"`: the :mod:`chaostoolkit.layers.platforms.noop` module

    Supported applications:

    * `"spring"`: the :mod:`chaostoolkit.layers.application.spring` module
    """
    layers = {}

    logger.info("Loading the following target layers:")
    for layer in ("platforms", "applications"):
        for target in target_layers.get(layer, []):
            key = target.get("key")
            mod_name = MAPPING.get(key, key)
            logger.info(" {layer}: {key} => {mod}".format(
                layer=layer, key=key, mod=mod_name))
            layers[key] = importlib.import_module(mod_name)

    return layers
