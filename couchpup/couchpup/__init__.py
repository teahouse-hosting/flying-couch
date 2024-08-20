import argparse
import importlib.util
import logging

import anyio


async def run(args): ...


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

    runp = subparsers.add_parser("run", help=run.__doc__)
    runp.set_defaults(func=run)

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
