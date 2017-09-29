# -*- coding: utf-8 -*-
from typing import Any, Callable, Dict

from chaostoolkit.errors import UnknownAction
from chaostoolkit.backend import k8s
from chaostoolkit.types import Action, Backend

__all__ = ["execute_action"]


def execute_action(name: str, action: Action, backend: Backend) -> Any:
    """
    Run the given action and return its result as-is. The `name` of the action
    must match a function where dashes are replaced with underscores.

    If no function can be found with such a name, raises :exc:`UnknownAction`.
    """
    if not name:
        raise ValueError("missing action name")

    name = name.replace('-', '_')
    action_func = get_action_function(name)
    if not action_func:
        raise UnknownAction(name)

    return action_func(action, backend)


def get_action_function(name: str) -> Callable[[Action], Any]:
    """
    Lookup the function matching the given name. This is an internal function.
    """
    return globals().get(name)

###############################################################################
# Actions
###############################################################################


def kill_microservice(action: Action, backend: Backend):
    """
    Try to kill a microservice as abruptly as possible. The `action` must have
    a parameter named `name` matching the name of the microservice.
    """
    return backend.kill_microservice(action.get("parameters").get("name"))


def start_microservice(action: Action, backend: Backend):
    """
    Start a microservice. The `action` must have a parameter named
    `config-path` which is the path on the filesystem to the description of
    that microservice.

    Refer to the backend for the exact meaning of that path.
    """
    return backend.start_microservice(
            action.get("parameters").get("config-path"))
