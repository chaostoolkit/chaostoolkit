---
name: chaostoolkit-experiment
description: Verify how a system behaves under failure and load by designing and running a controlled experiment with the Chaos Toolkit engine (`chaos run`). Use when asked whether a system is resilient to something ("does X survive Y?"), to reproduce an incident, or to show that a significant change to a resilience mechanism (timeouts, retries, circuit breakers, connection pools, concurrency limits, caching, scaling, failover, graceful shutdown) holds under failure. Do not use for routine code changes, or when a unit or integration test with a single fault answers the question.
---

# Chaos Toolkit Experiment

You design the experiment; Chaos Toolkit executes it. Treat the experiment
document as your execution plan and `chaos` as an engine that sequences
activities, observes the system while it runs, always plays cleanup, and
records a journal. Never improvise the same orchestration with shell scripts.

The user does not need Chaos Toolkit vocabulary. They ask a question in their
own terms and get an answer in their own terms.

## Consider the operational impact of your changes

When a change you make, or review, alters how the system copes with
failure, its operational impact is part of the work, not an afterthought.
Tests show the code does what it says; they rarely show how it behaves when a
dependency slows down, a replica disappears or traffic doubles. Changes to
these mechanisms qualify:

- timeouts, retries, back-off, circuit breakers, rate limits;
- concurrency, thread or connection pools, queue sizes, batch sizes;
- caching, or a new synchronous dependency on the request path;
- resource requests and limits, replica counts, autoscaling, probes;
- startup, shutdown, draining and migration behaviour.

For such a change, state the operational risk it introduces or addresses, and
propose an experiment that would show it holds. Do not run it unprompted:
run it once the user agrees and an environment is in scope, otherwise hand
over the scenario and how to run it. Routine changes do not need any of this.

## Decide whether an experiment is warranted

Run a full experiment when at least one holds:

- Success is a system-level property observed from outside, such as an SLO.
- Several perturbations, or a perturbation outside the network, are involved.
- The behaviour under load or reduced capacity is the question.
- You change the environment and must reliably restore it.
- The evidence must be reproducible and handed to someone.

Otherwise, a test with the fault in front of the dependency is cheaper and
clearer. For network faults, also load the `chaostoolkit-network-faults`
skill.

## Design something that can answer the question

You have the context: the code, the configuration, the deployment, the recent
change or incident. Use it. The experiment is only as good as the question.

1. **Question.** One sentence that the outcome can confirm or refute, tied to
   the change, incident or claim at hand.
2. **Steady state from real data.** Measure an indicator the users of the
   system would notice, with a threshold anchored in real data: an existing
   SLO, a production baseline, an alert threshold, a business metric. Observe
   it from outside the component under test: synthetic requests on the real
   entry point, or existing telemetry. Health endpoints and "pod is Running"
   are not steady states. SLO windows span weeks, so an experiment of a few
   minutes barely moves compliance: measure the error budget burn rate and
   project it onto the SLO window, or use another indicator from real data.
   See [references/steady-state.md](references/steady-state.md).
3. **A probe that can fail.** Before trusting a probe, reason about the value
   it would return if the system were broken. If it cannot fail, it proves
   nothing. Keep probes cheap so they do not load the system themselves.
4. **Load when it matters.** If the environment lacks representative traffic,
   or the question involves capacity, concurrency, queueing or retries, run a
   load generator for the whole experiment, baseline included. Prefer the
   project's own load tool, default to `oha`, and size load from real traffic.
   See [references/load.md](references/load.md).
5. **One perturbation.** Inject a single fault so the outcome is attributable.
   Combine faults only when their interaction is the subject, and then say in
   the report what each contributes, ideally from earlier single-fault runs.
