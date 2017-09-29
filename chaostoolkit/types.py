# -*- coding: utf-8 -*-
from typing import Any, Dict, Tuple

__all__ = ["MicroservicesStatus", "Probe", "Action", "Plan", "Backend"]


MicroservicesStatus = Tuple[Dict[str, Any], Dict[str, Any]]
Probe = Dict[str, Any]
Action = Dict[str, Any]
Plan = Dict[str, Any]
Backend = Any
