# Steady state from real data

The steady state must be anchored in real data about the system: an actual
SLO, production telemetry, an existing alert, a business metric. Never invent
a threshold. When there is no data, say so, derive the threshold from
something explicit (a client timeout, a contractual limit), label it as such
in the report, or ask the user.

## Why an SLO alone rarely works

SLOs are evaluated over long rolling windows, typically 28 or 30 days. A
10-minute experiment is 0.02% of a 30-day window: even a total outage during
the experiment barely moves compliance, so "the SLO is still met" says
nothing. Use one of the approaches below.

## Option 1: burn rate and projection

Keep the real SLO (its SLI definition, target and window) and measure how fast
the experiment consumes its error budget.

```
bad_ratio   = bad events / total events       during the fault
budget      = 1 - slo_target                  e.g. 0.001 for 99.9%
burn_rate   = bad_ratio / budget
consumed    = burn_rate * duration / window   share of the window's budget
```

- **Steady state:** the burn rate stays below a meaningful threshold. The
  best threshold is the organisation's own burn-rate alert: look for alert
  rules in the repository or monitoring configuration. Otherwise, common
  multi-window values for a 30-day window are 14.4 (2% of the budget in 1h,
  paging), 6 (5% in 6h, paging) and 1 (10% in 3 days, ticket). Say which you
  used and why.
- **Projection:** report what a real occurrence would cost. Use a realistic
  duration for this failure in production (incident history, time to detect
  and mitigate) rather than the experiment duration:
  `consumed = burn_rate * realistic_duration / window`. Compare it with the
  budget remaining in the current window when telemetry provides it.
- `assets/activities.py` provides `burn_rate(url, slo_target, samples,
  latency_threshold_ms)` for request-based SLIs. For telemetry-based SLIs,
  compute the bad ratio from the monitoring system over the probe interval.

Example report line: "During the 3-minute database slowdown, checkout burned
its latency error budget 38x faster than sustainable. A 20-minute occurrence
in production would consume 1.8% of the monthly budget and trigger the fast
burn page."

## Option 2: other indicators from real data

When there is no formal SLO, or the question is not about one, use an
indicator grounded in how the system really behaves:

- the production or staging baseline of an SLI, for instance p95 latency or
  error ratio over the last 7 days, with a stated margin;
- the threshold of an existing alert;
- a business or user-facing metric: checkout success, messages processed,
  queue lag, time to first byte;
- a saturation signal tied to the question: connection pool usage, queue
  depth, consumer lag.

Query the source (Prometheus, cloud monitoring, logs) for the baseline value
before writing the tolerance, and cite that query and value in the report.

## Probes

- Observe from outside the component: the entry point users hit, or
  telemetry of that entry point.
- Several samples per probe, so one slow request does not decide the outcome,
  but cheap enough not to load the system.
- Return a number and check it with a `range` tolerance.
- Reason about the value the probe would return if the system were broken. If
  it cannot fail, it proves nothing.
