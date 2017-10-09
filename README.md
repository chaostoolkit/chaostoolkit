# chaostoolkit

[![Build Status](https://travis-ci.org/chaostoolkit/chaostoolkit.svg?branch=master)](https://travis-ci.org/chaostoolkit/chaostoolkit)
[![Docker Pulls](https://img.shields.io/docker/pulls/chaostoolkit/chaostoolkit.svg)](https://hub.docker.com/r/chaostoolkit/chaostoolkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/chaostoolkit.svg)](https://www.python.org/)
[![Requirements Status](https://requires.io/github/chaostoolkit/chaostoolkit/requirements.svg?branch=master)](https://requires.io/github/chaostoolkit/chaostoolkit/requirements/?branch=master)
[![Has wheel](https://img.shields.io/pypi/wheel/chaostoolkit.svg)](http://pythonwheels.com/)

A chaos engineering toolkit for your system and microservices.

## Context and Purpose

The chaostoolkit aims at making it simple and straightforward to run
experiments against your live system to observe its behavior and learn about
potential weaknesses.

The idea is that your system is complex and no matter how well you planned
 and designed, it would be challenging to claim anyone knows how it would 
 react under certain conditions.

Following in the steps of giants like Netflix or LinkedIn, we believe in the
[principles of chaos engineering][principles]. Creating the conditions to
stress your system should help your team become better at handling those
situations while allowing your system to evolve nicely.

[principles]: http://principlesofchaos.org/

The chaostoolkit is, as its name implies, a toolkit for you to run those
experiments at the platform and/or application level. For instance, by killing
a microservice, your experiment could probe the system for other services and
see the impact of tsuch a failure.

The goal is not to break things, though this is one way to run an experiment,
but to create the conditions of stress that can make you learn from your system.

## Install or Upgrade

Install, or upgrade, the Chaos Toolkit as follows:

```
$ pip install -U chaostoolkit
``` 

The Chaos Toolkit CLI expects [Python 3.5][py3k] or above and permissions to
install Python dependencies. It is worh installing it in a virtual environment.
Please, read the main documentation to [install chaostoolkit][install] and
learn more about the requirements.

[py3k]: https://www.python.org/
[install]: https://chaostoolkit.github.io/chaostoolkit/usage/install/

## Getting Started

chaostoolkit is a command line tool that runs your experiment, then 
generates a report to share with your team for discussion.

Running an experiment is as simple as:

```
$ chaos run experiment.json
```

chaostoolkit takes your experiment as a description file, encoded in JSON, and
runs its steps sequentially.

## Extend

The Chaos Toolkit command plays the experiment you feed it. Experiments are
made of probes and actions which you can implement yourself whenever existing
ones do not fit the bill.

chaostoolkit supports probes and actions implemented as Python function,
processes or remote HTTP calls. As long as they obey the Chaos Toolkit API,
they are good to be applied as part of your experiment.

### Known Extensions

The following extensions can be used for your probes and/or actions:

* [chaostoolkit-kubernetes][chaoskube]: Kubernetes interactions

[chaoskube]: https://github.com/chaostoolkit/chaostoolkit-kubernetes-support

## Learn More

chaostoolkit is open and [you are more than welcome][join] to discuss and share
your experiments with its community.

[join]: https://join.chaostoolkit.org/
