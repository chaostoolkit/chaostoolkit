# Chaos Toolkit - An Open API for Chaos Engineering

[![Version](https://img.shields.io/pypi/v/chaostoolkit.svg)](https://img.shields.io/pypi/v/chaostoolkit.svg)
[![License](https://img.shields.io/pypi/l/chaostoolkit.svg)](https://img.shields.io/pypi/l/chaostoolkit.svg)


[![Build](https://github.com/chaostoolkit/chaostoolkit/workflows/Build/badge.svg)](https://github.com/chaostoolkit/chaostoolkit/actions?query=workflow%3ABuild)


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

![Chaos Toolkit](https://docs.chaostoolkit.org/static/images/schema-1920.svg)

### Simplifying Adoption of Chaos Engineering

Firstly the Chaos Toolkit aims to make it simple and straightforward to run
experiments against your live system to build confidence in its behavior and learn about
potential weaknesses.

Following the 
[principles of chaos engineering][principles], the Chaos Toolkit aims to be the easiest way to apply these principles to your own complex, and even sometimes chaotic, systems.

[principles]: http://principlesofchaos.org/

### An Open API to Chaos Engineering

Secondly the Chaos Toolkit defines an [Open API][api] to Chaos Engineering through it's JSON/YAML-format experiment definition. The toolkit can be extended to integrate with any number of commercial, private and open source chaos implementations through probes (to measure steady-state before and after an experiment) and actions (to vary real-world events during an experiment).

[api]: https://docs.chaostoolkit.org/reference/api/experiment/

## Install or Upgrade

### Install from Packages

Generally speaking, you can install it as follows:

```
$ pip install -U chaostoolkit
```

It is recommended that you create a Python virtual environment for running your chaos experiments. Full instructions for installing chaostoolkit and its requirements are available in the [installation documentation][install].

[install]: https://docs.chaostoolkit.org/reference/usage/install/

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

[extend]: https://docs.chaostoolkit.org/reference/extending/approaches/
[chaoslib]: https://github.com/chaostoolkit/chaostoolkit-lib

### Current Known Extensions

The Chaos Toolkit is made of [many extensions][ext] that you can simply download
and add to your environment to use.

[ext]: https://pypi.org/search/?q=chaostoolkit

## Get involved!

Chaos Toolkit's mission is to provide an open API to chaos engineering in all its forms. As such, we encourage and welcome you  to [join][join] our open community Slack team to discuss and share your experiments and needs with the community.
You can also use [StackOverflow][so] to ask any questions regarding using the
Chaos Toolkit or Chaos Engineering.

[join]: https://join.chaostoolkit.org/
[so]: https://stackoverflow.com/questions/ask?tags=chaostoolkit+chaosengineering

If you'd prefer not to use Slack then we welcome the raising of GitHub issues on this repo for any questions, requests, or discussions around the Chaos Toolkit.

Finally you can always email `contact@chaostoolkit.org` with any questions as well.

## Contribute

Contributors to this project are welcome as this is an open-source effort that
seeks [discussions][join] and continuous improvement.

[join]: https://join.chaostoolkit.org/

From a code perspective, if you wish to contribute, you will need to run a 
Python 3.5+ environment. Then, fork this repository and submit a PR. The
project cares for code readability and checks the code style to match best
practices defined in [PEP8][pep8]. Please also make sure you provide tests
whenever you submit a PR so we keep the code reliable.

[pep8]: https://pycodestyle.readthedocs.io/en/latest/

The Chaos Toolkit projects require all contributors must sign a
[Developer Certificate of Origin][dco] on each commit they would like to merge
into the master branch of the repository. Please, make sure you can abide by
the rules of the DCO before submitting a PR.

[dco]: https://github.com/probot/dco#how-it-works


### Develop

If you wish to develop on this project, make sure to install the development
dependencies. But first, [create a virtual environment][venv] and then install
those dependencies.

[venv]: http://docs.chaostoolkit.org/reference/usage/install/#create-a-virtual-environment


```console
$ pip install -r requirements-dev.txt -r requirements.txt
```

Then, point your environment to this directory:

```console
$ pip install -e .
```

Now, you can edit the files and they will be automatically be seen by your
environment, even when running from the `chaos` command locally.

### Test

To run the tests for the project execute the following:

```
$ pytest
```
