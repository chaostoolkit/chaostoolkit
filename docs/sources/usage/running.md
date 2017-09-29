## Run

The `chaostoolkit` CLI will display commands it supports as follows:

```
(venv) $ chaos --help
```

### Executing a plan

The main function of the `chaostoolkit` CLI is to execute the plan you
declared. This is done as follows:

```
(venv) $ chaos run my-plan.json
```

You caninitially perform a dry run:

```
(venv) $ chaos run --dry my-plan.json
```

`chaostoolkit` will log all the steps it follows from your plan.