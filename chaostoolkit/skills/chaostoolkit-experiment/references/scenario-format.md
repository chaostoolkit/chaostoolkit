# Scenario format

A scenario is a Chaos Toolkit experiment document in YAML or JSON. This is the
subset that matters for building one.

## Top level

```yaml
title: checkout keeps its latency SLO when a replica is lost   # required
description: why this is being tested                          # required
tags: [checkout]
configuration: {}            # values substituted as ${name}
secrets: {}                  # credentials, kept out of the journal
runtime: {}                  # Python dependencies prepared with uv
controls: []                 # code wrapped around the whole run
steady-state-hypothesis: {}  # the SLO, as probes with tolerances
method: []                   # the perturbation and its pacing, in order
rollbacks: []                # cleanup
```

## Execution order

1. Experiment-level controls start (`before_experiment_control`).
2. The steady-state hypothesis runs as a baseline. If it is not met, the method
   is skipped: nothing is injected.
3. The method runs activity by activity, in order. With
   `--hypothesis-strategy continuously` or `during-method-only`, the
   hypothesis also runs every `--hypothesis-frequency` seconds while the method
   runs.
4. The hypothesis runs again after the method, unless the strategy excludes it.
5. Rollbacks run. With `--rollback-strategy always`, they run whatever
   happened, including after an interruption.
6. Experiment-level controls stop (`after_experiment_control`).

Background activities (`background: true`) start and the method moves on
without waiting. The method only ends once they have all completed.

## Activities

Probes observe, actions change. Both use the same shape:

```yaml
- type: probe                 # or action
  name: p95-latency           # unique, used by `ref` and in the report
  provider:
    type: python
    module: activities        # must be importable, see PYTHONPATH
    func: p95_latency_ms
    arguments: {url: "${entrypoint}", samples: 20}
  background: false
```

## Waiting

Hold a perturbation or leave time to recover with a probe from
`chaostoolkit-addons`, not with the `pauses` property of an activity:

```yaml
- type: probe
  name: hold-degraded
  provider:
    type: python
    module: chaosaddons.utils.idle
    func: idle_for
    arguments: {duration: 90}
```

The wait is then an activity of its own: recorded in the journal and the
events file with its start, end and duration, skipped by dry runs, and it
checks for interruption every 0.1s. `pauses` sleep inside another activity's
run and leave no trace of their own.

The final steady-state check runs right after the method, before the
rollbacks. End a persistent perturbation in the method, then wait for the
recovery window, so that check observes recovery rather than the degraded
system. Keep the undo in the rollbacks as well, in case the method is cut
short.

Other providers:

```yaml
provider:
  type: process
  path: kubectl                       # resolved on PATH
  arguments: [get, pods, -n, shop]    # or a single string
  timeout: 30
# output: {status: <exit code>, stdout: str, stderr: str}

provider:
  type: http
  url: https://shop.example.com/health
  method: GET
  timeout: 5
  headers: {Accept: application/json}
# output: {status: <http status>, headers: {}, body: <str or parsed json>}
```

Reuse an activity declared elsewhere with `- ref: p95-latency`.

For Python providers, the engine passes `configuration` and `secrets` only
when the function declares parameters with those names. A function that
raises makes the activity fail: in the method, the run carries on; in the
hypothesis, the probe is reported as an error.

## Tolerances

Only hypothesis probes carry a `tolerance`. Pick the form matching the probe's
return value:

| Tolerance | Met when |
| --- | --- |
| `true` / `false` | value equals it |
| `200` (integer) | value equals it, or `value["status"]` does |
| `[200, 204]` | value, or `value["status"]`, is one of them |
| `[0, 300]` (two numbers) | **treated as an inclusive range** |
| `{type: range, range: [0, 300], target: key}` | numeric value, or `value[target]`, in range |
| `{type: regex, pattern: "ok", target: stdout}` | regex found in value, or `value[target]` |
| `{type: jsonpath, path: "$.status", expect: "UP", target: body}` | path matches, and equals `expect` if given; `count` checks the number of matches |
| `{type: probe, name: x, provider: {...}}` | the given function returns truthy; it receives the probe output as its `value` argument |

Floats are not accepted as literal tolerances; use `range`. Probes run in order
and the hypothesis stops at the first unmet one, so put the most important SLI
first.

## Configuration and secrets

```yaml
configuration:
  entrypoint: "http://127.0.0.1:8080/checkout"
  namespace:
    type: env
    key: TARGET_NAMESPACE
    default: staging

secrets:
  k8s:
    token:
      type: env
      key: K8S_TOKEN
```

Use `${entrypoint}` in arguments. Override values for a run with
`--var namespace=prod-eu` or `--var-file values.yaml`, so one scenario can be
replayed against another target. A Python activity receives secrets when its
provider lists their groups, `secrets: [k8s]`, and the function declares a
`secrets` parameter.

## Runtime

```yaml
runtime:
  python:
    isolated: true        # fresh environment, pinned to the running chaos
    version: "3.12"       # optional, implies isolated
    dependencies:
      - chaostoolkit-kubernetes>=0.40
      - httpx>=0.27
```

## Controls

Controls wrap the run with code. A Python module declared at the top level can
implement `configure_control`, `before_experiment_control`,
`after_experiment_control`, `cleanup_control` and `validate_control`. Raise
`chaoslib.exceptions.InterruptExecution` from a control to stop the run; other
exceptions are only logged.

```yaml
controls:
  - name: fault
    provider:
      type: python
      module: fault_control
      arguments:
        run_dir: /abs/runs/1
        proxies:
          - {name: database, protocol: tcp, listen: "127.0.0.1:15432", upstream: "database:5432"}
```

Controls are applied in declaration order: declare safeguards first, then the
controls that start things (fault proxies, then load), so pre-checks run
before anything is started.

### Safeguards

`chaostoolkit-addons` provides `chaosaddons.controls.safeguards`. Declare
`chaostoolkit-addons` in `runtime.python.dependencies`.

```yaml
controls:
  - name: safeguards
    provider:
      type: python
      module: chaosaddons.controls.safeguards
      arguments:
        probes:
          # no frequency nor background: pre-check, blocks until done,
          # before the baseline
          - name: intended-cluster
            type: probe
            tolerance: {type: regex, pattern: "^staging-", target: stdout}
            provider: {type: process, path: kubectl, arguments: [config, current-context]}
          # frequency: stop condition, checked every N seconds all run long
          - name: platform-error-rate
            type: probe
            frequency: 5
            tolerance: {type: range, range: [0, 0.02]}
            provider:
              type: python
              module: activities
              func: error_ratio
              arguments: {url: "${platform_health_url}"}
```

A probe with `background: true` and no `frequency` runs once, without
blocking. When any safeguard misses its tolerance, the run is interrupted
gracefully: rollbacks are played and controls stop. The journal records the
safeguard under `safeguards`, which the agent report exposes as
`interrupted_by`. Older releases of `chaostoolkit-addons` do not record it: when
`interrupted_by` is null, find `Safeguard '<name>' triggered the end of the
experiment` in the log file. Keep safeguard probes fast; a slow one can delay the end of
the run.

### Other addons controls

- `chaosaddons.controls.repeat`, declared on an activity with
  `repeat_count`, runs it several times in a row, for instance to kill a pod
  repeatedly.
- `chaosaddons.controls.bypass`, with `target_names` or `target_type`, skips
  matching activities while keeping them in the scenario.