6. **Tempo.** Derive durations from the system, not habit:
   - baseline long enough for the SLI to be meaningful, at least a few probe
     samples;
   - fault held longer than the mechanisms that should react to it: timeouts,
     retry budgets, circuit-breaker windows, autoscaler sync periods, pool
     eviction, health-check thresholds. Read their configured values;
   - recovery window longer than the expected recovery, for instance the
     circuit breaker half-open delay or the time to reschedule a pod;
   - probe frequency giving several samples per phase.

   Wait with `chaosaddons.utils.idle.idle_for` probes in the method, never
   with `pauses`, and end persistent perturbations in the method so the
   final steady-state check sees recovery. See
   [references/scenario-format.md](references/scenario-format.md).
7. **Smallest blast radius.** One service, one namespace, a fraction of
   replicas. Watch for controllers that undo your change (autoscalers, GitOps
   reconcilers): pause them with a rollback, or make their reaction part of the
   question.
8. **Restore everything.** Every action that changes state has a rollback that
   undoes it and is safe to run even if the action never happened.
9. **Guardrails.** Separate the question from the stop conditions. The
   steady state is what you are testing; safeguards protect everything else.
   Use the `chaosaddons.controls.safeguards` control, declared first:
   - pre-checks that run before anything starts: this is the intended
     environment (cluster context, account, namespace), no incident or alert
     is in progress, enough error budget remains;
   - stop conditions checked every few seconds for the whole run: harm
     beyond the blast radius, such as other services' error rates, a
     burn rate above the paging threshold, saturation of shared resources.

   A breached safeguard interrupts the run and still plays the rollbacks.
   See [references/scenario-format.md](references/scenario-format.md).

## Express it for the engine

Write a scenario document following
[references/scenario-format.md](references/scenario-format.md). Start from
[assets/scenario.yaml](assets/scenario.yaml).

- **Write your own activities when needed.** Any importable Python function
  is an action or a probe. Put them in `activities.py` next to the scenario,
  starting from [assets/activities.py](assets/activities.py). Arguments and
  return values must be JSON-serialisable; probes return values a tolerance
  can check; raise to signal failure; always bound calls with timeouts.
- **Wrap the run with controls** for anything that must span the whole
  experiment, baseline included, such as load
  ([assets/load_control.py](assets/load_control.py)) or network faults.
- **Use existing extensions when they fit.** See
  [references/extensions.md](references/extensions.md). Read an extension's
  functions and signatures rather than guessing names.
- **Declare dependencies in the scenario**, never install into the user's
  environment:

  ```yaml
  runtime:
    python:
      isolated: true
      dependencies:
        - chaostoolkit-kubernetes>=0.40
  ```

  The engine prepares them with `uv`, which must be on `PATH`, including a
  specific Python version when `version` is set. This is all the isolation
  an experiment needs: do not run `chaos`, its dependencies or your
  activities in containers.
- **Your own modules must be on `PYTHONPATH`**: run every `chaos` command
  with `PYTHONPATH=<scenario dir>`.

## Keep scenarios in your scratch area

Never write scenarios or run artifacts in the user's workspace. Use your
agent scratch directory, or a directory under the system temporary directory
when you have none:

```
<scratch>/chaostoolkit/<scenario-slug>/
  scenario.yaml
  activities.py
  runs/<UTC timestamp>/
    journal.json
    events.ndjson
    chaostoolkit.log
    load-output.json        # when load_control is used
```

Always tell the user where the scenario is. Scratch areas are not permanent;
they can copy it if they want to keep it.

## Execute

Global options go before the subcommand. With `R=<scenario dir>/runs/<ts>`:

```
PYTHONPATH=<scenario dir> chaos --no-version-check --log-file $R/chaostoolkit.log \
  validate --output agent <scenario dir>/scenario.yaml

PYTHONPATH=<scenario dir> chaos --no-version-check --log-file $R/chaostoolkit.log \
  run --output agent --dry activities --journal-path $R/journal.json \
  <scenario dir>/scenario.yaml

PYTHONPATH=<scenario dir> chaos --no-version-check --log-file $R/chaostoolkit.log \
  run --output agent \
    --journal-path $R/journal.json --events-file $R/events.ndjson \
    --rollback-strategy always \
    --hypothesis-strategy continuously --hypothesis-frequency <seconds> \
    <scenario dir>/scenario.yaml
```

