#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
target=../outline_wiki/nginx/conf.d/jupyterhub.conf
[[ -d ../outline_wiki/nginx/conf.d ]] || { echo 'Outline nginx/conf.d missing'; exit 1; }
if [[ -f "$target" ]]; then cp "$target" "${target}.backup.$(date +%Y%m%d%H%M%S)"; fi
cp nginx/jupyterhub.conf "$target"
if ! docker exec homelab-nginx nginx -t; then
 echo 'Nginx failed validation: remove/restore the new jupyterhub.conf and retry' >&2
 exit 1
fi
docker exec homelab-nginx nginx -s reload
echo 'Added https://jupyter.handyman.moscow. Configure DNS / trusted certificate if needed.'
