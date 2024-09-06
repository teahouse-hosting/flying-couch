set windows-powershell := true

# Show this help
@help:
  just --list

# Set up dev environments
install:
  pre-commit install

# Run the pre-commit hooks
hooks:
  pre-commit run --all-files

# Run flying-couch locally
run:
  docker build --load -t fc .
  docker run --rm -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=admin fc

# Connect to one of the overmind processes
connect PROC:
  fly ssh console --pty -C 'overmind connect {{PROC}}'

# Suspend all machines
pause:
  fly machine suspend $(fly machine list -q)

# Unsuspend all machines
resume:
  fly machine start $(fly machine list -q)

# Launch a dev copy
launch:
  fly launch --copy-config --flycast --no-public-ips
  fly secrets set COUCHDB_USER=admin COUCHDB_PASSWORD=admin
