# -*- coding: utf-8 -*-
import pytest

from chaostoolkit.layers import load_layers
from chaostoolkit.probes import apply_probe, microservices_all_healthy, \
    microservice_available_and_healthy, microservice_is_not_available
from chaostoolkit.errors import FailedProbe, InvalidProbe

layers = load_layers({
    "platforms": [{
        "key": "fixtures.failing_probe_backend"
    }]
})


def test_cannot_apply_an_unamed_probe():
    step = {}

    with pytest.raises(ValueError) as excinfo:
        apply_probe(step.get("name"), step, None)

    assert "missing probe name" in str(excinfo)


def test_unhealthy_system_should_be_reported():
    step = {
        "layer": "fixtures.failing_probe_backend",
        "name": "all-microservices-healthy"
    }

    with pytest.raises(FailedProbe) as excinfo:
        microservices_all_healthy(step, layers[step["layer"]])


def test_expecting_a_healthy_microservice_should_be_reported_when_not():
    step = {
        "layer": "fixtures.failing_probe_backend",
        "name": "microservice-available-and-healthy"
    }

    with pytest.raises(InvalidProbe) as excinfo:
        microservice_available_and_healthy(step, layers[step["layer"]])

    step = {
        "layer": "fixtures.failing_probe_backend",
        "name": "microservice-available-and-healthy",
        "parameters": {
            "name": "cherrypy-webapp"
        }
    }

    with pytest.raises(FailedProbe) as excinfo:
        microservice_available_and_healthy(step, layers[step["layer"]])

    assert "microservice 'cherrypy-webapp' is not healthy" in str(excinfo)


def test_expecting_microservice_is_there_when_it_should_not():
    step = {
        "layer": "fixtures.failing_probe_backend",
        "name": "microservice-is-not-available"
    }

    with pytest.raises(InvalidProbe) as excinfo:
        microservice_is_not_available(step, layers[step["layer"]])

    step = {
        "layer": "fixtures.failing_probe_backend",
        "name": "microservice-is-not-available",
        "parameters": {
            "name": "cherrypy-webapp"
        }
    }

    with pytest.raises(FailedProbe) as excinfo:
        microservice_is_not_available(step, layers[step["layer"]])
