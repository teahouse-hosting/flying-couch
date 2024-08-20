ARG COUCH_VERSION=3.3.3
FROM docker.io/library/python:3 AS couchpup
RUN pip install bork
WORKDIR /app
COPY couchpup .
RUN bork build

FROM ghcr.io/teahouse-hosting/couchdb-docker:$COUCH_VERSION
RUN --mount=type=tmpfs,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip

COPY --chown=couchdb:couchdb 10-single-node.ini /opt/couchdb/etc/default.d/
COPY --from=couchpup /app/dist/couchpup-*.whl /tmp
RUN pip install --break-system-packages /tmp/couchpup-*.whl