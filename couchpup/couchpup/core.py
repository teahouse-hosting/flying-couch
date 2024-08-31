"""
Actually implements synchronization
"""

import itertools

import anyio

from .syncer import Syncer, SyncTarget
from .flyio import FlyClient


async def do_a_sync(syncer: Syncer, flyio: FlyClient):
    """
    Do one sync pass
    """
    peer_ips = {ip async for ip in flyio.get_peers()}
    # TODO: Include remote databases?
    all_dbs = {f"/{db}" async for db in syncer.iter_local_dbs()} | {"/_users"}

    repls = set(itertools.product(peer_ips, all_dbs))
    live_repls = set()

    with anyio.create_task_group() as tg:
        async for st in syncer.iter_sync_targets():
            if (st.host, st.path) in repls:
                live_repls.add((st.host, st.path))
                tg.start_soon(syncer.add_sync_target, st)
            else:
                tg.start_soon(syncer.del_sync_target, st)

        for host, path in repls - live_repls:
            tg.start_soon(syncer.add_sync_target, SyncTarget(host=host, path=path))
