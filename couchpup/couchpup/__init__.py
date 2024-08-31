"""
Watches CouchDB and makes sure its up-to-date with fly.io
"""

import os

import argparse
import importlib.util
import logging
import random

import anyio

from .core import do_a_sync
from .syncer import Syncer
from .flyio import FlyClient


async def cron(args):
    """
    Runs continuously, periodically checking for updates
    """
    syncer = Syncer(os.environ["COUCHDB_USER"], os.environ["COUCHDB_PASSWORD"])
    flyio = FlyClient()

    async with syncer:
        while True:
            await do_a_sync(syncer, flyio)
            skew_range = args.period * args.skew
            await anyio.sleep(args.period + random.uniform(-skew_range, +skew_range))


def _arg_parser():
    async def usage(args):
        parser.print_usage()

    parser = argparse.ArgumentParser(
        prog="couchpup",
        description=__doc__,
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging."
    )
    parser.set_defaults(func=usage)

    subparsers = parser.add_subparsers(title="Subcommands")

    cronp = subparsers.add_parser("cron", help=cron.__doc__)
    cronp.add_argument(
        "--period",
        type=int,
        default=60,
        metavar="S",
        help="Frequency of updates in seconds (Default: %(default)s)",
    )
    cronp.add_argument(
        "--skew",
        type=float,
        default=0.1,
        metavar="F",
        help="Amount to vary frequency, as a fraction (Default: %(default)s)",
    )
    cronp.set_defaults(func=cron)

    return parser


async def main():
    args = _arg_parser().parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(name)s %(levelname)s %(message)s",
    )

    await args.func(args)


def entrypoint():
    if importlib.util.find_spec("trio") is None:
        anyio.run(main, backend="asyncio")
    else:
        anyio.run(main, backend="trio")
