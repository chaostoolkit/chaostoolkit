import sys
from collections.abc import Sequence

from chaostoolkit.runtime import runtime_child_invocation


# This is not meant to be called manually
# It will be called automatically when a runtime
# definition is found in the experiment
def main(arguments: Sequence[str] | None = None):
    argv = list(sys.argv[1:] if arguments is None else arguments)
    if not argv or argv.pop(0) != "--":
        print("chaostoolkit.runner is an internal command", file=sys.stderr)
        return 2

    with runtime_child_invocation():
        from chaostoolkit.cli import cli

        return cli.main(args=argv, prog_name="chaos")


if __name__ == "__main__":
    raise SystemExit(main())