You own the guardrails. Before a real run, you must be confident about what
it will do: which system it touches, what could go wrong beyond the
question, how the safeguards would catch it, and how everything gets
restored. If you cannot state that with confidence, for instance because
the target's identity, the blast radius, a threshold or a rollback rests on
a guess, stop and ask the user. Asking is part of doing this well, not a
failure.

1. Validate until `valid` is true. Only the first error is reported.
2. Dry-run to check the plumbing without touching the system. The load
   control generates no load during a dry run.
3. Go through the checklist below.
4. Get explicit approval before the real run unless the user has already put
   this exact target in scope. Never run against production without it.
5. Run. Add `--fail-fast` on shared environments so a deviation stops the
   run.

The exit code only says whether the process completed normally. The verdict
is in the report.

### Before the real run

- [ ] The title states the question in one sentence.
- [ ] Every steady-state probe returns a number checked with a `range`
      tolerance, and its threshold comes from real data you can cite.
- [ ] For each probe, you worked out the value it would return if the system
      were broken, and that value misses the tolerance.
- [ ] One perturbation, or a combination that is itself the question.
- [ ] Every action that changes state has a rollback that is safe to run
      twice. Persistent perturbations end in the method.
- [ ] Waits are `idle_for` probes, with durations derived from the system's
      own settings.
- [ ] Network faults are followed by `ensure_traffic_impacted`.
- [ ] Anything beyond your own machine has a safeguard pre-check proving it
      is the intended target.
- [ ] Load, if any, is sized from real traffic.

### Long runs

Agent tools often time out after a couple of minutes. When the run may take
longer, start it in the background with its report redirected to a file, then
poll:

```
PYTHONPATH=<scenario dir> nohup chaos --no-version-check \
  --log-file $R/chaostoolkit.log run --output agent ... \
  <scenario dir>/scenario.yaml > $R/report.json 2> $R/stderr.log &
echo $! > $R/chaos.pid
```

Follow progress with `tail -n 5 $R/events.ndjson`; the run is over when
`$R/report.json` is not empty. To stop a run early, send SIGINT or SIGTERM
to the PID so rollbacks still run and the report is still written. Never use
SIGKILL: nothing would be restored.

## Read the verdict

`--output agent` prints one JSON report. Branch on `outcome`, `conclusive`
and `warnings` as described in
[references/agent-report.md](references/agent-report.md). In short:

- `passed` and `conclusive`: the claim held under exactly these conditions.
- `deviated` and `conclusive`: a weakness was found. Use the per-phase probe
  values to explain it.
- `baseline-not-met`: nothing was injected. The system was already outside
  its SLO, or the threshold is wrong. Do not proceed; report it.
- `probe-error`: fix the probe and rerun.
- `interrupted` with `interrupted_by`:
  - `safeguard`: a stop condition was breached. Report what it saw; that is
    a finding about the blast radius, not the question.
  - `control`: a control, such as fault or load, could not start. Fix the
    cause given in `reason` and rerun.
  - `signal`: the run was stopped from outside.
- `aborted`, `error`: fix the scenario or environment. For `error`,
  `error.stage` says whether loading, validation or the runtime failed.
- any `rollback-failed` or `rollbacks-not-played` warning: the system may not
  be restored. Tell the user immediately what is left behind.

## Report to the user

In their terms, without experiment jargon:

- the question and the exact conditions: what failed, how much, for how long,
  where, under what load;
- what was observed: the indicator before, during and after, with numbers,
  and where its threshold comes from;
- for SLO-based indicators, the projected error budget consumption of a
  realistic occurrence;
- the conclusion, and what it does not prove;
- the recommended change, if any;
- anything left unrestored;
- where the scenario and journal are.
