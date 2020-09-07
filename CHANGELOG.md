# Changelog

## [Unreleased][]

[Unreleased]: https://github.com/chaostoolkit/chaostoolkit/compare/1.7.0...HEAD

## [1.7.0][] - 2020-09-07

[1.7.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.6.0...1.7.0

### Added

* Add the `--hypothesis-strategy` flag to the `run` command. It defines how the
  steady-state hypothesis is applied. One of:
  * `default` is the classic mode where the hypothesis is run before and after
    the method
  * `before-method-only` runs the hypothesis once only before the method
  * `after-method-only` runs the hypothesis once only after the method. This is
    useful when you know your environment is not in the appropriate state
    before the conditions are applied
  * `during-method-only` runs the hypothesis repeatedly during the method but
    not before nor after
  * `continously` runs the hypothesis repeatedly during the method as well as
    before and after as usual
* Add the `--hypothesis-frequency` flag to the `run` command. This flag is
  only meaningful with `--hypothesis-strategy=during-method-only|continously`.
  It takes a floating number indicating how many seconds to wait between two
  executions of the hypothesis
* Add the `--fail-fast` flag to the `run` command. This flag is
  only meaningful with `--hypothesis-strategy=during-method-only|continously`.
  If set, this indicates the experiment should be marked as deviating
  immediatly. When not provided, the hypothesis runs until the end of the
  method without terminating the experiment

### Changed

- Bump dependency on chaostoolkit-lib to 1.13.0 to support the steady state
  strategy

## [1.6.0][] - 2020-08-17

[1.6.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.5.0...1.6.0

## Added

- The `--var` and `--var-file` flags to override values in the configuration,
  and secrets for var files, blocks of the experiments. They take precedence
  for inlined values and allow to have data files managed externally to the
  experiment itself when environment variables are not an option for example.
  [#175][175]

[175]: https://github.com/chaostoolkit/chaostoolkit-lib/issues/175

## [1.5.0][] - 2020-07-06

[1.5.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.4.2...1.5.0

### Added

- Commands to get/set/remove an entry from the settings as well as show
  the settings file entirely [#65][65]
- Rollbacs runtime strategy flag [#176][176]
  
  Backwars compatible default strategy to run the rollbacks. This will run
  unless of a failed probe in the hypothesis or when a control interrupted
  the experiment (not passing the flag is equivalent to this):
  ```
  $ chaos run --rollback-strategy=default experiment.json
  ```

  Always run the rollbacks:
  ```
  $ chaos run --rollback-strategy=always experiment.json
  ```

  Never run the rollbacks:
  ```
  $ chaos run --rollback-strategy=never experiment.json
  ```

  Run the rollbacks only when deviated:
  ```
  $ chaos run --rollback-strategy=deviated experiment.json
  ```

[65]: https://github.com/chaostoolkit/chaostoolkit-lib/issues/65
[176]: https://github.com/chaostoolkit/chaostoolkit-lib/issues/176

## [1.4.2][] - 2020-04-29

[1.4.2]: https://github.com/chaostoolkit/chaostoolkit/compare/1.4.1...1.4.2

### Added
* New flag `--no-verify-tls` to `chaos run` and `chaos validate`commands;
  it disables TLS certificate verification when source is downloaded
  over a self-signed certificate endpoint.

### Changed

* Migrates CI/CD from TravisCI to Github Actions
* [Potentially breaking] Build the Docker image with a non-root user by default (rootless container).
  This is a potentially breaking change if you created your own docker image
  using the chaostoolkit/chaostoolkit as a base image.
* Allow validating experiments downloaded from URL: `chaos validate http://...`


## [1.4.1][] - 2020-02-20

[1.4.1]: https://github.com/chaostoolkit/chaostoolkit/compare/1.4.0...1.4.1

### Added

* Added build for Python 3.8

### Changed

* Fixed `importlib_metadata` different naming between Python 3.8 and
  earlier [#162][162]

[162]: https://github.com/chaostoolkit/chaostoolkit-lib/issues/162


## [1.4.0][] - 2020-02-20

[1.4.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.3.0...1.4.0

### Added

- Add critical level color to the logger
- Add chaos init exports experiment also in yaml format

  ```
  chaos init --experiment-path prod-experiment.yaml
  ```

### Changed

* Fixed Dockerfile so the right dependencies are installed at build time
* Replaced pkg_resource usage with python 3.8 backport importlib_metadata
* Bump chaostoolkit-lib dependency to 1.8.0

## [1.3.0][] - 2019-09-03

[1.3.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.2.0...1.3.0

### Added

- Load global controls before we even read the experiments so we can apply
  them before and after loading the experiment.

## [1.2.0][] - 2018-04-17

[1.2.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.1.0...1.2.0

### Added

- Support for structured logging [#122][122]

[122]: https://github.com/chaostoolkit/chaostoolkit/issues/122

### Changed

- Moved loading global controls back into `run_experiment` itself
  [chaostoolkit-lib#116][116]

[116]: https://github.com/chaostoolkit/chaostoolkit-lib/issues/116

## [1.1.0][] - 2018-04-17

[1.1.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.0.0...1.1.0

## Added

- Bump to Chaos Toolkit library 1.2.0
- Allow to declare and load controls from settings so they are globally
  applied to all your runs [chaostoolkit-lib#99][99]

  In your settings file, at `~/.chaostooltkit-lib/settings.yaml` add, for
  instance:

  ```yaml
  controls:
  my-own-control:
    provider:
      module: mypackage.mycontrole_module
      type: python
  ```

  This will load `mypackage/mycontrole_module.py` from your `PYTHONPATH`
  and use it as a [control][].
- Remove MacOSX build. Way too long for any benefits.
- Build against stable Python 3.7
- Ensure exit code is set in all cases

[control]: https://docs.chaostoolkit.org/reference/extending/create-control-extension/
[99]: https://github.com/chaostoolkit/chaostoolkit-lib/issues/99

## [1.0.0][] - 2018-02-21

[1.0.0]: https://github.com/chaostoolkit/chaostoolkit/compare/1.0.0rc4...1.0.0

## Changed

- Cleaned up package metadata

## [1.0.0rc4][] - 2018-02-21

[1.0.0rc4]: https://github.com/chaostoolkit/chaostoolkit/compare/1.0.0rc3...1.0.0rc4

## Added

- Ensure requirements-dev.txt is bundled with the package
- Bumped chaostoolkit-lib to 1.0.0
- Ensure we don't create installation problem by forcing a specific version

## [1.0.0rc3][] - 2018-01-29

[1.0.0rc3]: https://github.com/chaostoolkit/chaostoolkit/compare/1.0.0rc2...1.0.0rc3

## Changed

- Bump to chaostoolkit-lib 1.0.0rc3

## [1.0.0rc2][] - 2018-01-28

[1.0.0rc2]: https://github.com/chaostoolkit/chaostoolkit/compare/1.0.0rc1...1.0.0rc2

## Changed

- Bump to chaostoolkit-lib 1.0.0rc2
- Enable MacOSX travis build to ensure Chaos Toolkit does build there

## [1.0.0rc1][] - 2018-11-30

[1.0.0rc1]: https://github.com/chaostoolkit/chaostoolkit/compare/0.17.1...1.0.0rc1

## Changed

- Handle RC versioning when building release
- Pin dependency versions

## [0.17.1][] - 2018-11-30

[0.17.1]: https://github.com/chaostoolkit/chaostoolkit/compare/0.17.0...0.17.1

### Changed

* Remove `NoReturn` import as it is not available prior Python 3.6.5 [#90][90]

[90]: https://github.com/chaostoolkit/chaostoolkit/issues/90

## [0.17.0][] - 2018-11-29

[0.17.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.16.0...0.17.0

### Added

- add `info` command to display basic information such as version of the
  toolkit core library or installed extensions. Display also the current
  settings [#64][64]

[64]: https://github.com/chaostoolkit/chaostoolkit/issues/64

### Changed

- strip command name before sending it to check newer version as sometimes
  we get a tabulation character in there
- swap `logger.warn` for `logger.warning` as the former is obsolete

## [0.16.0][] - 2018-09-19

[0.16.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.15.0...0.16.0

### Added

- send a `RunFlowEvent.RunDeviated` event in addition to other events when the
  steady state deviated after the experimental method [#56][56]

[56]: https://github.com/chaostoolkit/chaostoolkit/issues/56

## [0.15.0][] - 2018-08-09

[0.15.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.14.0...0.15.0

## Added

- a new global flag `chaos --settings <path>` to explicitely specify the
  location of the Chaos Toolkit settings file
- experiments can now also be loaded from a HTTP(s) resource (with or without
  auth) as per [#53][53]

[53]: https://github.com/chaostoolkit/chaostoolkit/issues/53

## Changed

- by default, the run command will now set the exit code to 1 when the
  experiment is not successful (interrupted, aborted or failed). This can be
  bypassed by plugins so they have the opportunity to process the journal as
  well. In that case, they must set the exit code themselves to play nicely.

## [0.14.0][] - 2018-04-27

[0.14.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.13.0...0.14.0

### Changed

- Do not notify of experiment validation when running it (too noisy)
- Encode date, datetime, decimal and UUID to JSON explicitely

## [0.13.0][] - 2018-02-20

[0.13.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.12.0...0.13.0

### Changed

- Publish events for each step of the flow

## [0.12.0][] - 2018-02-09

[0.12.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.11.0...0.12.0

### Changed

- New `chaos init` wizard instructions

## [0.11.0][] - 2018-02-08

[0.11.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.10.0...0.11.0

### Changed

- Returning journal and experiment from run and validate commands for
  downstream applications
- Better guidance on init

## [0.10.0][] - 2018-02-06

[0.10.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.9.0...0.10.0

### Changed

- Create an empty experiment when no discovery was run beforehand [#27][27]
- Returns the generated experiment to external callers
- Name of the journal output from the run command is now `journal.json` rather
  than `chaos-report.json` [#31][31]
- Renamed the debug log from `experiment.log` to `chaostoolkit.log` because
  it is used for any commands, even when the experiment is not required
- The debug log is now appending
- The command being run is logged into the debug log
- You can bypass argument in the init command via empty string [#29][29]
- Allow to create steady-state hypothesis from init command [#28][28]
- Allow to set rollbacks from init command [#30][30]
- Pass command executed to checker for compatbility [#36][36]
- Better logging of failed discovery [chaostoolkit-lib#29][29lib]
- Depending now on chaostoolkit-lib 0.14.0

[27]: https://github.com/chaostoolkit/chaostoolkit/issues/27
[28]: https://github.com/chaostoolkit/chaostoolkit/issues/28
[29]: https://github.com/chaostoolkit/chaostoolkit/issues/29
[30]: https://github.com/chaostoolkit/chaostoolkit/issues/30
[31]: https://github.com/chaostoolkit/chaostoolkit/issues/31
[36]: https://github.com/chaostoolkit/chaostoolkit/issues/36
[29lib]: https://github.com/chaostoolkit/chaostoolkit-lib/issues/29

## [0.9.0][] - 2018-01-17

[0.9.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.8.0...0.9.0

### Added

- Steady state hypothesis is not mandatory when exploring weaknesses [#18][18]

[18]: https://github.com/chaostoolkit/chaostoolkit/issues/18

## [0.8.0][] - 2018-01-16

[0.8.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.7.0...0.8.0

### Added

- New init feature [#23][23]

[23]: https://github.com/chaostoolkit/chaostoolkit/issues/23

## [0.7.0][] - 2018-01-16

[0.7.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.6.0...0.7.0

### Added

- New discovery feature

## [0.6.0][] - 2017-12-19

[0.6.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.5.0...0.6.0

### Changed

- Version check is now done server-side to remove semver dependency

## [0.5.0][] - 2017-12-17

[0.5.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.4.0...0.5.0

### Changed

- Log to file by default and added a flag to disable it
- Updated to chaostoolkit-lib 0.8.0

## [0.4.0][] - 2017-12-12

[0.4.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.3.0...0.4.0

### Added

- Added log-file flag to log the run (at DEBUG level) to a file

### Changed

- Bumped to chaostoolkit-lib 0.7.0

## [0.3.0][] - 2017-12-06

[0.3.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.2.8...0.3.0

### Changed

- Proper contact email address
- Ensuring latest spec version support from chaostoolkit-lib 0.6.0

## [0.2.8][] - 2017-11-30

[0.2.8]: https://github.com/chaostoolkit/chaostoolkit/compare/0.2.5...0.2.8

### Changed

-   Minor improvements of the version check
-   Triggering the documentation build on new releases so the doc is updated
    with the latest tag information


## [0.2.5][] - 2017-11-23

[0.2.5]: https://github.com/chaostoolkit/chaostoolkit/compare/0.2.4...0.2.5

### Added

-   Checking for newer release of the toolkit at runtime

## [0.2.4][] - 2017-10-12

[0.2.4]: https://github.com/chaostoolkit/chaostoolkit/compare/0.2.3...0.2.4

### Added

-   Enable CLI extensions
-   Provide a change directory argument when using the CLI

### Changed

-   Proper verbose log level

## [0.2.3][] - 2017-10-07

[0.2.3]: https://github.com/chaostoolkit/chaostoolkit/compare/0.2.2...0.2.3

### Changed

-   Not a universal wheel distribution

## [0.2.2][] - 2017-10-06

[0.2.2]: https://github.com/chaostoolkit/chaostoolkit/compare/0.2.1...0.2.2

### Changed

-   Removed old dependencies

## [0.2.1][] - 2017-10-06

[0.2.1]: https://github.com/chaostoolkit/chaostoolkit/compare/0.2.0...0.2.1

### Changed

-   Package up extra files when installed from source

## [0.2.0][] - 2017-10-06

[0.2.0]: https://github.com/chaostoolkit/chaostoolkit/compare/0.1.12...0.2.0

### Changed

-   Core code now lives in a dedicated project [chaoslib][chaoslib].
    chaostoolkit is now just the CLI of running experiments [#3][3]

[chaoslib]: https://github.com/chaostoolkit/chaostoolkit-lib
[3]: https://github.com/chaostoolkit/chaostoolkit/issues/3

## [0.1.12][] - 2017-10-03

[0.1.12]: https://github.com/chaostoolkit/chaostoolkit/compare/0.1.11...0.1.12

### Removed

-   Documentation has moved to its own project

## [0.1.11][] - 2017-10-02

[0.1.11]: https://github.com/chaostoolkit/chaostoolkit/compare/0.1.10...0.1.11

### Added

-   Ensure CNAME is set for the docs to be resolved via chaostoolkit.org

## [0.1.10][] - 2017-10-02

[0.1.9]: https://github.com/chaostoolkit/chaostoolkit/compare/0.1.9...0.1.10

### Added

-   Installing dependencies along with the command
-   Using a regular user to run from a Docker container

## [0.1.9][] - 2017-10-01

[0.1.9]: https://github.com/chaostoolkit/chaostoolkit/compare/0.1.8...0.1.9

### Changed

-   Switched to an alpine based Docker image for smaller footprint

## [0.1.8][] - 2017-10-01

[0.1.8]: https://github.com/chaostoolkit/chaostoolkit/compare/0.1.7...0.1.8

### Changed

-   Better installation docs

## [0.1.0][] - 2017-10-01

[0.1.0]: https://github.com/chaostoolkit/chaostoolkit/tree/0.1.0

### Added

-   Initial release