# Existing extensions

Extensions are Python packages exposing actions and probes as plain
functions. Use them through the `python` provider with the module and
function name, and declare the package in `runtime.python.dependencies`.

| Package | Module | Covers |
| --- | --- | --- |
| `chaostoolkit-kubernetes` | `chaosk8s` | deployments, pods, nodes, services, events |
| `chaostoolkit-aws` | `chaosaws` | EC2, ECS, EKS, ASG, Lambda, RDS, ELB, CloudWatch, FIS... |
| `chaostoolkit-google-cloud-platform` | `chaosgcp` | GKE, Cloud Run, Cloud SQL, load balancers, monitoring... |
| `chaostoolkit-azure` | `chaosazure` | AKS, VMs, scale sets, app services... |
| `chaostoolkit-prometheus` | `chaosprometheus` | PromQL probes, good SLI sources; also declare `logzero` |
| `chaostoolkit-addons` | `chaosaddons` | controls: safeguards (pre-checks, stop conditions), repeat, bypass |

Each area usually has an `actions` and a `probes` module, e.g.
`chaosk8s.deployment.actions`, `chaosaws.ecs.probes`.

## Look functions up, do not guess them

Inspect the package in a throwaway environment, without touching the user's:

```
uv run --no-project --with chaostoolkit-kubernetes \
  python -m pydoc chaosk8s.deployment.actions

uv run --no-project --with chaostoolkit-kubernetes python -c \
  "import inspect, chaosk8s.pod.actions as m; \
   [print(n, inspect.signature(getattr(m, n))) for n in m.__all__]"
```

Examples of what you will find:

- `chaosk8s.deployment.actions.scale_deployment(name, replicas, ns)`
- `chaosk8s.pod.actions.terminate_pods(label_selector, qty, grace_period, ns, ...)`:
  `grace_period=0` is closer to abrupt compute loss than a graceful scale down
- `chaosk8s.node.actions.drain_nodes(name, label_selector, count, ...)`
- `chaosprometheus.probes.query(query, when)` returns the Prometheus API
  response, check it with a `jsonpath` or `probe` tolerance

Extensions pick up credentials the usual way for their platform (kubeconfig,
AWS profile, application default credentials) or through `secrets`.

## Network faults

Do not use network fault actions from extensions, such as
`chaosk8s.chaosmesh.network`, or ad-hoc tools like `tc` or `iptables`.
Network faults go through `fault`; see the `chaostoolkit-network-faults` skill.

## When nothing fits

Write the function yourself in `activities.py`. A few lines around the
platform's SDK or CLI are usually clearer than bending the scenario around an
extension. Declare the SDK in `runtime.python.dependencies`.
