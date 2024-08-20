# flying-couch
Magical CouchDB on fly.io

The app itself will look for app peers and automatically set up a replication
network.

The use of private networking is strongly encouraged, and fly has
[several features](https://fly.io/docs/networking/private-networking/) to help
with accessibility. In particular, the use of
[flycast](https://fly.io/docs/networking/flycast/) is probably best for you.


## couchctl

Additionally, a script called `couchctl` is provided to manage your flying couch
instances. In particular, it provides commands to scale up and scale down as
efficiently as possible. (eg, making use of volume forking to reduce warm up
time.)

`couchctl` is a wrapper around `flyctl`, so you need to have `flyctl` installed
and authenticated.
