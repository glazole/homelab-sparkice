#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo 'Iceberg REST from inside docker:'
docker compose exec spark-master curl -fsS 'http://iceberg-rest:8181/v1/config'
echo
echo 'Spark Master services:'
docker compose exec spark-worker bash -lc 'curl -fsS http://spark-master:8080/ >/dev/null && echo Spark-Master-HTTP-OK'
echo 'Notebook identity redirect (HTTP code):'
docker exec homelab-nginx sh -c 'wget -S --spider http://jupyterhub:8000/hub/ 2>&1 | tail -n 8 || true'
