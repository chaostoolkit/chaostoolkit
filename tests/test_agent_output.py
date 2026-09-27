import json

import pytest
from click.testing import CliRunner

from chaostoolkit.agent import (
    RUN_SCHEMA,
    VALIDATE_SCHEMA,
    Outcome,
    classify,
    run_report,
)
from chaostoolkit.cli import cli
from chaostoolkit.events import MAX_OUTPUT_SIZE

BASE_ARGS = ["--no-version-check", "--no-log-file"]


def _exists_probe(path):
    return {
        "type": "probe",
        "name": "file-exists",
        "tolerance": True,
        "provider": {
            "type": "python",
            "module": "os.path",
            "func": "exists",
            "arguments": {"path": str(path)},
        },
    }


def _noop(name="noop"):
    return {
        "type": "probe",
        "name": name,
        "provider": {
            "type": "python",
            "module": "os.path",
            "func": "basename",
            "arguments": {"p": "/a/target"},
        },
    }


def _write(path, probes=None, method=None, rollbacks=None):
    experiment = {
        "title": "agent output",
        "description": "agent output",
        "method": method if method is not None else [_noop()],
    }
    if probes is not None:
        experiment["steady-state-hypothesis"] = {
            "title": "h",
            "probes": probes,
        }
    if rollbacks is not None:
        experiment["rollbacks"] = rollbacks
    path.write_text(json.dumps(experiment))
    return path


def _run(tmp_path, experiment, *args):
    return CliRunner().invoke(
        cli,
        [
            *BASE_ARGS,
            "run",
            "--output",
            "agent",
            "--journal-path",
            str(tmp_path / "journal.json"),
            *args,
            str(experiment),
        ],
    )


def _report(result):
    return json.loads(result.stdout)


@pytest.fixture
def target(tmp_path):
    t = tmp_path / "target"
    t.write_text("x")
    return t


def test_run_passed(tmp_path, target):
    exp = _write(tmp_path / "e.json", probes=[_exists_probe(target)])

    result = _run(tmp_path, exp)

    assert result.exit_code == 0
    report = _report(result)
    assert report["schema"] == RUN_SCHEMA
    assert report["outcome"] == "passed"
    assert report["conclusive"] is True
    assert report["verdict"] == (
        "The steady state held before and after the method."
    )
    assert report["exit_code"] == 0
    assert report["source"] == str(exp)
    assert report["journal_path"] == str(tmp_path / "journal.json")
    assert report["events_path"] is None
    assert report["warnings"] == []
    assert report["error"] is None
    assert report["journal"]["status"] == "completed"
    probe = report["steady_state"]["before"]["probes"][0]
    assert probe == {
        "name": "file-exists",
        "status": "succeeded",
        "tolerance_met": True,
        "tolerance": True,
        "output": True,
    }


def test_run_baseline_not_met_keeps_process_exit_code(tmp_path):
    exp = _write(
        tmp_path / "e.json", probes=[_exists_probe(tmp_path / "missing")]
    )

    result = _run(tmp_path, exp)

    # the process went through normally, the verdict is in the report
    assert result.exit_code == 0
    report = _report(result)
    assert report["outcome"] == "baseline-not-met"
    assert report["conclusive"] is False
    assert report["exit_code"] == 0
    assert report["method"]["count"] == 0


def test_run_deviated_after(tmp_path, target):
    remove = {
        "type": "action",
        "name": "remove-target",
        "provider": {
            "type": "python",
            "module": "os",
            "func": "remove",
            "arguments": {"path": str(target)},
        },
    }
    exp = _write(
        tmp_path / "e.json", probes=[_exists_probe(target)], method=[remove]
    )

    result = _run(tmp_path, exp)

    assert result.exit_code == 1
    report = _report(result)
    assert report["outcome"] == "deviated"
    assert report["conclusive"] is True
    assert report["verdict"] == (
        "The steady state held before the method but not after it."
    )
    assert report["steady_state"]["after"]["met"] is False


def test_run_probe_error(tmp_path):
    probe = {
        "type": "probe",
        "name": "kaboom",
        "tolerance": True,
        "provider": {
            "type": "python",
            "module": "tests.fixtures.force_failure",
            "func": "kaboom",
        },
    }
    exp = _write(tmp_path / "e.json", probes=[probe], method=[])

    result = _run(tmp_path, exp)

    assert result.exit_code == 1
    report = _report(result)
    assert report["outcome"] == "probe-error"
    assert report["conclusive"] is False
    assert report["steady_state"]["before"]["probes"][0]["error"]


