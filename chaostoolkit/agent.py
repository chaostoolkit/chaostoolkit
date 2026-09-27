"""
Reports produced with `--output agent`.

Each command writes a single JSON document on stdout once it is done. The
document is derived deterministically from what the command observed, the
journal in the case of a run, so an agent can branch on a handful of stable
fields rather than interpret logs or re-derive a verdict from the journal:

* `outcome`: one of the `Outcome` values, chosen by fixed precedence
* `conclusive`: whether the outcome actually answers the question asked
* `warnings`: stable codes for anything that weakens or qualifies the outcome

The process exit code is unchanged by this output mode. It still reflects
whether the process went through normally, while the report reflects what
the experiment found.
"""

import json
import os
from enum import StrEnum
from typing import Any

import click
from chaoslib.types import Experiment, Journal

from chaostoolkit.events import bounded_output, safe_encoder

__all__ = [
    "RUN_SCHEMA",
    "VALIDATE_SCHEMA",
    "Outcome",
    "WarningCode",
    "classify",
    "emit",
    "relay_child_report",
    "run_error_report",
    "run_report",
    "validate_report",
]

RUN_SCHEMA = "chaostoolkit/agent/run/v1"
VALIDATE_SCHEMA = "chaostoolkit/agent/validate/v1"


class Outcome(StrEnum):
    # the steady state held before, during and after the method
    PASSED = "passed"
    # the steady state held before the method but not during or after it
    DEVIATED = "deviated"
    # the steady state did not hold before the method: nothing was injected
    BASELINE_NOT_MET = "baseline-not-met"
    # a steady-state probe raised so its tolerance could not be evaluated
    PROBE_ERROR = "probe-error"
    # the method ran into an unexpected error
    ABORTED = "aborted"
    # the run was interrupted by a signal or a control
    INTERRUPTED = "interrupted"
    # the run could not start: invalid source, experiment or runtime
    ERROR = "error"


class WarningCode(StrEnum):
    # activities were not executed, the outcome says nothing about the system
    DRY_RUN = "dry-run"
    # no probes to judge the system with, the run only explored
    NO_STEADY_STATE_HYPOTHESIS = "no-steady-state-hypothesis"
    # an action or probe of the method failed, the perturbation may not have
    # been applied as intended
    METHOD_ACTIVITY_FAILED = "method-activity-failed"
    # declared rollbacks were not all played, the system may not be restored
    ROLLBACKS_NOT_PLAYED = "rollbacks-not-played"
    # a rollback failed, the system may not be restored
    ROLLBACK_FAILED = "rollback-failed"


# warnings that prevent the outcome from answering the question
INCONCLUSIVE_WARNINGS = frozenset(
    {
        WarningCode.DRY_RUN,
        WarningCode.NO_STEADY_STATE_HYPOTHESIS,
        WarningCode.METHOD_ACTIVITY_FAILED,
    }
)

WARNING_MESSAGES = {
    WarningCode.DRY_RUN: "Activities were not executed (dry run: {dry}).",
    WarningCode.NO_STEADY_STATE_HYPOTHESIS: (
        "The experiment has no steady-state probes, nothing was judged."
    ),
    WarningCode.METHOD_ACTIVITY_FAILED: (
        "Method activities failed, the perturbation may not have been "
        "applied: {names}."
    ),
    WarningCode.ROLLBACKS_NOT_PLAYED: (
        "Only {played} of {declared} declared rollbacks were played, the "
        "system may not be restored."
    ),
    WarningCode.ROLLBACK_FAILED: (
        "Rollbacks failed, the system may not be restored: {names}."
    ),
}


def emit(report: dict[str, Any]) -> None:
    click.echo(
        json.dumps(report, indent=2, ensure_ascii=False, default=safe_encoder)
    )


