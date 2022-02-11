<h2 align="center">
  <br>
  <p align="center"><img src="https://avatars.githubusercontent.com/u/32068152?s=200&v=4"></p>
</h2>

<h4 align="center">Chaos Toolkit - Chaos Engineering Automation for Developers</h4>

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
  <a href="https://join.chaostoolkit.org/">Community</a> •
  <a href="https://chaostoolkit.org/reference/usage/install/">Installation</a> •
  <a href="https://chaostoolkit.org/reference/tutorial/">Tutorials</a> •
  <a href="https://chaostoolkit.org/reference/concepts/">Reference</a> •
  <a href="https://github.com/chaostoolkit/chaostoolkit/blob/master/CHANGELOG.md">ChangeLog</a>
</p>

---

# Chaos Toolkit - Chaos Engineering for Developers

The Chaos Toolkit, or as we love to call it &#x201C;ctk&#x201D;, is a simple
CLI-driven tool who helps you write and run Chaos Engineering experiment. It 
supports any target platform you can think of through
[existing extensions](https://chaostoolkit.org/drivers/overview/) or
the ones you write as you need.

Chaos Toolkit is versatile and works really well in settings where other Chaos
Engineering tools may not fit: cloud environments, datacenters, CI/CD, etc.

## Install or Upgrade

Provided you have Python 3.7+ installed, you can install it as follows:

```console
$ pip install -U chaostoolkit
```

## Getting Started

Once you have installed the Chaos Toolkit you can use it through its simple command line tool. 

Running an experiment is as simple as:

```console
$ chaos run experiment.json
```

## Get involved!

Chaos Toolkit's mission is to provide an open API to chaos engineering in all its forms. As such, we encourage and welcome you  to [join][join] our open community Slack team to discuss and share your experiments and needs with the community.
You can also use [StackOverflow][so] to ask any questions regarding using the
Chaos Toolkit or Chaos Engineering.

[join]: https://join.chaostoolkit.org/
[so]: https://stackoverflow.com/questions/ask?tags=chaostoolkit+chaosengineering

If you'd prefer not to use Slack then we welcome the raising of GitHub issues on this repo for any questions, requests, or discussions around the Chaos Toolkit.

Finally you can always email `contact@chaostoolkit.org` with any questions as well.

## Contribute

<a href="https://github.com/tooljet/tooljet/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=chaostoolkit/chaostoolkit" />
</a>

Contributors to this project are welcome as this is an open-source effort that
seeks [discussions][join] and continuous improvement.

[join]: https://join.chaostoolkit.org/

From a code perspective, if you wish to contribute, you will need to run a
Python 3.7+ environment. Please, fork this project, write unit tests to cover
the proposed changes, implement the changes, ensure they meet the formatting
standards set out by `black`, `flake8`, and `isort`, add an entry into
`CHANGELOG.md`, and then raise a PR to the repository for review

The Chaos Toolkit projects require all contributors must sign a
[Developer Certificate of Origin][dco] on each commit they would like to merge
into the master branch of the repository. Please, make sure you can abide by
the rules of the DCO before submitting a PR.

[dco]: https://github.com/probot/dco#how-it-works