def test_run_failed_method_activity_is_inconclusive(tmp_path, target):
    broken = {
        "type": "action",
        "name": "inject",
        "provider": {
            "type": "python",
            "module": "tests.fixtures.force_failure",
            "func": "kaboom",
        },
    }
    exp = _write(
        tmp_path / "e.json", probes=[_exists_probe(target)], method=[broken]
    )

    report = _report(_run(tmp_path, exp))

    assert report["outcome"] == "passed"
    assert report["conclusive"] is False
    assert [w["code"] for w in report["warnings"]] == ["method-activity-failed"]
    assert report["method"]["failed"][0]["name"] == "inject"


def test_run_rollbacks_not_played_and_failed(tmp_path, target):
    broken = {
        "type": "action",
        "name": "undo",
        "provider": {
            "type": "python",
            "module": "tests.fixtures.force_failure",
            "func": "kaboom",
        },
    }
    exp = _write(
        tmp_path / "e.json", probes=[_exists_probe(target)], rollbacks=[broken]
    )

    report = _report(_run(tmp_path, exp, "--rollback-strategy", "never"))
    assert [w["code"] for w in report["warnings"]] == ["rollbacks-not-played"]
    assert report["rollbacks"] == {"declared": 1, "played": 0, "failed": []}
    # the question was still answered
    assert report["conclusive"] is True

    report = _report(_run(tmp_path, exp, "--rollback-strategy", "always"))
    assert [w["code"] for w in report["warnings"]] == ["rollback-failed"]
    assert report["rollbacks"]["failed"][0]["name"] == "undo"


def test_run_dry_and_no_hypothesis_are_inconclusive(tmp_path):
    exp = _write(tmp_path / "e.json")

    report = _report(_run(tmp_path, exp, "--dry", "activities"))

    assert report["outcome"] == "passed"
    assert report["conclusive"] is False
    assert report["verdict"] == (
        "The run completed without evaluating a steady state."
    )
    assert [w["code"] for w in report["warnings"]] == [
        "dry-run",
        "no-steady-state-hypothesis",
    ]


def test_run_large_probe_output_is_left_to_the_journal(tmp_path):
    probe = {
        "type": "probe",
        "name": "big",
        "tolerance": {"type": "regex", "pattern": "x+"},
        "provider": {
            "type": "python",
            "module": "textwrap",
            "func": "indent",
            "arguments": {"text": "x" * MAX_OUTPUT_SIZE, "prefix": ""},
        },
    }
    exp = _write(tmp_path / "e.json", probes=[probe])

    report = _report(_run(tmp_path, exp))

    detail = report["steady_state"]["before"]["probes"][0]
    assert detail["output_truncated"] is True
    assert "output" not in detail


def test_run_events_file(tmp_path, target):
    exp = _write(tmp_path / "e.json", probes=[_exists_probe(target)])
    events_path = tmp_path / "events.ndjson"

    result = _run(tmp_path, exp, "--events-file", str(events_path))

    assert result.exit_code == 0
    assert _report(result)["events_path"] == str(events_path)
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    types = [e["type"] for e in events]
    assert types[0] == "run-started"
    assert types[-1] == "run-finished"
    assert "method-started" in types
    assert all("timestamp" in e for e in events)
    noop = next(
        e
        for e in events
        if e["type"] == "activity-completed" and e["name"] == "noop"
    )
    assert noop["output"] == "target"


