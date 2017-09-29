# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Tuple

__all__ = ["MicroservicesStatus", "Probe", "Action", "Plan", "Layer",
           "TargetLayers"]


MicroservicesStatus = Tuple[Dict[str, Any], Dict[str, Any]]
Probe = Dict[str, Any]
Action = Dict[str, Any]
Plan = Dict[str, Any]
Layer = Any
TargetLayers = Dict[str, List[Dict[str, Any]]]
