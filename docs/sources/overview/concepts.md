# Chaos Engeering Concepts in the Chaos Toolkit

If you haven't already, we strongly recommend reading the fantastic [Chaos Engineering][chaos-engingeering-book] book from O'Reilly Media. This book will give you some fantastic background on the whole Chaos Engineering discipline, and it's free!

[chaos-engingeering-book]: http://www.oreilly.com/webops-perf/free/chaos-engineering.csp

Chaos Engineering is a discipline that allows you to surface weaknesses, and eventually build confidence, in complex and often distributed systems. 

The Chaos Toolkit aims to give you the simplest experience for writing and running your own Chaos Engineering experiments. The main concepts are all expressed in an experiment definition, of which the following is an example from the [Chaos Toolkit Samples](https://github.com/chaostoolkit/chaostoolkit-samples) project:

```json
{
    "title": "System is resilient to provider's failures",
    "description": "Can our consumer survive gracefully a provider's failure?",
    "target-layers": {
        "platforms": [
            { "key": "kubernetes" }
        ],
        "applications": [
            { "key": "spring" }
        ]
    },
    "method": [
        {
            "title": "Checking our system is healthy",
            "probes": {
                "steady": {
                    "layer": "kubernetes",
                    "name": "microservices-all-healthy"
                }
            }
        },
        {
            "title": "Killing the provider abruptly",
            "action": {
                "layer": "kubernetes",
                "name": "kill-microservice",
                "parameters": {
                    "name": "my-provider-service"
                },
                "pauses": {
                    "after": 10
                }
            },
            "probes": {
                "steady": {
                    "layer": "kubernetes",
                    "name": "microservice-available-and-healthy",
                    "parameters": {
                        "name": "my-provider-service"
                    }
                },
                "close": {
                    "layer": "kubernetes",
                    "name": "microservice-is-not-available",
                    "parameters": {
                        "name": "my-provider-service"
                    }
                }
            }
        },
        {
            "title": "Consumer should not be impacted by provider's failure",
            "probes": {
                "steady": {
                    "layer": "spring",
                    "name": "endpoint-should-respond-ok",
                    "parameters": {
                        "url": "http://192.168.99.100:32220/invokeConsumedService"
                    }
                }
            }
        }
    ]
}
```

The key concepts of the Chaos Toolkit are `Experiments`, `Target Layers` and the experiment's `Method`. The `Method` contains a combination of `Probes` and `Actions`.

## Experiments

A Chaos Toolkit experiment is provided in a single file and is currently expressed in JSON.

## Target Layers

A target layer is in fact a collection of extensions that allow the experiment to target specific systems to apply the experiment to. Out of the box support for Kubernetes (Platform layer) and Spring (Application Layer) is currently provided and we intend to extend this out rapidly into other technologies.

When you execute an experiment's probes and actions it is against a particular target layer.

## Method

An experiment's activities are contained within its `Method` block.

## Probes

A probe is a way of detecting a particular set of conditions in the system that is undergoing experimentation.

## Actions

An action is a particular activity that needs to be enacted on the system under experimentation.

