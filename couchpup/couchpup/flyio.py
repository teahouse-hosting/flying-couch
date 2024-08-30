"""
Utilities to access FlyIO stuff
"""
# https://fly.io/docs/networking/private-networking/
# https://fly.io/docs/machines/runtime-environment/

import os
from socket import AddressFamily, SocketKind
import typing

import anyio


# We're doing this whole protocol/live/test dance in order to support test mocking


class FlyClient(typing.Protocol):
    async def get_peers(self) -> typing.AsyncIterable[str]: ...


class LiveFlyClient:
    async def get_peers(self) -> typing.AsyncIterable[str]:
        """
        Uses fly envvars and fly internal DNS to find app peers.
        """
        # Could return ipaddress objects, but the other end is just going to stuff
        # them into URLs
        app = os.environ["FLY_APP_NAME"]
        my_ips = set()
        if os.environ.get("FLY_PUBLIC_IP", None):
            my_ips.add(os.environ["FLY_PUBLIC_IP"])
        if os.environ.get("FLY_PRIVATE_IP", None):
            my_ips.add(os.environ["FLY_PRIVATE_IP"])

        for gai in await anyio.getaddrinfo(f"{app}.internal", None):
            match gai:
                case (AddressFamily.AF_INET, SocketKind.SOCK_STREAM, _, _, (addr, _)):
                    if addr not in my_ips:
                        yield addr
                case (
                    AddressFamily.AF_INET6,
                    SocketKind.SOCK_STREAM,
                    _,
                    _,
                    (addr, _, _, scope),
                ):
                    # IPv6 flow is without purpose and cannot be represented in addresses
                    if addr not in my_ips:
                        if scope:
                            yield f"{addr}%{scope}"
                        else:
                            yield addr


class TestFlyClient:
    peers: list[str]

    async def get_peers(self) -> typing.AsyncIterable[str]:
        for p in self.peers:
            yield p
