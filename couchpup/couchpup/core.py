"""
Actually implements synchronization
"""

import itertools

import anyio
import structlog

from .syncer import Syncer, SyncTarget
from .flyio import FlyClient


async def do_a_sync(syncer: Syncer, flyio: FlyClient):
    """
    Do one sync pass
    """
    LOG = structlog.get_logger()
    # HTTPX handles bracketing IPv6
    peer_ips = {ip async for ip in flyio.get_peers()}
    # TODO: Include remote databases?
    all_dbs = {f"/{db}" async for db in syncer.iter_local_dbs()} | {"/_users"}
    LOG.info("Starting sync", dbs=all_dbs, peers=peer_ips)

    repls = set(itertools.product(peer_ips, all_dbs))
    live_repls = set()

    async with anyio.create_task_group() as tg:
        async for st in syncer.iter_sync_targets():
            if (st.host, st.path) in repls:
                LOG.debug("Updating", host=st.host, path=st.path)
                live_repls.add((st.host, st.path))
                tg.start_soon(syncer.add_sync_target, st)
            else:
                LOG.debug("Deleting", host=st.host, path=st.path)
                tg.start_soon(syncer.del_sync_target, st)

        for host, path in repls - live_repls:
            LOG.debug("Adding", host=host, path=path)
            tg.start_soon(syncer.add_sync_target, SyncTarget(host=host, path=path))
