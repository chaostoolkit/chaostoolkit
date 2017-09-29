# -*- coding: utf-8 -*-
import json
import os.path
from typing import Union

from chaostoolkit.types import MicroservicesStatus, Probe


def all_microservices_healthy() -> MicroservicesStatus:
    return [], [{"name": "my-svc"}]


def microservice_available_and_healthy(name: str) -> Union[bool, None]:
    return False


def microservice_is_not_available(name: str) -> bool:
    return False


def kill_microservice(name: str):
    raise RuntimeError("failed killing microservice")


def start_microservice(deployment_config: str):
    raise RuntimeError("failed starting microservice")
