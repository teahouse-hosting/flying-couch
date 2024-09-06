"""
Responsible for taking fly data and actually configuring CouchDB.
"""

import dataclasses
import re
import typing

import chaise.dictful
import chaise.helpers
import httpx
import structlog

from . import couch


DOC_FORMAT = "pup_{ip}_{db}"
DOC_PARSE = re.compile(r"^pup_(?P<ip>.*?)_(?P<db>.*)$")


@dataclasses.dataclass
class SyncTarget:
    host: str
    path: str
    _doc: chaise.dictful.Document | None = None


class Syncer:
    """
    Abstracts the replicator database,
    """

    url: str
    session: chaise.dictful.BasicSession

    def __init__(self, username, password):
        self.url = str(
            httpx.URL("http://localhost:5984/", username=username, password=password)
        )

    async def __aenter__(self):
        self.session = await couch.ConstantPool(self.url).session()
        try:
            await self.session.create_db("_replicator")
        except chaise.Conflict:
            pass
        return self

    async def __aexit__(self, *exc):
        del self.session

    async def iter_local_dbs(self) -> typing.AsyncIterable[str]:
        """
        Get the databases instantiated locally.

        Does not include any special databases (_users, _replicator, etc).
        """
        async for db in self.session.iter_dbs():
            if not db.startswith("_"):
                yield db

    async def iter_sync_targets(self) -> typing.AsyncIterable[SyncTarget]:
        """
        List of every host/db we're pulling from
        """
        repl = self.session["_replicator"]  # No need to check, definitely exists
        async for docref in repl.iter_all_docs(include_docs=True):
            doc = await docref.doc()
            target = httpx.URL(doc["source"])
            yield SyncTarget(host=target.host, path=target.path, _doc=doc)

    async def del_sync_target(self, target: SyncTarget):
        """
        Remove a replication
        """
        repl = self.session["_replicator"]  # No need to check, definitely exists
        try:
            await repl.attempt_delete(target._doc)
        except (chaise.Missing, chaise.Deleted):
            # Already deleted
            pass

    async def add_sync_target(self, target: SyncTarget):
        """
        Add a replication, or update an existing one
        """
        LOG = structlog.get_logger()

        repl = self.session["_replicator"]  # No need to check, definitely exists
        docid = DOC_FORMAT.format(ip=target.host, db=target.path.strip("/"))
        from_url = str(
            httpx.URL(self.url, host=target.host, path=target.path)
        )  # Copy auth, port, protocol
        to_url = str(httpx.URL(self.url, path=target.path))

        # TODO: Short circuit if target._doc is set

        LOG.debug("Adding replication", src=from_url, dst=to_url)

        try:
            await repl.attempt_put(
                chaise.dictful.Document(
                    source=from_url, target=to_url, create_target=False, continuous=True
                ),
                docid,
            )
        except chaise.Conflict:
            # Already exists, update the existing document
            # This can be important if auth changes
            async for doc in repl.mutate(docid):
                doc["source"] = from_url
                doc["target"] = to_url
