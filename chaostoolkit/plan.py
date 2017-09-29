# -*- coding: utf-8 -*-
import io
import json
import os.path
import pkgutil
import time
from typing import Any, Dict, Union

import jsonschema
from logzero import logger

from chaostoolkit.actions import execute_action, Action
from chaostoolkit.backend import load_backend_module
from chaostoolkit.errors import InvalidPlan
from chaostoolkit.probes import apply_probe, get_probe_from_step
from chaostoolkit.report import Report
from chaostoolkit.types import Backend, Plan

__all__ = ["run_plan", "load_plan", "execute_plan"]


def run_plan(plan_path: str, dry_run: bool = False) -> Report:
    """
    Execute the given plan and return a report once done.
    """
    with Report() as report:
        logger.info("Executing plan '{path}'".format(path=plan_path))
        plan = load_plan(plan_path)
        if dry_run:
            plan["backend"]["name"] = "noop"

        report.with_plan(plan)

        backend = load_backend_module(plan.get("backend", "dummy"))

        execute_plan(plan, backend)
        return report


def load_plan(plan_path: str) -> Plan:
    """
    Load the given plan, using the v1 dialect, and return a :class:~`Plan`
    instance.
    """
    logger.info("Loading plan...")

    if not os.path.exists(plan_path):
        raise IOError("could not find plan at {path}".format(path=plan_path))

    with io.open(plan_path) as f:
        payload = json.load(f)
        schema = pkgutil.get_data("chaostoolkit", "plan-schema.json")
        jsonschema.validate(payload, json.loads(schema.decode("utf-8")))
        return payload


def execute_plan(plan: Plan, backend: Backend):
    """
    Execute the given plan by applying the method's steps in the plan
    description.

    For each step, the ordering is as follows:

    * the steady probe to check the conditions are met before we can continue
    * the action, if provided, that will trigger the experiment condition
    * the close probe to check the state is as expected after the action was
      applied

    Note that the execution exists as soon as one of those fail, meaning the
    following steps are not applied. This also means you responsible for
    cleaning up your system.
    """
    title = plan.get("title", "N/A")
    logger.info("Running plan: '{name}'".format(name=title))

    method = plan.get("method")
    if method is None:
        raise InvalidPlan("a plan must have a method defined")

    for step in method:
        logger.info("Moving on to step '{title}'".format(
            title=step.get("title", "N/A")))
        apply_steady_probe(step, backend)
        apply_action(step, backend)
        apply_close_probe(step, backend)

    logger.info("Done with plan: '{name}'".format(name=title))


def apply_steady_probe(step: Dict[str, Any], backend: Backend):
    """
    Apply the steady probe found in this step. If none is defined, does
    nothing.

    When the name of the probe is not recognized, fails the call with an
    :exc:`UnknownProbe` exception.
    """
    probe = get_probe_from_step(step, "steady")
    if probe is None:
        return

    if "name" not in probe:
        raise InvalidPlan("steady probe requires a probe name to apply")

    if probe:
        probe_name = probe.pop("name")
        logger.info(" Applying steady probe '{name}'".format(name=probe_name))
        apply_probe(probe_name, probe, backend)


def apply_close_probe(step: Dict[str, Any], backend: Backend):
    """
    Apply the close probe found in this step. If none is defined, does
    nothing.

    When the name of the probe is not recognized, fails the call with an
    :exc:`UnknownProbe` exception.
    """
    probe = get_probe_from_step(step, "close")
    if probe is None:
        return

    if "name" not in probe:
        raise InvalidPlan("close probe requires a probe name to apply")

    if probe:
        probe_name = probe.pop("name")
        logger.info(" Applying close probe '{name}'".format(name=probe_name))
        apply_probe(probe_name, probe, backend)


def apply_action(step: Dict[str, Any], backend: Backend):
    """
    Apply the saction found in this step. If none is defined, does
    nothing.

    When the name of the probe is not recognized, fails the call with an
    :exc:`UnknownAction` exception.
    """
    action = step.get("action")
    if not action:
        return

    action_name = action.get("name")
    if not action_name:
        raise InvalidPlan("action requires a name")

    pause(action, "before")
    logger.info(" Executing action '{name}'".format(name=action_name))
    execute_action(action_name, action, backend)
    pause(action, "after")


def pause(action: Action, when: str):
    """
    Look in the action for the pause at the given moment, either `"before"` the
    action or `"after"`.

    The pause should be in seconds.
    """
    pauses = action.get("pauses")
    if pauses and when in pauses:
        logger.info(" Pausing {pause}s".format(pause=pauses[when]))
        time.sleep(pauses[when])
