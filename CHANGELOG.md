# Changelog

## [Unreleased][]

[Unreleased]: https://github.com/chaostoolkit/chaostoolkit/compare/0.11.0...HEAD

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