# -*- coding: utf-8 -*-
import requests

from chaostoolkit.types import MicroservicesStatus, Probe


def endpoint_should_respond_ok(url: str) -> bool:
    r = requests.get(url)
    return r.status_code == 200
