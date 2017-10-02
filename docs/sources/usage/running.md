# Running the Chaos Toolkit

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

You can initially perform a dry run:

```
(venv) $ chaos run --dry my-plan.json
```

`chaostoolkit` will log all the steps it follows from your plan.

If you run the command from a container, you may use a command such as:

```
$ docker run --rm -it \
    --user `id -u` \
    -v $HOME/.kube:/root/.kube \
    -v $HOME/.minikube:$HOME/.minikube \
    -v `pwd`:/tmp/chaos \
    chaostoolkit/chaostoolkit run /tmp/chaos/my-plan.json
```

This command snippet shows how you would share your [Kubernetes][kube]
 and [minikube][] configurations if your experiment targets Kubernetes.

[kube]: https://kubernetes.io/
[minikube]: https://github.com/kubernetes/minikube
