import json
import logging
import os
from typing import List

import click
import yaml
from chaoslib.discovery.discover import portable_type_name_to_python_type
from chaoslib.notification import (
    InitFlowEvent,
    notify,
)
from chaoslib.types import Activity, Experiment
from chaoslib.settings import load_settings

from chaostoolkit import encoder


logger = logging.getLogger("chaostoolkit")


@click.command()
@click.option(
    "--discovery-path",
    default="./discovery.json",
    help="Path to the discovery outcome.",
    show_default=True,
    type=click.Path(exists=False),
)
@click.option(
    "--experiment-path",
    default="./experiment.json",
    type=click.Path(exists=False),
    help="Path where to save the experiment (.yaml or .json)",
    show_default=True,
)
@click.pass_context
def init(
    ctx: click.Context,
    discovery_path: str = "./discovery.json",  # noqa: C901
    experiment_path: str = "./experiment.json",
) -> Experiment:
    """Initialize a new experiment from discovered capabilities."""
    settings = load_settings(ctx.obj["settings_path"])
    notify(settings, InitFlowEvent.InitStarted)
    click.secho(
        "You are about to create an experiment.\n"
        "This wizard will walk you through each step so that you can build\n"
        "the best experiment for your needs.\n"
        "\n"
        "An experiment is made up of three elements:\n"
        "- a steady-state hypothesis [OPTIONAL]\n"
        "- an experimental method\n"
        "- a set of rollback activities [OPTIONAL]\n"
        "\n"
        "Only the method is required. Also your experiment will\n"
        "not run unless you define at least one activity (probe or action)\n"
        "within it",
        fg="blue",
    )

    discovery = None
    if discovery_path and os.path.exists(discovery_path):
        with open(discovery_path) as d:
            discovery = json.loads(d.read())
    else:
        click.echo("No discovery was found, let's create an empty experiment")

    base_experiment = {"title": "", "description": "N/A", "tags": []}

    s = click.style

    title = click.prompt(s("Experiment's title", fg="green"), type=str)
    base_experiment["title"] = title

    click.secho(
        "\nA steady state hypothesis defines what 'normality' "
        "looks like in your system\n"
        "The steady state hypothesis is a collection of "
        "conditions that are used,\n"
        "at the beginning of an experiment, to decide if the "
        "system is in a recognised\n"
        "'normal' state. The steady state conditions are then "
        "used again when your experiment\n"
        " is complete to detect where your system may have "
        "deviated in an interesting,\n"
        "weakness-detecting way\n"
        "\n"
        "Initially you may not know what your steady state "
        "hypothesis is\n"
        "and so instead you might create an experiment "
        "without one\n"
        "This is why the stead state hypothesis is optional.",
        fg="blue",
    )
    m = s("Do you want to define a steady state hypothesis now?", dim=True)
    if click.confirm(m):
        hypo = {}

        title = click.prompt(s("Hypothesis's title", fg="green"), type=str)
        hypo["title"] = title
        hypo["probes"] = []

        if discovery:
            activities = []
            for a in discovery["activities"]:
                if a["type"] == "probe":
                    activities.append((a["name"], a))

            click.secho(
                "\nYou may now define probes that will determine\n"
                "the steady-state of your system.",
                fg="blue",
            )
            add_activities(activities, hypo["probes"], with_tolerance=True)

        base_experiment["steady-state-hypothesis"] = hypo

    if discovery:
        base_experiment["method"] = []
        click.secho(
            "\nAn experiment's method contains actions "
            "and probes. Actions\n"
            "vary real-world events in your system to determine if your\n"
            "steady-state hypothesis is maintained when those events occur.\n"
            "\n"
            "An experimental method can also contain probes to gather"
            " additional\n"
            "information about your system as your method is executed.",
            fg="blue",
        )

        m = s("Do you want to define an experimental method?", dim=True)
        if click.confirm(m):
            activities = [(a["name"], a) for a in discovery["activities"]]
            add_activities(activities, base_experiment["method"])

        click.secho(
            "\nAn experiment may optionally define a set of remedial"
            " actions\nthat are used to rollback the system to a given"
            " state.",
            fg="blue",
        )
        m = s("Do you want to add some rollbacks now?", dim=True)
        if click.confirm(m):
            rollbacks = []
            activities = []
            for a in discovery["activities"]:
                if a["type"] == "action":
                    activities.append((a["name"], a))
            add_activities(activities, rollbacks)
            base_experiment["rollbacks"] = rollbacks

    if is_yaml(experiment_path):
        output = yaml.dump(
            base_experiment, indent=4, default_flow_style=False, sort_keys=False
        )
    else:
        output = json.dumps(base_experiment, indent=4, default=encoder)

    with open(experiment_path, "w") as e:
        e.write(output)

    click.echo(f"\nExperiment created and saved in '{experiment_path}'")

    notify(settings, InitFlowEvent.InitCompleted, base_experiment)
    return base_experiment


