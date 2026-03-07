#!/usr/bin/env bash
set -e

nohup jupyter server --no-browser --ip=0.0.0.0 --port=8888 \
  --IdentityProvider.token="${JUPYTER_TOKEN:-local-dev}" \
  --ServerApp.allow_origin="http://localhost:3000" \
  --allow-root \
  > /proc/1/fd/1 2>&1 &

myst clean --all --yes
HOST=0.0.0.0 myst start --keep-host --port 3000 --server-port 3100
