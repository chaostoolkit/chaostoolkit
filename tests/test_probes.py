# -*- coding: utf-8 -*-
import pytest

from chaostoolkit.backend import load_backend_module
from chaostoolkit.probes import apply_probe, microservices_all_healthy, \
    microservice_available_and_healthy, microservice_is_not_available
from chaostoolkit.errors import FailedProbe, InvalidProbe

backend = load_backend_module({"name": "fixtures.failing_probe_backend"})


def test_cannot_apply_an_unamed_probe():
    step = {}

    with pytest.raises(ValueError) as excinfo:
        apply_probe(step.get("name"), step, backend)

    assert "missing probe name" in str(excinfo)


def test_unhealthy_system_should_be_reported():
    step = {
        "name": "all-microservices-healthy"
    }

    with pytest.raises(FailedProbe) as excinfo:
        microservices_all_healthy(step, backend)


def test_expecting_a_healthy_microservice_should_be_reported_when_not():
    step = {
        "name": "microservice-available-and-healthy"
    }

    with pytest.raises(InvalidProbe) as excinfo:
        microservice_available_and_healthy(step, backend)

    step = {
        "name": "microservice-available-and-healthy",
        "parameters": {
            "name": "cherrypy-webapp"
        }
    }

    with pytest.raises(FailedProbe) as excinfo:
        microservice_available_and_healthy(step, backend)

    assert "microservice 'cherrypy-webapp' is not healthy" in str(excinfo)


def test_expecting_microservice_is_there_when_it_should_not():
    step = {
        "name": "microservice-is-not-available"
    }

    with pytest.raises(InvalidProbe) as excinfo:
        microservice_is_not_available(step, backend)

    step = {
        "name": "microservice-is-not-available",
        "parameters": {
            "name": "cherrypy-webapp"
        }
    }

    with pytest.raises(FailedProbe) as excinfo:
        microservice_is_not_available(step, backend)
