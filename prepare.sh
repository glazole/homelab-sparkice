#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo 'Docker required'; exit 1; }
command -v openssl >/dev/null || { echo 'openssl required'; exit 1; }
if [[ ! -e .env ]]; then
  cp .env.example .env
  chmod 600 .env
  p="$(openssl rand -hex 24)"
  sed -i "s/^ICEBERG_DB_PASSWORD=.*/ICEBERG_DB_PASSWORD=${p}/" .env
  echo 'Created .env: fill Keycloak realm/client secret, preferred_username, RustFS bucket credentials.'
else
  echo 'Existing .env left unchanged.'
fi
mkdir -p certs
chmod 700 certs
base="$(realpath ../outline_wiki/nginx/certs/rootCA.pem 2>/dev/null || true)"
if [[ -n "$base" && -f "$base" ]]; then
  cat /etc/ssl/certs/ca-certificates.crt "$base" > certs/ca-bundle.pem
  chmod 600 certs/ca-bundle.pem
  echo 'CA bundle prepared (system CA + existing Outline rootCA.pem).'
else
  echo 'WARNING: rootCA.pem not found. Copy trusted root CA into certs/ca-bundle.pem before start.'
fi
printf '
Existing shared networks:
'
for name in outline-network homelab-db; do
  docker network inspect "$name" >/dev/null 2>&1 && echo "  OK $name" || echo "  MISSING $name"
done
printf '
Next: nano .env; ./init-db.sh; create RustFS bucket; ./start.sh
'
