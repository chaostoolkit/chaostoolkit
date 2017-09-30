# -*- coding: utf-8 -*-
import json
import os.path
from typing import Union

from chaostoolkit.types import MicroservicesStatus, Probe


def endpoint_should_respond_ok(url: str) -> bool:
    return True


def all_microservices_healthy() -> MicroservicesStatus:
    return [], []


def microservice_available_and_healthy(name: str) -> Union[bool, None]:
    return True


def microservice_is_not_available(name: str) -> bool:
    return True


def kill_microservice(name: str):
    pass


def start_microservice(deployment_config: str):
    pass
