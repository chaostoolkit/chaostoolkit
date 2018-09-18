# Chaos Toolkit - An Open API for Chaos Engineering

[![Version](https://img.shields.io/pypi/v/chaostoolkit.svg)](https://img.shields.io/pypi/v/chaostoolkit.svg)
[![License](https://img.shields.io/pypi/l/chaostoolkit.svg)](https://img.shields.io/pypi/l/chaostoolkit.svg)


[![Build Status](https://travis-ci.org/chaostoolkit/chaostoolkit.svg?branch=master)](https://travis-ci.org/chaostoolkit/chaostoolkit)
[![codecov](https://codecov.io/gh/chaostoolkit/chaostoolkit/branch/master/graph/badge.svg)](https://codecov.io/gh/chaostoolkit/chaostoolkit)


[![Downloads](https://pepy.tech/badge/chaostoolkit)](https://pepy.tech/project/chaostoolkit)
[![Docker Pulls](https://img.shields.io/docker/pulls/chaostoolkit/chaostoolkit.svg)](https://hub.docker.com/r/chaostoolkit/chaostoolkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/chaostoolkit.svg)](https://www.python.org/)
[![Requirements Status](https://requires.io/github/chaostoolkit/chaostoolkit/requirements.svg?branch=master)](https://requires.io/github/chaostoolkit/chaostoolkit/requirements/?branch=master)
[![Has wheel](https://img.shields.io/pypi/wheel/chaostoolkit.svg)](http://pythonwheels.com/)

Chaos Toolkit is a project whose mission is to provide a free, open and community-driven toolkit and API to all the various forms of chaos engineering tools that the community needs.

## Why the Chaos Toolkit?

The Chaos Toolkit has two main purposes:

* To provide a full chaos engineering implementation that simplifies the adoption of chaos engineering by providing an easy starting point for applying the discipline.
* To define an open API with the community so that any chaos experiment can be executed consistently using integrations with the many commercial, private and open source chaos implementations that are emerging.

![Chaos Toolkit](https://chaostoolkit.org/static/chaos-toolkit-schema.fbdfc57a.svg)

### Simplifying Adoption of Chaos Engineering

Firstly the Chaos Toolkit aims to make it simple and straightforward to run
experiments against your live system to build confidence in its behavior and learn about
potential weaknesses.

Following the 
[principles of chaos engineering][principles], the Chaos Toolkit aims to be the easiest way to apply these principles to your own complex, and even sometimes chaotic, systems.

[principles]: http://principlesofchaos.org/

### An Open API to Chaos Engineering

Secondly the Chaos Toolkit defines an [Open API][api] to Chaos Engineering through it's JSON/YAML-format experiment definition. The toolkit can be extended to integrate with any number of commercial, private and open source chaos implementations through probes (to measure steady-state before and after an experiment) and actions (to vary real-world events during an experiment).

[api]: http://chaostoolkit.org/reference/api/experiment/

## Install or Upgrade

### Install from Packages

Generally speaking, you can install it as follows:

```
$ pip install -U chaostoolkit
```

It is recommended that you create a Python virtual environment for running your chaos experiments. Full instructions for installing chaostoolkit and its requirements are available in the [installation documentation][install].

[install]: http://chaostoolkit.org/reference/usage/install/

### Download and run the bundle

While installing via packages gives you the most control over what to deploy,
you may also be interested in simply dowloading a standalone binary that can
be run as-is.

Download a copy from [here][download].

[download]: https://github.com/chaostoolkit/chaostoolkit-bundler

Whenever a new version is released, just download its copy again.

## Getting Started

Once you have installed the Chaos Toolkit you can use it through its simple command line tool. The tool's main job is to run your experiment and then 
generate a report of the findings from the experiment to then share with your team for discussion.

Running an experiment is as simple as:

```
$ chaos run experiment.json
```

The Chaos Toolkit takes experiments defined in a [JSON format][json] description file, encoded in JSON (YAML is also supported), and runs its steps sequentially. A full specifiction of this experiment description file can be found in the [main project documentation][api].

[json]: https://www.json.org/

![Chaos Toolkit Run Sample](https://github.com/chaosiq/demos/raw/master/openfaas/experiments/switching-gce-nodepool/chaostoolkit-run.gif)

## Extending the Chaos Toolkit

The Chaos Toolkit plays the experiment description that you provide to it. 
Experiments are made up of probes and actions (to vary real-world events during an experiment). We are always looking for community contribution and ideas around
what probes and actions you might need as you integrate chaos experiments through the Chaos Toolkit, into your own unique context and evironment.

If you have an idea for a new set of probes and actions that you'd like to share, please first consider raising a ticket or even joining our community slack to suggest your idea.

In terms of implementation, the [Chaos Toolkit currently supports][extend] probes and actions implemented as Python functions, separate processes or even remote HTTP calls. As long as your extensions conform to the [Chaos Toolkit API][api] you can then specify your own unique extensions in your experiment definitions. 

The core implementation of the Chaos Toolkit API can be found in the [chaostoolkit-lib][chaoslib] project.

[extend]: http://chaostoolkit.org/reference/extending/approaches/
[chaoslib]: https://github.com/chaostoolkit/chaostoolkit-lib

### Current Known Extensions

The following free and open source extensions are available for your probes
and/or actions:

Infrastructure/Platform Fault Injections:

* [chaostoolkit-kubernetes][chaoskube]: Kubernetes activities
* [chaostoolkit-cloud-foundry][chaoscf]: Cloud Foundry activities
* [chaostoolkit-aws][chaosaws]: AWS activities
* [chaostoolkit-azure][chaosazure]: Microsoft Azure activities
* [chaostoolkit-google-cloud][chaosgce]: Google Cloud Engine activities

Application Fault Injections:

* [chaostoolkit-gremlin][chaosgremlin]: Gremlin, Inc activities
* [chaostoolkit-toxiproxy][chaostoxy]: Toxy Proxy fault injections
* [chaostoolkit-spring][chaospring]: Spring Project fault injections

Observability:

* [chaostoolkit-prometheus][chaosprom]: Prometheus probes
* [chaostoolkit-slack][chaosslack]: Slack notifications
* [chaostoolkit-humio][chaoshumio]: Humio logging

[chaoskube]: https://github.com/chaostoolkit/chaostoolkit-kubernetes-support
[chaosgremlin]: https://github.com/chaostoolkit-incubator/chaostoolkit-gremlin
[chaosaws]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws
[chaosazure]: https://github.com/chaostoolkit-incubator/chaostoolkit-azure
[chaosgce]: https://github.com/chaostoolkit-incubator/chaostoolkit-google-cloud
[chaosprom]: https://github.com/chaostoolkit-incubator/chaostoolkit-prometheus
[chaoscf]: https://github.com/chaostoolkit-incubator/chaostoolkit-cloud-foundry
[chaosslack]: https://github.com/chaostoolkit-incubator/chaostoolkit-slack
[chaoshumio]: https://github.com/chaostoolkit-incubator/chaostoolkit-humio
[chaostoxy]: https://github.com/chaostoolkit-incubator/chaostoolkit-toxiproxy
[chaospring]: https://github.com/chaostoolkit-incubator/chaostoolkit-spring

## Get involved!

Chaos Toolkit's mission is to provide an open API to chaos engineering in all its forms. As such, we encourage and welcome you  to [join][join] our open community Slack team to discuss and share your experiments and needs with the community.
You can also use [StackOverflow][so] to ask any questions regarding using the
Chaos Toolkit or Chaos Engineering.

[join]: https://join.chaostoolkit.org/
[so]: https://stackoverflow.com/questions/ask?tags=chaostoolkit+chaosengineering

If you'd prefer not to use Slack then we welcome the raising of GitHub issues on this repo for any questions, requests, or discussions around the Chaos Toolkit.

Finally you can always email `contact@chaostoolkit.org` with any questions as well.
