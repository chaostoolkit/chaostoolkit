<h2 align="center">
  <br>
  <p align="center"><img src="https://avatars.githubusercontent.com/u/32068152?s=200&v=4"></p>
</h2>

<h4 align="center">Chaos Toolkit - Chaos Engineering for All Engineers</h4>

<p align="center">
   <a href="https://github.com/chaostoolkit/chaostoolkit/releases">
   <img alt="Release" src="https://img.shields.io/github/v/release/chaostoolkit/chaostoolkit">
   <a href="#">
   <img alt="Build" src="https://github.com/chaostoolkit/chaostoolkit/actions/workflows/build.yaml/badge.svg">
   <a href="https://github.com/reliablyhq/cli/issues">
   <img alt="GitHub issues" src="https://img.shields.io/github/issues/chaostoolkit/chaostoolkit?style=flat-square&logo=github&logoColor=white">
   <a href="https://github.com/reliablyhq/cli/blob/master/LICENSE.md">
   <img alt="License" src="https://img.shields.io/github/license/chaostoolkit/chaostoolkit">
   <a href="#">
   <img alt="Python version" src="https://img.shields.io/pypi/pyversions/chaostoolkit.svg">
   <a href="https://pkg.go.dev/github.com/chaostoolkit/chaostoolkit">
</p>

<p align="center">
  <a href="https://join.slack.com/t/chaostoolkit/shared_invite/zt-22c5isqi9-3YjYzucVTNFFVIG~Kzns8g">Community</a> •
  <a href="https://chaostoolkit.org/reference/usage/install/">Installation</a> •
  <a href="https://chaostoolkit.org/reference/tutorial/">Tutorials</a> •
  <a href="https://chaostoolkit.org/reference/concepts/">Reference</a> •
  <a href="https://github.com/chaostoolkit/chaostoolkit/blob/master/CHANGELOG.md">ChangeLog</a>
</p>

---

# Chaos Toolkit - Chaos Engineering for All Engineers

The Chaos Toolkit, or as we love to call it &#x201C;ctk&#x201D;, is a simple
CLI-driven tool who helps you write and run Chaos Engineering experiment. It 
supports any target platform you can think of through
[existing extensions](https://chaostoolkit.org/drivers/overview/) or
the ones you write as you need.

Chaos Toolkit is versatile and works really well in settings where other Chaos
Engineering tools may not fit: cloud environments, datacenters, CI/CD, etc.

## Install or Upgrade

Provided you have Python 3.12+ installed, the recommended installation uses
[`uv`](https://docs.astral.sh/uv/):

```console
$ uv tool install chaostoolkit
```

You can also install it with `pip`, as before:

```console
pip install -U chaostoolkit
```

## Getting Started

Once you have installed the Chaos Toolkit you can use it through its simple command line tool. 

Running an experiment is as simple as:

```console
chaos run experiment.json
```

### Experiment dependencies

An experiment can declare the Python packages it needs. For example:

```yaml
runtime:
  python:
    version: "3.14"
    dependencies:
      - chaostoolkit-kubernetes>=0.38
```

When `chaos run` or `chaos validate` sees this declaration, it asks `uv` to
prepare the dependencies and runs the command in that Python environment. The
current Chaos Toolkit installation and its environment are not modified.
Setting `isolated` to `true` creates an isolated run environment; it defaults
to `false`. Setting `version` selects the Python version used by `uv` and
automatically enables isolation.

This feature requires the `uv` executable to be available on `PATH`. Without a
`runtime.python.dependencies` declaration, Chaos Toolkit behaves exactly as it
did before and expects extensions to already be installed.

For remote sources, controls needed to fetch or load the experiment must
already be installed with Chaos Toolkit. A remote experiment may be fetched
once to discover its dependencies and again inside the prepared runtime;
remote experiment documents should therefore be immutable or versioned.

## Get involved!

Chaos Toolkit's mission is to provide an open API to chaos engineering in all its forms. As such, we encourage and welcome you  to [join][join] our open community Slack team to discuss and share your experiments and needs with the community.
You can also use [StackOverflow][so] to ask any questions regarding using the
Chaos Toolkit or Chaos Engineering.

[join]: https://join.slack.com/t/chaostoolkit/shared_invite/zt-22c5isqi9-3YjYzucVTNFFVIG~Kzns8g
[so]: https://stackoverflow.com/questions/ask?tags=chaostoolkit+chaosengineering

If you'd prefer not to use Slack then we welcome the raising of GitHub issues on this repo for any questions, requests, or discussions around the Chaos Toolkit.

Finally you can always email `contact@chaostoolkit.org` with any questions as well.

## Contribute

<a href="https://github.com/tooljet/tooljet/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=chaostoolkit/chaostoolkit" />
</a>

Contributors to this project are welcome as this is an open-source effort that
seeks [discussions][join] and continuous improvement.

From a code perspective, if you wish to contribute, you will need to run a
Python 3.12+ environment. Please, fork this project, write unit tests to cover
the proposed changes, implement the changes, ensure they meet the formatting
standards set out by `ruff`, add an entry into
`CHANGELOG.md`, and then raise a PR to the repository for review

The project is driven by [PDM][pdm], so install it and you can run the
following commands:

[pdm]: https://pdm-project.org/latest/

```console
pdm install
pdm run test
pdm run format
pdm run lint
```

The Chaos Toolkit projects require all contributors must sign a
[Developer Certificate of Origin][dco] on each commit they would like to merge
into the master branch of the repository. Please, make sure you can abide by
the rules of the DCO before submitting a PR.

[dco]: https://github.com/probot/dco#how-it-works