###############################################################################
# Private functions
###############################################################################
def is_yaml(experiment_path: str) -> bool:
    _, ext = os.path.splitext(experiment_path)
    return ext.lower() in (".yaml", ".yml")


def add_activities(
    activities: List[Activity],
    pool: List[Activity],  # noqa: C901
    with_tolerance: bool = False,
):
    """
    Add activities to the given pool.
    """
    base_activity = {
        "type": None,
        "name": None,
        "provider": {
            "type": "python",
            "module": None,
            "func": None,
            "arguments": {},
        },
    }

    s = click.style
    echo = click.echo
    if len(activities) > 20:
        echo = click.echo_via_pager

    click.echo(s("Add an activity", fg="green"))
    echo(
        "\n".join(
            [f"{idx + 1}) {name}" for (idx, (name, a)) in enumerate(activities)]
        )
    )
    activity_index = click.prompt(
        s("Activity (0 to escape)", fg="green"), type=int
    )
    if not activity_index:
        return

    activity_index = activity_index - 1
    if activity_index > len(activities):
        click.secho("Please pick up a valid activity", fg="red", err=True)
        add_activities(activities, pool)
        return

    selected = activities[activity_index][1]
    selected_doc = selected.get("doc")
    if selected_doc:
        click.secho(f"\n{selected_doc}", fg="blue")
    m = s("Do you want to use this {a}?".format(a=selected["type"]), dim=True)
    if not click.confirm(m):
        m = s("Do you want to select another activity?", dim=True)
        if not click.confirm(m):
            return
        add_activities(activities, pool)

    activity = base_activity.copy()
    activity["name"] = selected["name"]
    activity["type"] = selected["type"]
    if with_tolerance:
        click.secho(
            "\nA steady-state probe requires a tolerance value, "
            "within which\n"
            "your system is in a recognised `normal` state.\n",
            fg="blue",
        )
        tolerance_value = click.prompt(
            s("What is the tolerance for this probe?", fg="green")
        )
        activity["tolerance"] = tolerance_value
    activity["provider"] = {"type": "python"}
    activity["provider"]["module"] = selected["mod"]
    activity["provider"]["func"] = selected["name"]
    activity["provider"]["arguments"] = {}

    click.secho(
        "\nYou now need to fill the arguments for this activity. Default\n"
        "values will be shown between brackets. You may simply press return\n"
        "to use it or not set any value.",
        fg="blue",
    )
    for arg in selected.get("arguments", []):
        arg_name = arg["name"]
        if arg_name in ("secrets", "configuration"):
            continue

        # None is a bit of a problem because for the prompt it means
        # no defaults. When the user doesn't want to set a value, then
        # the prompt keeps asking. So, we pretend the default for None
        # is actually the empty string.
        arg_default = None
        if "default" in arg:
            arg_default = arg["default"]
            if arg_default is None:
                arg_default = ""
        arg_type = portable_type_name_to_python_type(arg["type"])
        question = f"Argument's value for '{arg_name}'"
        m = s(question, fg="yellow")
        arg_value = click.prompt(
            m, default=arg_default, show_default=True, type=arg_type
        )

        # now, if the user didn't input anything and the default was
        # None, we override it back to None
        if "default" in arg:
            arg_default = arg["default"]
            if arg_default is None and arg_value == "":
                arg_value = None

        activity["provider"]["arguments"][arg["name"]] = arg_value
    pool.append(activity)

    m = s("Do you want to select another activity?", dim=True)
    if not click.confirm(m):
        return
    add_activities(activities, pool)
