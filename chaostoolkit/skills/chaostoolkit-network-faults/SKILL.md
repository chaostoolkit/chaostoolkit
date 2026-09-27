---
name: chaostoolkit-network-faults
description: Inject network faults (latency, jitter, bandwidth limits, blackholes, connection resets, DNS failures) into a Chaos Toolkit experiment through fault's engine. Use together with chaostoolkit-experiment whenever an experiment degrades or cuts traffic between a client and a dependency. Do not use for application-level faults such as HTTP error injection.
---

# Network Faults in Chaos Toolkit Experiments

Network faults always go through fault. Do not use `tc`, `iptables`,
toxiproxy, service-mesh fault injection or the network actions of Chaos
Toolkit extensions.

For fault semantics, flows, fault chains and realistic failure mappings, use
the `fault-network-injection` skill and fault's
[agent reference](https://fault-project.com/agent-reference.md). Fault
specifications here use exactly the same shapes as in a fault run document.
This skill covers how fault runs inside a Chaos Toolkit experiment.

## How it fits together

[assets/fault_control.py](assets/fault_control.py) drives fault's engine
through `faultlib`, fault's Python binding. Copy it next to the scenario so it
is on `PYTHONPATH` with your other activities.

- **faultlib needs Python 3.14+.** Declare it and let the engine prepare it:

  ```yaml
  runtime:
    python:
      version: "3.14"
      dependencies: ["faultlib>=1.0"]
  ```

- **The control owns the proxies.** Declared under `controls` with the
  proxies to bind, it starts them healthy before the baseline, so the
  baseline is measured on the same path as the fault, and shuts them down
  after the rollbacks.
- **The method owns the timing.** `set_faults` changes the fault chains of
  named proxies immediately; `clear_faults` makes them healthy again. Hold a
  fault, and later observe recovery, with `chaosaddons.utils.idle.idle_for`
  probes between them.
- **Always verify the fault reached traffic.** Add the
  `ensure_traffic_impacted` probe to the method after the hold. If the
  application does not actually route through the proxy, it fails, the report
  carries `method-activity-failed` and the outcome is inconclusive instead of
  a false pass.
- **Rollbacks always clear.** Declare `clear_faults` as a rollback. It is safe
  whether or not fault is running.
- **Observe throughout.** Run with `--hypothesis-strategy continuously` and a
  frequency giving several samples while the fault is held and while the
  system recovers.
- **Load, when used, comes second.** Declare the `fault` control before the
  `load` control from `chaostoolkit-experiment`, so the proxies are up before
  traffic flows.

Start from [assets/scenario.yaml](assets/scenario.yaml).

## Routing

Pointing the application at the proxy is a precondition, not part of the
method:

- Prefer an existing address override: an environment variable such as
  `DATABASE_URL`, a config file entry, a command-line flag. Never change
  application code.
- If routing requires a restart or a rollout, do it before `chaos run`, and
  let the baseline confirm the system is healthy through the proxy. A restart
  inside the method would confound the result.
- For TLS dependencies, keep the real hostname for SNI and certificate
  checks, for instance through the client's dial override or local name
  resolution. Never disable certificate verification.
- Restore the original routing after the run, and say so in the report.
- Never redirect production traffic through a proxy without explicit
  approval.

The proxies run inside the `chaos` process, from the `faultlib` dependency
prepared by uv: there is nothing else to install, package or deploy. This
works when the application can reach the machine running `chaos`, for
instance when it runs locally. When it cannot, such as inside a cluster,
fault would have to run next to the application instead. This skill does not
cover that case: tell the user rather than work around it.

## Designing the fault

- One proxy and one fault chain, unless the interaction is the question.
  `set_faults` accepts several proxies at once; they change one after the
  other within the same call.
- Match the fault to the failure you mean: a slow dependency is client-bound
  `latency`; pod or load-balancer rotation is a `connection-reset` with a
  probability; a partition is a `blackhole`; a resolver outage is `dns` with
  `timeout` or `serv-fail`.
- Size magnitude and hold from the client's configuration. Latency just below
  a timeout and just above it answer different questions. Hold the fault
  longer than retries, circuit-breaker windows and pool timeouts.
- There is no HTTP status or packet-loss fault. Use the closest transport
  behaviour (`connection-reset`, `blackhole`) and say so, or do not test it.

## Evidence

After the run, the journal has a `fault` entry with:

- the proxy endpoints;
- every fault change with its `applied_at` timestamp;
- fault's final transport counters: streams or exchanges opened, impacted
  and failed, applied latency;
- the number of records per proxy and the paths to `fault-records.ndjson`
  (one line per TCP stream or UDP exchange) and `fault-changes.ndjson`.

Line up the change timestamps with the steady-state samples taken during the
method to show when the indicator broke and recovered. Evidence is best
effort: if `dropped_records` is not zero, say so. fault records what it did to
the network; the probes record how the application behaved. Keep the two
apart in the report.
