"""
Watches CouchDB and makes sure its up-to-date with fly.io
"""

import os

import argparse
import importlib.util
import logging
import random
import sys

import anyio
import httpx
import structlog

from .core import do_a_sync
from .syncer import Syncer
from .flyio import LiveFlyClient


async def cron(args):
    """
    Runs continuously, periodically checking for updates
    """
    LOG = structlog.get_logger()
    syncer = Syncer(os.environ["COUCHDB_USER"], os.environ["COUCHDB_PASSWORD"])
    flyio = LiveFlyClient()

    while True:
        try:
            async with syncer:
                pass
        except httpx.ConnectError:
            pass
        except Exception:
            LOG.exception("Error waiting for couch")
        else:
            break
        await anyio.sleep(1)

    while True:
        try:
            async with syncer:
                await do_a_sync(syncer, flyio)
        except Exception:
            LOG.exception("Error running a sync")
        skew_range = args.period * args.skew
        wait_time = args.period + random.uniform(-skew_range, +skew_range)
        LOG.debug("Sleeping", seconds=wait_time)
        await anyio.sleep(wait_time)


def _arg_parser():
    async def usage(args):
        parser.print_usage()

    parser = argparse.ArgumentParser(
        prog="couchpup",
        description=__doc__,
    )
    # parser.add_argument(
    #     "--verbose", action="store_true", help="Enable verbose logging."
    # )
    # parser.set_defaults(func=usage)

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

    # TODO: Re-implement --verbose
    # structlog.stdlib.recreate_defaults(log_level=0 if args.verbose else logging.INFO)
    logging.basicConfig(
        level=logging.INFO,  # HTTPX is pretty verbose, this still shows every request made
        format="%(name)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )

    await args.func(args)


def entrypoint():
    if importlib.util.find_spec("trio") is None:
        anyio.run(main, backend="asyncio")
    else:
        anyio.run(main, backend="trio")
