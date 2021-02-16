# Chaos Toolkit Roadmap

The Chaos Toolkit aims at being a unifying automation protocol for Chaos
Engineering experiments.

This document covers core projects only:

* the [Chaos Toolkit CLI][cli]
* the [Chaos Toolkit core library][core]
* the [Chaos Toolkit bundler][bundler]
* the [Chaos Toolkit documentation][doc]
* the Chaos Toolkit governance efforts

[cli]: https://github.com/chaostoolkit/chaostoolkit
[core]: https://github.com/chaostoolkit/chaostoolkit-lib
[bundler]: https://github.com/chaostoolkit/chaostoolkit-bundler
[doc]: https://github.com/chaostoolkit/chaostoolkit-documentation

For any extensions, please see each related project for their own roadmap.

## Why a roadmap?

An open-source project starts small but, as it grows, becomes more difficult
for its community to follow, or help with. In the case of the Chaos Toolkit,
over the years, new issues were raised that had great potential. They were
referenced in a meta-issue, the infamous
[Paving the way for greater and more powerful automation][#74]. This issue
became a bit of a mess and wasn't really helpful to understand what was
worked on ot not. Eventually, [@ojongerius][ojongerius] [suggested][165] we
should setup a more formal roadmap so that community could start helping as
well.

A roadmap is here to make visible the path to the future of the project. It
supports better governance and a more active contribution dynamic.

[ojongerius]: https://github.com/ojongerius
[#74]: https://github.com/chaostoolkit/chaostoolkit/issues/74
[165]: https://github.com/chaostoolkit/chaostoolkit/issues/165


## Governance

The Chaos Toolkit is an open project with a semi [BDFL][bdfl] approach. The idea
is not for the project maintainers to veto randomly but to provide support and
guidance by keeping the project consistent with its original [values] and
goals, while moving forward.

[values]: https://docs.chaostoolkit.org/reference/developing/values/

As for June 2020, there is no heavy process around this governance. This is to
say that the project evolves based on its community requirements while gradually
building a proper definition of its own future.

## How to help?

Glad you ask! The Chaos Toolkit is an open source project which strives to
be welcoming and supportive of [contributions][contribute]. we love a civil and
joyful community that [respects its members][coc]. To help the project you
have a variety of entry points, depending on your experience and time. In
regards to the core, we'll do our best to keep this roadmap up to date so that
yo ucan quickly see if anything picks up your interest. In that case, mostly
start by creating and issue and come to the [community chat][slack] to
announce it. Usually we expect PRs with fully squashed and [signed][dco]
commits.

[contribute]: https://docs.chaostoolkit.org/reference/contributing/
[coc]: https://github.com/chaostoolkit/chaostoolkit/blob/master/CODE_OF_CONDUCT.md
[slack]: https://join.chaostoolkit.org/
[dco]: https://docs.chaostoolkit.org/reference/contributing/#licensing-and-certification-of-origin
[bdfl]: https://en.wikipedia.org/wiki/Benevolent_dictator_for_life

## How do we organize roadmap work?

Not everything is part of the roadmap because not everything in life can be
planned ahead. Therefore, expect issues and features to be worked on at any
time.

With that said, there cannot be visibility without some sort of planning either.
To be a little more dynamic and visible, this project relies on GitHub
project boards. For now these are the existing projects:

* https://github.com/orgs/chaostoolkit/projects/5: This is an org-level covering
  all the core repositories listed above.

As the Chaos Toolkit grows, new boards will likely come to life but until
then it feels more connected to have a single one.

Any issue of these repositories could be part of the roadmap, just ensure they
are associated with that project to become "actionable".

A roadmap item is not a particular issue. It's merely one that moves
the project forward as it matures. Bugs can become roadmap items if they
demonstrate a current limitation that could be unlocked with an improvement of
the core projects. So can feature requests.

It may take some time before anything enters the roadmap:

* go through a first review to determine what the issue/question is about
* see how it fits into the project's goals. Sometimes a feature request makes
  sense on its own but gos beyond the scope of CTK
* consider its efforts at first glance

Once entered the roadmap, timing can be discussed to see when any work is
done on it.

This may look like a convoluted and fairly loose way to organise the project
but the idea is to offer a visibility on how things can move forward.

As ever, don't hesitate to come to the [chat][slack] to discuss this with
the maintainers and community. The whole "process" will evolved and improve.

### Milestones or no milestones?

In an ideal world, there would be milestones. We think we will get there
someday with a more regular release scheduling, like every 6 month or
something in that vein.

For now, the project is not structured well enough to make any sort 
of promises as to when new releases happens. 

However, milestones could be used to advertize of future releases scope so
they prove useful. The only downside of GitHub milestones is that they only
exist on a per-repository basis, which lead to more project maintanance.

Nevertheless we will be using milestones to scope a future release but without
a release date in mind for now.


## Roadmap

In this section, we will link to future milestones so that can be easily
discovered.

### v1.x

#### Novelties

* [x] command line flags to pass variables as a file or directly via the
  cli [#175][175]
* [x] enable steady-state execution strategies
* [x] add a command to the cli to set properties in the settings file [#65][65]
* [ ] enable extending secrets backend [#114][114]
* [ ] improve `discover` and `init` commands to make them more useful/usable
* [ ] improve json format logging [#173][173]
* [ ] improve documentation
* [x] create an official repository/package of common tolerances
* [x] create an official repository/package for common controls
* [x] add a flag to control the rollbacks strategy [#176][176]
* [ ] support finer control over rollbacks and when they should be
      executed [#177][177]

[65]: https://github.com/chaostoolkit/chaostoolkit/issues/65
[114]: https://github.com/chaostoolkit/chaostoolkit/issues/114
[173]: https://github.com/chaostoolkit/chaostoolkit/issues/173
[175]: https://github.com/chaostoolkit/chaostoolkit/issues/175
[176]: https://github.com/chaostoolkit/chaostoolkit/issues/176
[177]: https://github.com/chaostoolkit/chaostoolkit/issues/177

#### Deprecation

* [x] the notification API in favour to more specific internal events
* [ ] archive chaosplatform projects and move them to the [attic][]

[attic]: https://github.com/chaostoolkit-attic


### v2.x

To be defined :)

