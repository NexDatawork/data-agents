"""CLI entrypoint for OpenGraph AI.

TODO: Wire command handlers and argument dispatch.
"""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser.

    TODO: Register subcommands from cli.commands.
    """
    parser = argparse.ArgumentParser(prog="opengraph")
    parser.add_argument("--version", action="store_true", help="Show version")
    return parser


def main() -> int:
    """Execute CLI main flow.

    TODO: Route parsed args to concrete command modules.
    """
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print("opengraph scaffold 0.1.0")
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