def classify(journal: Journal) -> Outcome:
    """
    Precedence, from the least to the most trustworthy verdict:
    interrupted, aborted, probe-error, baseline-not-met, deviated, passed.
    """
    status = journal.get("status")
    if status == "interrupted" or _swallowed_interruption(journal):
        return Outcome.INTERRUPTED
    if status == "aborted":
        return Outcome.ABORTED

    before, during, after = _states(journal)
    for state in [before, *during, after]:
        if not state:
            continue
        for probe in state.get("probes") or []:
            if probe.get("status") != "succeeded":
                return Outcome.PROBE_ERROR

    if before and before.get("steady_state_met") is False:
        return Outcome.BASELINE_NOT_MET

    if _deviated_phases(journal):
        return Outcome.DEVIATED

    # with --fail-fast, the continuous hypothesis marks the run as failed
    # once it deviated, which is caught above. Any other failed status is
    # the result of a probe error, also caught above.
    return Outcome.PASSED


def run_report(
    journal: Journal,
    *,
    source: str,
    journal_path: str,
    exit_code: int,
    events_path: str | None = None,
) -> dict[str, Any]:
    experiment = journal.get("experiment") or {}
    before, during, after = _states(journal)
    outcome = classify(journal)
    warnings = _warnings(journal, experiment)
    codes = {w["code"] for w in warnings}
    conclusive = outcome in (Outcome.PASSED, Outcome.DEVIATED) and not (
        codes & INCONCLUSIVE_WARNINGS
    )

    return {
        "schema": RUN_SCHEMA,
        "command": "run",
        "outcome": outcome.value,
        "conclusive": conclusive,
        "verdict": _verdict(outcome, journal),
        "exit_code": exit_code,
        "source": _location(source),
        "journal_path": os.path.abspath(journal_path),
        "events_path": os.path.abspath(events_path) if events_path else None,
        "experiment": {
            "title": experiment.get("title"),
            "dry": experiment.get("dry"),
        },
        "journal": {
            "status": journal.get("status"),
            "deviated": journal.get("deviated", False),
            "start": journal.get("start"),
            "end": journal.get("end"),
            "duration": journal.get("duration"),
        },
        "steady_state": {
            "before": _state_detail(before),
            "during": _during_detail(during),
            "after": _state_detail(after),
        },
        "method": {
            "count": len(journal.get("run") or []),
            "failed": _failed_runs(journal.get("run")),
        },
        "rollbacks": {
            "declared": len(experiment.get("rollbacks") or []),
            "played": len(journal.get("rollbacks") or []),
            "failed": _failed_runs(journal.get("rollbacks")),
        },
        "interrupted_by": _interrupted_by(journal),
        "warnings": warnings,
        "error": None,
    }


def run_error_report(
    stage: str,
    exc: BaseException,
    *,
    source: str,
    exit_code: int = 1,
) -> dict[str, Any]:
    return {
        "schema": RUN_SCHEMA,
        "command": "run",
        "outcome": Outcome.ERROR.value,
        "conclusive": False,
        "verdict": f"The experiment could not be run: {stage} failed.",
        "exit_code": exit_code,
        "source": _location(source),
        "journal_path": None,
        "events_path": None,
        "experiment": None,
        "journal": None,
        "steady_state": None,
        "method": None,
        "rollbacks": None,
        "interrupted_by": None,
        "warnings": [],
        "error": _error(stage, exc),
    }


def relay_child_report(
    child: Any, command: str, source: str, stage: str = "runtime"
) -> int:
    """
    Wait for a runtime child process whose stdout was captured, forward its
    report, or emit an error report when it exited without one, typically
    because uv could not prepare the runtime. Return the child's exit code.
    """
    out = child.stdout.read() if child.stdout is not None else ""
    exit_code = child.wait()
    if out.strip():
        click.echo(out, nl=False)
        return exit_code

    message = (
        f"the experiment runtime exited with {exit_code} before reporting, "
        "most likely because uv could not prepare it: see stderr"
    )
    exc = RuntimeError(message)
    if command == "validate":
        emit(validate_report(source, stage=stage, exc=exc))
    else:
        emit(run_error_report(stage, exc, source=source, exit_code=exit_code))
    return exit_code


