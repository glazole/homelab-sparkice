#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ -f .env ]] || { echo 'Run ./prepare.sh first'; exit 1; }
# ICEBERG_DB_PASSWORD is generated hexadecimal; do not echo it.
pass="$(sed -n 's/^ICEBERG_DB_PASSWORD=//p' .env | head -n1)"
[[ "$pass" =~ ^[a-f0-9]{48}$ ]] || { echo 'Invalid ICEBERG_DB_PASSWORD. Run ./prepare.sh and check .env.'; exit 1; }
docker inspect pg2 >/dev/null 2>&1 || { echo 'pg2 container not found'; exit 1; }
if ! docker exec pg2 pg_isready -U postgres -d iceberg_catalog >/dev/null; then echo 'pg2 not ready'; exit 1; fi
docker exec -i pg2 psql -U postgres -d iceberg_catalog -v ON_ERROR_STOP=1 -v iceberg_pass="$pass" <<'SQL'
SELECT format('CREATE ROLE iceberg_app LOGIN PASSWORD %L', :'iceberg_pass')
  WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'iceberg_app') \gexec
SELECT format('ALTER ROLE iceberg_app PASSWORD %L', :'iceberg_pass') \gexec
GRANT CONNECT ON DATABASE iceberg_catalog TO iceberg_app;
GRANT USAGE, CREATE ON SCHEMA public TO iceberg_app;
SQL
echo 'Role iceberg_app is ready in pg2:iceberg_catalog.'