def test_run_events_file_works_with_text_output(tmp_path, target):
    exp = _write(tmp_path / "e.json", probes=[_exists_probe(target)])
    events_path = tmp_path / "events.ndjson"

    result = CliRunner().invoke(
        cli,
        [
            *BASE_ARGS,
            "run",
            "--journal-path",
            str(tmp_path / "journal.json"),
            "--events-file",
            str(events_path),
            str(exp),
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert events_path.read_text()


@pytest.mark.parametrize("content,stage", [({}, "validation"), (None, "load")])
def test_run_error_report(tmp_path, content, stage):
    exp = tmp_path / "e.json"
    if content is not None:
        exp.write_text(json.dumps({"title": "t", "description": "d"}))

    result = _run(tmp_path, exp)

    assert result.exit_code == 1
    report = _report(result)
    assert report["outcome"] == "error"
    assert report["conclusive"] is False
    assert report["journal_path"] is None
    assert report["error"]["stage"] == stage
    assert report["error"]["type"]
    assert report["error"]["message"]


def test_validate_report_valid(tmp_path, target):
    exp = _write(tmp_path / "e.json", probes=[_exists_probe(target)])

    result = CliRunner().invoke(
        cli, [*BASE_ARGS, "validate", "--output", "agent", str(exp)]
    )

    assert result.exit_code == 0
    assert _report(result) == {
        "schema": VALIDATE_SCHEMA,
        "command": "validate",
        "valid": True,
        "source": str(exp),
        "title": "agent output",
        "error": None,
    }


@pytest.mark.parametrize("content,stage", [({}, "validation"), (None, "load")])
def test_validate_report_invalid(tmp_path, content, stage):
    exp = tmp_path / "e.json"
    if content is not None:
        exp.write_text(json.dumps({"title": "t", "description": "d"}))

    result = CliRunner().invoke(
        cli, [*BASE_ARGS, "validate", "--output", "agent", str(exp)]
    )

    assert result.exit_code == 1
    report = _report(result)
    assert report["valid"] is False
    assert report["error"]["stage"] == stage
    assert report["error"]["message"]


def _state(met=True, status="succeeded"):
    return {
        "steady_state_met": met,
        "probes": [
            {
                "activity": {"name": "p"},
                "status": status,
                "tolerance_met": met,
            }
        ],
    }


def _journal(
    status="completed", deviated=False, before=None, during=None, after=None
):
    return {
        "status": status,
        "deviated": deviated,
        "experiment": {"title": "t"},
        "steady_states": {
            "before": before,
            "during": during or [],
            "after": after,
        },
        "run": [],
        "rollbacks": [],
    }


@pytest.mark.parametrize(
    "journal,expected",
    [
        (_journal(before=_state(), after=_state()), Outcome.PASSED),
        (_journal(before=_state(met=False)), Outcome.BASELINE_NOT_MET),
        (
            _journal(deviated=True, before=_state(), after=_state(met=False)),
            Outcome.DEVIATED,
        ),
        # deviation seen only by the continuous hypothesis
        (
            _journal(
                before=_state(), during=[_state(met=False)], after=_state()
            ),
            Outcome.DEVIATED,
        ),
        # --fail-fast marks the run as failed once it deviated
        (
            _journal(
                status="failed", before=_state(), during=[_state(met=False)]
            ),
            Outcome.DEVIATED,
        ),
        (
            _journal(
                status="failed", before=_state(met=False, status="failed")
            ),
            Outcome.PROBE_ERROR,
        ),
        (_journal(status="aborted", deviated=True), Outcome.ABORTED),
        (_journal(status="interrupted", deviated=True), Outcome.INTERRUPTED),
    ],
)
def test_classify(journal, expected):
    assert classify(journal) is expected


def test_during_detail():
    during = [_state(), _state(met=False), _state(met=False)]
    report = run_report(
        _journal(before=_state(), during=during, after=_state()),
        source="e.json",
        journal_path="j.json",
        exit_code=0,
    )
    assert report["steady_state"]["during"] == {
        "iterations": 3,
        "unmet": 2,
        "first_unmet_iteration": 2,
        "unmet_probes": ["p"],
    }
    assert report["verdict"] == (
        "The steady state held before the method but not during it."
    )


def test_deviated_verdict_without_baseline():
    report = run_report(
        _journal(during=[_state(met=False)]),
        source="e.json",
        journal_path="j.json",
        exit_code=0,
    )
    assert report["outcome"] == "deviated"
    assert report["verdict"] == (
        "The steady state did not hold during the method, no baseline was "
        "evaluated before it."
    )


def test_interrupted_by_safeguard():
    journal = _journal(status="interrupted", before=_state())
    journal["safeguards"] = {
        "triggered_by": "error-rate",
        "run": {
            "activity": {"name": "error-rate", "tolerance": [0, 1]},
            "status": "succeeded",
            "output": 4.2,
        },
    }

    report = run_report(
        journal, source="e.json", journal_path="j.json", exit_code=1
    )

    assert report["outcome"] == "interrupted"
    assert report["interrupted_by"] == {
        "kind": "safeguard",
        "name": "error-rate",
        "status": "succeeded",
        "tolerance": [0, 1],
        "output": 4.2,
    }
    assert report["verdict"] == (
        "The run was interrupted by the safeguard 'error-rate' before it "
        "completed."
    )


def test_interrupted_without_safeguard():
    report = run_report(
        _journal(status="interrupted"),
        source="e.json",
        journal_path="j.json",
        exit_code=1,
    )
    assert report["interrupted_by"] is None


def test_swallowed_interruption_is_never_a_pass():
    journal = _journal(before=_state(), after=_state())
    journal["run"] = [
        {
            "activity": {"name": "hold"},
            "status": "failed",
            "exception": [
                "Traceback (most recent call last):\n",
                (
                    "chaoslib.exceptions.ActivityFailed: "
                    "chaoslib.exceptions.InterruptExecution: SIGTERM signal "
                    "received\n"
                ),
            ],
        }
    ]

    report = run_report(
        journal, source="e.json", journal_path="j.json", exit_code=0
    )

    assert report["outcome"] == "interrupted"
    assert report["conclusive"] is False
    assert report["interrupted_by"] == {
        "kind": "signal",
        "name": None,
        "reason": "SIGTERM signal received",
    }
    assert report["verdict"] == (
        "The run was interrupted before it completed: SIGTERM signal received"
    )


def test_interrupted_by_control_start_failure():
    journal = _journal(status="interrupted")
    journal["interruption"] = {
        "kind": "control",
        "name": "fault",
        "reason": "fault could not start: Address already in use",
    }

    report = run_report(
        journal, source="e.json", journal_path="j.json", exit_code=1
    )

    assert report["interrupted_by"] == journal["interruption"]
    assert report["verdict"] == (
        "The run was interrupted by the control 'fault': fault could not "
        "start: Address already in use"
    )


def test_activity_printing_does_not_corrupt_the_report(tmp_path, target):
    probe = {
        "type": "probe",
        "name": "chatty",
        "provider": {
            "type": "python",
            "module": "builtins",
            "func": "print",
            "arguments": {"sep": "", "end": "noise on stdout\n"},
        },
    }
    exp = _write(
        tmp_path / "e.json", probes=[_exists_probe(target)], method=[probe]
    )

    result = _run(tmp_path, exp)

    assert result.exit_code == 0
    assert "noise on stdout" not in result.stdout
    assert _report(result)["outcome"] == "passed"


def _child(stdout, exit_code):
    import io
    from unittest.mock import MagicMock

    run_child = MagicMock()
    child = run_child.return_value.__enter__.return_value
    child.stdout = io.StringIO(stdout)
    child.wait.return_value = exit_code
    return run_child


def _runtime_experiment(tmp_path):
    exp = tmp_path / "e.json"
    exp.write_text(
        json.dumps(
            {
                "title": "t",
                "description": "d",
                "runtime": {"python": {"dependencies": ["nope-xyz==9"]}},
                "method": [],
            }
        )
    )
    return exp


@pytest.mark.parametrize("command", ["run", "validate"])
def test_runtime_child_without_report(tmp_path, monkeypatch, command):
    from importlib import import_module

    module = import_module(f"chaostoolkit.commands.{command}")
    run_child = _child("", 2)
    monkeypatch.setattr(module, "supervised_runtime", run_child)
    exp = _runtime_experiment(tmp_path)

    result = CliRunner().invoke(
        cli, [*BASE_ARGS, command, "--output", "agent", str(exp)]
    )

    assert result.exit_code == 2
    assert run_child.call_args.kwargs["capture_stdout"] is True
    report = _report(result)
    assert report["error"]["stage"] == "runtime"
    assert "uv could not prepare it" in report["error"]["message"]
    if command == "run":
        assert report["outcome"] == "error"
        assert report["exit_code"] == 2
    else:
        assert report["valid"] is False


def test_runtime_child_report_is_relayed(tmp_path, monkeypatch):
    from importlib import import_module

    module = import_module("chaostoolkit.commands.run")
    child_report = json.dumps({"schema": RUN_SCHEMA, "outcome": "passed"})
    monkeypatch.setattr(
        module, "supervised_runtime", _child(child_report + "\n", 0)
    )
    exp = _runtime_experiment(tmp_path)

    result = CliRunner().invoke(
        cli, [*BASE_ARGS, "run", "--output", "agent", str(exp)]
    )

    assert result.exit_code == 0
    assert _report(result) == {"schema": RUN_SCHEMA, "outcome": "passed"}
