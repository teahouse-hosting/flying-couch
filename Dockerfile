ARG COUCH_VERSION=3.3.3
FROM docker.io/library/python:3 AS couchpup
RUN --mount=type=tmpfs,target=/var/lib/apt --mount=type=tmpfs,target=/tmp \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        git
RUN pip install bork
WORKDIR /app
COPY couchpup .
RUN bork build

FROM ghcr.io/teahouse-hosting/couchdb-docker:$COUCH_VERSION
RUN --mount=type=tmpfs,target=/var/lib/apt --mount=type=tmpfs,target=/tmp \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip tmux git

COPY --chown=couchdb:couchdb 10-single-node.ini /opt/couchdb/etc/default.d/
COPY --from=couchpup /app/dist/couchpup-*.whl /tmp
RUN pip install --no-cache-dir --break-system-packages /tmp/couchpup-*.whl

RUN --mount=type=tmpfs,target=/tmp \
    curl -L https://github.com/DarthSim/overmind/releases/download/v2.5.1/overmind-v2.5.1-linux-amd64.gz | gunzip > /tmp/overmind && \
    install -m 0755 /tmp/overmind /usr/bin/overmind
COPY Procfile /etc/procfile

ENTRYPOINT []
CMD ["overmind", "start", "-f", "/etc/procfile", "-N", "-c", "pup", "-r", "pup"]
