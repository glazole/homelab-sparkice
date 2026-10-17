#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose stop jupyterhub spark-worker spark-master iceberg-rest
# Volumes (JupyterHub state and user notebooks) are not removed.
