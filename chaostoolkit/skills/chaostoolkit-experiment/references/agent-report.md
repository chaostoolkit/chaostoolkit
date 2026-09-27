# Agent report

`chaos run --output agent` and `chaos validate --output agent` print a single
JSON document on stdout when they finish. Logs go to stderr and the log file.
Stdout carries the report only: anything activities or controls print goes
to stderr. When the uv runtime cannot be prepared, the report is still
written, with `outcome` `error` and `error.stage` `runtime`.

The process exit code is `1` when the journal status is not `completed`, when
the journal is flagged as deviated, or when the run could not start, and `0`
otherwise. A run whose baseline was not met therefore exits with `0`. Base
decisions on the report, not on the exit code.

## Run report

```json
{
  "schema": "chaostoolkit/agent/run/v1",
  "command": "run",
  "outcome": "deviated",
  "conclusive": true,
  "verdict": "The steady state held before the method but not during it.",
  "exit_code": 1,
  "source": "/abs/scenario.yaml",
  "journal_path": "/abs/runs/<ts>/journal.json",
  "events_path": "/abs/runs/<ts>/events.ndjson",
  "experiment": {"title": "...", "dry": null},
  "journal": {"status": "completed", "deviated": false,
              "start": "...", "end": "...", "duration": 93.2},
  "steady_state": {
    "before": {"met": true, "probes": [
      {"name": "p95-latency", "status": "succeeded", "tolerance_met": true,
       "tolerance": {"type": "range", "range": [0, 300]}, "output": 41.2}]},
    "during": {"iterations": 30, "unmet": 7, "first_unmet_iteration": 12,
               "unmet_probes": ["p95-latency"]},
    "after": {"met": true, "probes": ["..."]}
  },
  "method": {"count": 3, "failed": []},
  "rollbacks": {"declared": 1, "played": 1, "failed": []},
  "interrupted_by": null,
  "warnings": [],
  "error": null
}
```

Probe outputs larger than 4 KB are replaced by `output_truncated` and
`output_size`; read them from the journal. Per-iteration values observed
during the method are in the journal under `steady_states.during`, with
timestamps you can line up with `events.ndjson`.

## Outcome

Chosen by fixed precedence, first match wins:

| Outcome | Meaning | Next step |
| --- | --- | --- |
| `error` | The run could not start. `error.stage` is `load`, `validation` or `runtime`. | Fix the scenario or environment. |
| `interrupted` | A signal, a control or a safeguard stopped the run. See `interrupted_by`. | Act on `interrupted_by`, check what is left behind. |
| `aborted` | The method raised unexpectedly. | Fix the activity. |
| `probe-error` | A steady-state probe raised, its tolerance could not be evaluated. | Fix the probe, rerun. No verdict. |
| `baseline-not-met` | The steady state did not hold before the method. Nothing was injected. | Stop. The system is already outside its SLO or the threshold is wrong. Report it. |
| `deviated` | The steady state broke during or after the method. | A finding: explain it with the probe values. |
| `passed` | The steady state held for every evaluated phase. | Evidence for the claim, under these conditions only. |

`interrupted_by` is null unless the journal tells what interrupted the run:

| `kind` | Fields | Meaning |
| --- | --- | --- |
| `safeguard` | `name`, `status`, `tolerance`, `output` | A safeguard missed its tolerance with that output. |
| `control` | `name`, `reason` | A bundled control (`fault`, `load`) could not start. |
| `signal` | `reason` | The run was interrupted from outside, e.g. SIGTERM. |

`conclusive` is true only for `passed` or `deviated` without any of the
warnings `dry-run`, `no-steady-state-hypothesis` or `method-activity-failed`.
An inconclusive `passed` means nothing was really tested.

## Warnings

| Code | Meaning |
| --- | --- |
| `dry-run` | Activities were not executed. |
| `no-steady-state-hypothesis` | No probes judged the system. |
| `method-activity-failed` | A method activity failed, the perturbation may not have happened. `method.failed` lists them. |
| `rollbacks-not-played` | Fewer rollbacks played than declared. The system may not be restored. |
| `rollback-failed` | A rollback failed. The system may not be restored. `rollbacks.failed` lists them. |

## Validate report

```json
{
  "schema": "chaostoolkit/agent/validate/v1",
  "command": "validate",
  "valid": false,
  "source": "/abs/scenario.yaml",
  "title": "...",
  "error": {"stage": "validation", "type": "InvalidActivity",
            "message": "The python module 'activities' does not expose a function called 'nope' in probe 'p95-latency'"}
}
```

Validation imports Python activities, so a missing module usually means
`PYTHONPATH` or `runtime.python.dependencies` is incomplete.

## Events file

`--events-file PATH` appends one JSON object per line while the run
progresses: `run-started`, `hypothesis-started` / `hypothesis-completed`
(with `phase` `before`, `during` or `after`), `method-started`,
`activity-started` / `activity-completed`, `rollbacks-started` /
`rollbacks-completed`, `run-finished`. Follow it to monitor a long run; the
report remains the verdict.
