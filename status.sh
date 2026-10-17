#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose ps
echo '--- Spark Master ---'
docker compose logs --tail=15 spark-master
echo '--- Spark Worker ---'
docker compose logs --tail=15 spark-worker
echo '--- Iceberg REST ---'
docker compose logs --tail=15 iceberg-rest
echo '--- JupyterHub ---'
docker compose logs --tail=15 jupyterhub
