# -*- coding: utf-8 -*-
from typing import Any, Callable, Dict

from chaostoolkit.errors import FailedProbe, InvalidProbe, UnknownProbe
from chaostoolkit.types import Layer, MicroservicesStatus, Probe

__all__ = ["apply_probe", "get_probe_from_step"]


def get_probe_from_step(step: Dict[str, Any],
                        probe_name: str) -> Dict[str, Any]:
    """
    Extract the probe with the given name from the provided `step`.

    This will return `None` if the step does not contain such a probe.
    """
    return step.get("probes", {}).get(probe_name)


def apply_probe(name: str, probe: Probe, layer: Layer) -> Any:
    """
    Apply the given probe and return its result. The name of the probe
    matches a function in this module by replacing dashes with underscores.

    If no function matches, raises :exc:`UnknownProbe`.
    """
    if not name:
        raise ValueError("missing probe name")

    name = name.replace('-', '_')
    probe_func = get_probe_function(name)
    if not probe_func:
        raise UnknownProbe(name)

    return probe_func(probe, layer)


def get_probe_function(name: str) -> Callable[[Probe], Any]:
    """
    Lookup the function matching the given probe name. This is an internal
    function.
    """
    return globals().get(name)

###############################################################################
# Probes
###############################################################################


def microservices_all_healthy(probe: Probe, layer: Layer):
    """
    Query the system for its health. Raises :exc:`FailedProbe` when at least
    one microservice is not marked running.
    """
    notready, failed = layer.all_microservices_healthy()
    if notready or failed:
        raise FailedProbe("the system is unhealthy")


def microservice_available_and_healthy(probe: Probe, layer: Layer):
    """
    Query the system for one microservice's availability and health. If the
    microservice is not available or running, raises :exc:`FailedProbe`.
    """
    name = probe.get("parameters", {}).get("name")
    if not name:
        raise InvalidProbe("missing microservice name")

    available = layer.microservice_available_and_healthy(name)

    if available is None:
        raise FailedProbe(
            "microservice '{name}' was not found".format(name=name))

    if available is False:
        raise FailedProbe(
            "microservice '{name}' is not healthy".format(name=name))


def microservice_is_not_available(probe: Probe, layer: Layer):
    """
    Query the system for one microservice's availability. If the microservice
    is found, even in a non-running state, then raises :exc:`FailedProbe`.
    """
    name = probe.get("parameters", {}).get("name")
    if not name:
        raise InvalidProbe("missing microservice name")

    unavailable = layer.microservice_is_not_available(name)

    if unavailable is False:
        raise FailedProbe(
            "microservice '{name}' looks healthy".format(name=name))


def endpoint_should_respond_ok(probe: Probe, layer: Layer):
    url = probe.get("parameters", {}).get("url")
    if not url:
        raise InvalidProbe("missing endpoint url")

    if not layer.endpoint_should_respond_ok(url):
        raise FailedProbe("endpoint did not return an okay status")
