# Load during experiments

Many weaknesses only appear under traffic: exhausted connection pools,
growing queues, retry storms, autoscaling lag, thread starvation. Light probes
alone do not create that pressure.

## When to add load

- The target sees little or no traffic, as staging environments often do.
- The question involves capacity, concurrency, queueing, back-pressure,
  retries or autoscaling.
- The perturbation removes capacity: lost replicas, drained nodes, a slower
  dependency holding connections longer.

Do not add load when the environment already carries representative traffic,
or when the question is about a single request path such as a timeout value.

## Tool

Use the load tool the project already has (k6, Locust, Gatling, vegeta, hey
scripts in the repository), since it knows the real traffic mix. Otherwise
default to `oha`:

```
oha --no-tui -j -z 5m -q 50 -c 10 http://127.0.0.1:8080/checkout
```

`-q` is the rate in requests per second, `-c` the number of concurrent
connections, `-z` the duration, `-j` a JSON summary on stdout (also printed
when interrupted). Check `oha --help` for headers, methods and bodies.

## Sizing

Size load from real data: production requests per second on that endpoint at
a typical peak, scaled to the environment's capacity, or a fraction stated
explicitly. Say how you chose it. Never point load at production, or at a
shared dependency such as a payment sandbox, without explicit approval.

## Running it for the whole experiment

Load has to be present during the baseline too, otherwise the baseline and
the fault are measured under different conditions. Use
[`assets/load_control.py`](../assets/load_control.py) as an experiment-level
control:

```yaml
controls:
  - name: load
    provider:
      type: python
      module: load_control
      arguments:
        url: "${entrypoint}"
        rate: 50
        connections: 10
        warmup: 20
        run_dir: /abs/runs/<ts>
```

It starts the generator before the baseline, waits `warmup` seconds, and
stops it after the rollbacks. Pass `command: [k6, run, script.js]` to use
another tool; it must run until interrupted with SIGINT. The generator's
output lands in `run_dir` and, for oha, a summary (throughput, success rate,
p50/p95/p99, status codes, errors) is added to the journal under `load`.

The load generator's summary covers the whole run. Per-phase evidence still
comes from the steady-state probes, which now measure the system under load.