def validate_report(
    source: str,
    experiment: Experiment | None = None,
    stage: str | None = None,
    exc: BaseException | None = None,
) -> dict[str, Any]:
    return {
        "schema": VALIDATE_SCHEMA,
        "command": "validate",
        "valid": exc is None,
        "source": _location(source),
        "title": (experiment or {}).get("title"),
        "error": _error(stage, exc) if exc is not None else None,
    }


def _states(
    journal: Journal,
) -> tuple[dict | None, list[dict], dict | None]:
    steady_states = journal.get("steady_states") or {}
    during = [s for s in steady_states.get("during") or [] if s]
    return steady_states.get("before"), during, steady_states.get("after")


def _deviated_phases(journal: Journal) -> list[str]:
    _, during, after = _states(journal)
    phases = []
    if any(s.get("steady_state_met") is False for s in during):
        phases.append("during")
    if after and after.get("steady_state_met") is False:
        phases.append("after")
    return phases


def _verdict(outcome: Outcome, journal: Journal) -> str:
    if outcome is Outcome.PASSED:
        before, during, after = _states(journal)
        phases = [
            name
            for name, state in (
                ("before", before),
                ("during", during),
                ("after", after),
            )
            if state
        ]
        if not phases:
            return "The run completed without evaluating a steady state."
        return f"The steady state held {_join(phases)} the method."
    if outcome is Outcome.DEVIATED:
        before, _, _ = _states(journal)
        deviated = _join(_deviated_phases(journal))
        if not before:
            return (
                f"The steady state did not hold {deviated} the method, no "
                "baseline was evaluated before it."
            )
        return f"The steady state held before the method but not {deviated} it."
    if outcome is Outcome.BASELINE_NOT_MET:
        return (
            "The steady state did not hold before the method, nothing was "
            "injected."
        )
    if outcome is Outcome.PROBE_ERROR:
        return (
            "A steady-state probe could not be executed, its tolerance "
            "could not be evaluated."
        )
    if outcome is Outcome.ABORTED:
        return "The method ran into an unexpected error, the run was aborted."
    by = _interrupted_by(journal)
    if by and by["kind"] == "safeguard":
        return (
            f"The run was interrupted by the safeguard '{by['name']}' before "
            "it completed."
        )
    if by and by["kind"] == "control":
        return (
            f"The run was interrupted by the control '{by['name']}': "
            f"{by['reason']}"
        )
    if by:
        return f"The run was interrupted before it completed: {by['reason']}"
    return "The run was interrupted before it completed."


def _warnings(journal: Journal, experiment: Experiment) -> list[dict[str, Any]]:
    warnings = []

    def add(code: WarningCode, **details: Any) -> None:
        warnings.append(
            {
                "code": code.value,
                "message": WARNING_MESSAGES[code].format(**details),
            }
        )

    dry = experiment.get("dry")
    if dry:
        add(WarningCode.DRY_RUN, dry=dry)

    hypothesis = experiment.get("steady-state-hypothesis") or {}
    if not hypothesis.get("probes"):
        add(WarningCode.NO_STEADY_STATE_HYPOTHESIS)

    failed = [r["name"] for r in _failed_runs(journal.get("run"))]
    if failed:
        add(WarningCode.METHOD_ACTIVITY_FAILED, names=", ".join(failed))

    declared = len(experiment.get("rollbacks") or [])
    played = len(journal.get("rollbacks") or [])
    if played < declared:
        add(WarningCode.ROLLBACKS_NOT_PLAYED, played=played, declared=declared)

    failed = [r["name"] for r in _failed_runs(journal.get("rollbacks"))]
    if failed:
        add(WarningCode.ROLLBACK_FAILED, names=", ".join(failed))

    return warnings


