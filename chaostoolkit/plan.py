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
from chaostoolkit.layers import load_layers
from chaostoolkit.errors import InvalidPlan
from chaostoolkit.probes import apply_probe, get_probe_from_step
from chaostoolkit.report import Report
from chaostoolkit.types import Layer, Plan

__all__ = ["run_plan", "load_plan", "execute_plan"]


def run_plan(plan_path: str, dry_run: bool = False) -> Report:
    """
    Execute the given plan and return a report once done.
    """
    with Report() as report:
        logger.info("Executing plan '{path}'".format(path=plan_path))
        plan = load_plan(plan_path)
        if dry_run:
            switch_to_dry_run(plan)

        report.with_plan(plan)

        layers = load_layers(plan.get("target-layers"))

        execute_plan(plan, layers)
        return report


def switch_to_dry_run(plan: Plan):
    """
    When running a dry run, we switch all target layers to a noop layer
    so operations do nothing.
    """
    for target in plan["target-layers"]:
        for layer in plan["target-layers"][target]:
            layer["key"] = "noop"

        for step in plan["method"]:
            probes = step.get("probes")
            if probes:
                if "steady" in probes:
                    probes["steady"]["layer"] = "noop"
                if "close" in probes:
                    probes["close"]["layer"] = "noop"

            if "action" in step:
                step["action"]["layer"] = "noop"


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
        #schema = os.path.join(os.path.dirname(__file__), "plan-schema.json")
        #with io.open(schema) as s:
        #    jsonschema.validate(payload, json.load(s))
        return payload


def execute_plan(plan: Plan, layers: Dict[str, Layer]):
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

        apply_steady_probe(step, layers)
        apply_action(step, layers)
        apply_close_probe(step, layers)

    logger.info("Done with plan: '{name}'".format(name=title))


def apply_steady_probe(step: Dict[str, Any], layers: Dict[str, Layer]):
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

    if "layer" not in probe:
        raise InvalidPlan("steady probe requires the target layer to be set")

    if probe:
        probe_name = probe.pop("name")
        layer = layers.get(probe["layer"])
        logger.info(" Applying steady probe '{name}'".format(name=probe_name))
        apply_probe(probe_name, probe, layer)


def apply_close_probe(step: Dict[str, Any], layers: Dict[str, Layer]):
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

    if "layer" not in probe:
        raise InvalidPlan("close probe requires the target layer to be set")

    if probe:
        probe_name = probe.pop("name")
        layer = layers.get(probe["layer"])
        logger.info(" Applying close probe '{name}'".format(name=probe_name))
        apply_probe(probe_name, probe, layer)


def apply_action(step: Dict[str, Any], layers: Dict[str, Layer]):
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

    if "layer" not in action:
        raise InvalidPlan("action requires the target layer to be set")

    pause(action, "before")
    logger.info(" Executing action '{name}'".format(name=action_name))
    layer = layers.get(action["layer"])
    execute_action(action_name, action, layer)
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
