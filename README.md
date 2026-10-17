# Homelab Sparkice · HP server · handyman.moscow

Single-node **Spark Standalone 3.5.5 + JupyterHub 5.3 + Iceberg REST 1.6.0**.
Uses **existing** Keycloak (OIDC), RustFS (S3), PostgreSQL `pg2` (`iceberg_catalog`), and `homelab-nginx`. No duplicate instances.

## Networks and service dependencies

* `outline-network`: Nginx ↔ JupyterHub, Spark Master ↔ Worker ↔ single-user Jupyter, all ↔ RustFS (`rustfs:9000`), Iceberg (`iceberg-rest:8181`).
* `homelab-db`: **only Iceberg REST** ↔ `pg2:5432`.
* **No host ports** for Spark RPC, web UIs, or catalog. Exposing JupyterHub is done through existing Nginx.
* Existing Outline, Keycloak, RustFS, pg1, pg2, pg3 and Airflow are **not modified by `docker compose up`**.

## Resources (HP: 15 GiB RAM / 12 logical CPUs)

Spark Worker: **3 cores / 4 GiB advertised**, container cap **5 GiB**; single-user notebook: **3 GiB cap**, `spark.cores.max=2`, `executor.memory=2g`, `executor.cores=2`. This is a starter budget; don't run several simultaneous sessions until tuning. Spark and PySpark v3.5.5, Iceberg runtime v1.6.1.

### Prerequisites

```bash
cd ~/projects/homelab
# Extract archive so that ~/projects/homelab/sparkice exists
cd sparkice
./prepare.sh
```

* `outline-network` and `homelab-db` must already exist. `pg2` must be healthy.
* Outline RustFS service must be available at `http://rustfs:9000` **inside** `outline-network`.
* Existing Nginx must be `homelab-nginx`, with wildcard/SAN certificate covering `jupyter.handyman.moscow`.
* Domain `jupyter.handyman.moscow` needs to point/reach the existing Nginx (same pattern as `airflow.handyman.moscow`).
* S3 API bucket **`home-iceberg`** must be created in existing RustFS Console (`https://rustfs.handyman.moscow`). Use dedicated least-privilege S3 keys for just that bucket (and optionally `smoke/`). RustFS does not automatically create buckets for Iceberg.
* No production/company credentials or datasets in this homelab.

### Step 1 · `.env` and certificate

`./prepare.sh` copies `.env.example` to `.env`, generates a 48-character hexadecimal DB password, and assembles `certs/ca-bundle.pem` using the host CA and existing `../outline_wiki/nginx/certs/rootCA.pem` (if present). Existing `.env` is never overwritten.

```bash
nano .env
```

Set **real** existing Keycloak realm in `KEYCLOAK_ISSUER`, new OIDC client secret, real Keycloak `preferred_username` (allowed user) and dedicated RustFS key/secret. `REPLACE_*` placeholders will make `start.sh` stop. **Do not commit `.env` / CA bundles / credentials.**

Keycloak: create a **new Confidential OIDC client** `jupyterhub` in same existing realm as Outline. `Client authentication ON`, `Standard flow ON`, `Valid redirect URIs = https://jupyter.handyman.moscow/hub/oauth_callback`, `Web origins = https://jupyter.handyman.moscow`. Obtain Client Secret from credentials. No new Keycloak service/realm/database required. Existing Outline remains unchanged.

`JUPYTERHUB_ALLOWED_USERS` must contain `preferred_username`, comma-separated if multiple; only those users are authorized. Don't use `allow_all=True` on a public site.

### Step 2 · PostgreSQL pg2

```bash
./init-db.sh
```

Creates/updates **only** the `iceberg_app` role and grants `CONNECT`, `USAGE`, `CREATE` on the `public` schema of database `iceberg_catalog`; does not change `pg1`, `pg3`, Keycloak, Outline, or Airflow. The existing `pg2` remains separate.

### Step 3 · Build and start

```bash
./start.sh
```

`start.sh` builds Spark base, notebook runtime (also used by the Worker), JupyterHub (can take several minutes / download many jars), then starts Spark Master, Spark Worker, Iceberg REST and JupyterHub. An experimental warning or large image download is not by itself a fatal error. `start.sh` rebuilds images on rerun, but does **not** delete storage.

```bash
./status.sh
./check.sh
```

For diagnostics:

```bash
docker compose logs -f --tail=100 jupyterhub
docker compose logs -f --tail=100 iceberg-rest
docker compose logs -f --tail=100 spark-worker
```

### Step 4 · Existing Nginx

```bash
./install-nginx.sh
```

Adds only `../outline_wiki/nginx/conf.d/jupyterhub.conf`, tests Nginx config and reloads `homelab-nginx`. Existing `homelab.conf` unchanged. If there is already a custom `jupyter.handyman.moscow` server block in Outline Nginx, **do not install a duplicate**.

Open **https://jupyter.handyman.moscow**. New browser session should redirect to the **same** Keycloak realm used for Outline / Airflow. After login JupyterHub starts a user container (`sparkice-jupyter-<username>`). The notebook image is built before startup and must already be present locally.

### Step 5 · Create the smoke notebook

Start a terminal in JupyterLab and upload `notebooks/01_smoke_test.ipynb` (file included in this repo), or copy the cells. It checks RustFS bucket visibility, submits a Spark job to Spark Master, writes to `ice.homelab.smoke` in Iceberg via REST/JDBC and reads Parquet via S3A. It **inserts a row each time**. If no bucket exists, it tells you to create it.

Expected outcomes:

* API `GET http://iceberg-rest:8181/v1/config` returns HTTP 200;
* Spark Worker registered in Master;
* `spark.range(100).count()` returns 100;
* Iceberg namespace/table created and read back;
* Parquet count returns 10.

### Issues to note

* The working multi-node Sparkice deployment was configured for `192.168.150.*` and used host-network workers and fixed Driver ports. This homelab is **single-host** and uses Docker DNS instead, with zero published Spark RPC ports.
* This design deliberately reuses `outline-network` to make the RustFS endpoint accessible to Spark executors. That network is not a strict security boundary; shared secrets and Docker socket require trust.
* DockerSpawner mounts `/var/run/docker.sock`; **this is effectively host-level privilege**, not suitable for untrusted users. The deployment must be access-controlled and preferably reached over VPN / protected entrypoint.
* JupyterHub state is stored in named volume `homelab-sparkice_jupyterhub-data`; notebooks in Docker volumes `sparkice-notebooks-<username>`; back them up separately. `docker compose down -v` **removes volumes** — avoid it.
* The `tabulario/iceberg-rest:1.6.0` image is a test/reference implementation and must not be treated as production service.
* JupyterHub and Spark image compatibility, JDBC, and OIDC must be verified on actual HP server; files were statically reviewed but not run against the host here.

### Stop (preserves data)

```bash
./stop.sh
```

### Git hygiene

```bash
git init -b main
git add .gitignore .dockerignore .env.example docker-compose.yml README.md \
    prepare.sh init-db.sh start.sh stop.sh status.sh check.sh install-nginx.sh \
    nginx docker conf jupyterhub spark-ui-startup.py notebooks
git status --short
git diff --cached --check
```

Check no `REPLACE` actual secret has been accidentally copied into tracked config. Never commit `.env`, `certs/`, volumes, logs, or enterprise data.
