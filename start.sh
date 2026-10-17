#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ -s certs/ca-bundle.pem ]] || { echo 'Missing certs/ca-bundle.pem; run ./prepare.sh'; exit 1; }
[[ -f .env ]] || { echo 'Missing .env; run ./prepare.sh'; exit 1; }
for key in KEYCLOAK_ISSUER KEYCLOAK_CLIENT_SECRET JUPYTERHUB_ALLOWED_USERS RUSTFS_ACCESS_KEY_ID RUSTFS_SECRET_ACCESS_KEY; do
 value="$(sed -n "s/^${key}=//p" .env | head -n1)"
 if [[ -z "$value" || "$value" == *REPLACE* ]]; then echo "Fill ${key} in .env first"; exit 1; fi
done
for network in outline-network homelab-db; do
  docker network inspect "$network" >/dev/null || { echo "Missing Docker network: $network"; exit 1; }
done
./init-db.sh
docker compose config --quiet
printf '
Build Spark image...
'
docker compose build spark-master
printf '
Build single-user Jupyter image...
'
docker compose --profile images build jupyter-image
printf '
Build JupyterHub with DockerSpawner + OAuth...
'
docker compose build jupyterhub
printf '
Starting services...
'
docker compose up -d spark-master spark-worker iceberg-rest jupyterhub
docker compose ps
printf '
NEXT: create/check RustFS bucket; ./install-nginx.sh; ./status.sh
'
