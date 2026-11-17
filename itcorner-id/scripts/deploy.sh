#!/usr/bin/env bash
set -euo pipefail

WEB_SERVER_IP="${WEB_SERVER_IP:-10.10.10.2}"
WEB_SERVER_USER="${WEB_SERVER_USER:-rks301}"
CONTAINER_NAME="itcorner_web"

SSH_CMD=(ssh -o StrictHostKeyChecking=no "${WEB_SERVER_USER}@${WEB_SERVER_IP}")

echo "[DEPLOY] Menyimpan snapshot image kontainer aktif untuk persiapan Auto-Rollback..."
"${SSH_CMD[@]}" "
  if docker ps -a --format '{{.Names}}' | grep -Eq \"^${CONTAINER_NAME}\$\"; then
    docker commit ${CONTAINER_NAME} itcorner-app:rollback || true
  fi
"

echo "[DEPLOY] Mengirim dan menjalankan image terbaru di Web Server DMZ (${WEB_SERVER_IP})..."
docker save itcorner-app:latest | "${SSH_CMD[@]}" "
  docker load &&
  docker stop ${CONTAINER_NAME} || true &&
  docker rm ${CONTAINER_NAME} || true &&
  docker run -d --name ${CONTAINER_NAME} \
    --restart always \
    -p 127.0.0.1:5000:5000 \
    -e FLASK_ENV=production \
    -e DB_HOST=10.10.30.2 \
    -e DB_PORT=5432 \
    -e DB_NAME=itcorner_db \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgrespassword \
    itcorner-app:latest
"

echo "[DEPLOY] Status kontainer pada Web Server DMZ:"
"${SSH_CMD[@]}" "docker ps --filter name=${CONTAINER_NAME}"