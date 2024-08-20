#!/usr/bin/env python3
"""
Management command for flying couch instances.
"""
# Just wraps flyctl

import argparse
import json
import logging
import subprocess


def flyctl(*cmd):
    """
    Call flyctl in JSON mode
    """
    # --json isn't a global flag, so we have to add it after the subcommand. We
    # do this by looking for the first - arg and adding it before then. That's
    # not as soon as it will be, but Jamie thinks it'll never split a flag and
    # an argument, and it'll always be before a --.
    for i, bit in enumerate(cmd):
        if bit.startswith("-"):
            cmd = [*cmd[:i], "--json", *cmd[i:]]
            break
    else:
        cmd = [*cmd, "--json"]
    proc = subprocess.run(
        ["flyctl", "--json", "", *cmd],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    # FIXME: Redirect stderr into logging
    # FIXME: Allow stdin
    return json.loads(proc.stdout)


def add_more(args):
    """
    Add another server in a region
    """


def remove_one(args):
    """
    Remove a server in a region
    """


def _arg_parser():
    def usage(args):
        parser.print_usage()

    parser = argparse.ArgumentParser(
        prog="couchctl",
        description=__doc__,
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging."
    )
    parser.add_argument(
        "app",
        metavar="APP",
        help="Fly app to work against",
    )
    parser.set_defaults(func=usage)

    subparsers = parser.add_subparsers(title="Subcommands")

    morep = subparsers.add_parser("more", help=add_more.__doc__)
    morep.set_defaults(func=add_more)
    morep.add_argument("region", help="Fly region to add to")

    lessp = subparsers.add_parser("less", help=remove_one.__doc__)
    lessp.set_defaults(func=remove_one)
    lessp.add_argument("region", help="Fly region to add to")

    return parser


def main():
    args = _arg_parser().parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(name)s %(levelname)s %(message)s",
    )

    args.func(args)


if __name__ == "__main__":
    main()