def _interrupted_by(journal: Journal) -> dict[str, Any] | None:
    """
    What interrupted the run, when the journal tells:

    * a safeguard, as recorded by `chaosaddons.controls.safeguards`;
    * a control, as recorded under `interruption` by the controls bundled
      with the skills when they fail to start;
    * an interruption raised while an activity ran, which older versions of
      chaostoolkit-lib recorded as a failure of that activity.
    """
    swallowed = _swallowed_interruption(journal)
    if journal.get("status") != "interrupted" and not swallowed:
        return None

    safeguards = journal.get("safeguards") or {}
    name = safeguards.get("triggered_by")
    if not name:
        interruption = journal.get("interruption")
        if isinstance(interruption, dict) and interruption.get("reason"):
            return {
                "kind": interruption.get("kind") or "control",
                "name": interruption.get("name"),
                "reason": interruption["reason"],
            }
        if swallowed:
            return {"kind": "signal", "name": None, "reason": swallowed}
        return None
    run = safeguards.get("run") or {}
    detail = {
        "kind": "safeguard",
        "name": name,
        "status": run.get("status"),
        "tolerance": (run.get("activity") or {}).get("tolerance"),
        **bounded_output(run.get("output")),
    }
    if run.get("exception"):
        detail["error"] = _last_line(run["exception"])
    return detail


SWALLOWED_INTERRUPTION = (
    "chaoslib.exceptions.ActivityFailed: chaoslib.exceptions.InterruptExecution"
)


def _swallowed_interruption(journal: Journal) -> str | None:
    """
    Older chaostoolkit-lib versions turned an interruption raised while a
    Python activity ran, on SIGTERM for instance, into a failure of that
    activity and carried on. Return the interruption's reason if so.
    """
    before, during, after = _states(journal)
    runs = list(journal.get("run") or []) + list(journal.get("rollbacks") or [])
    for state in [before, *during, after]:
        if state:
            runs.extend(state.get("probes") or [])
    for run in runs:
        for line in run.get("exception") or []:
            line = line.strip()
            if line.startswith(SWALLOWED_INTERRUPTION):
                reason = line[len(SWALLOWED_INTERRUPTION) :].lstrip(": ")
                return reason or "interrupted"
    return None


def _state_detail(state: dict[str, Any] | None) -> dict[str, Any] | None:
    if not state:
        return None
    return {
        "met": state.get("steady_state_met"),
        "probes": [_probe_detail(p) for p in state.get("probes") or []],
    }


def _probe_detail(probe: dict[str, Any]) -> dict[str, Any]:
    activity = probe.get("activity") or {}
    detail = {
        "name": activity.get("name"),
        "status": probe.get("status"),
        "tolerance_met": probe.get("tolerance_met"),
        "tolerance": activity.get("tolerance"),
        **bounded_output(probe.get("output")),
    }
    if probe.get("exception"):
        detail["error"] = _last_line(probe["exception"])
    return detail


def _during_detail(during: list[dict[str, Any]]) -> dict[str, Any]:
    unmet = [
        (index, s)
        for index, s in enumerate(during, start=1)
        if s.get("steady_state_met") is False
    ]
    probes = sorted(
        {
            (p.get("activity") or {}).get("name")
            for _, s in unmet
            for p in s.get("probes") or []
            if p.get("tolerance_met") is False
        }
    )
    return {
        "iterations": len(during),
        "unmet": len(unmet),
        "first_unmet_iteration": unmet[0][0] if unmet else None,
        "unmet_probes": probes,
    }


def _failed_runs(runs: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    failed = []
    for run in runs or []:
        if run.get("status") != "failed":
            continue
        failed.append(
            {
                "name": (run.get("activity") or {}).get("name"),
                "error": _last_line(run.get("exception") or []),
            }
        )
    return failed


def _error(stage: str | None, exc: BaseException) -> dict[str, Any]:
    return {
        "stage": stage,
        "type": type(exc).__name__,
        "message": str(exc),
    }


def _last_line(exception: list[str]) -> str | None:
    lines = "".join(exception).strip().splitlines()
    return lines[-1] if lines else None


def _join(phases: list[str]) -> str:
    if len(phases) == 1:
        return phases[0]
    return ", ".join(phases[:-1]) + " and " + phases[-1]


def _location(source: str) -> str:
    if "://" in source:
        return source
    return os.path.abspath(source)
