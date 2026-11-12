#!/usr/bin/env bash
set -euo pipefail

WEB_SERVER_IP="${WEB_SERVER_IP:-10.10.10.2}"
WEB_SERVER_USER="${WEB_SERVER_USER:-ubuntu}"
HEALTH_URL="https://${WEB_SERVER_IP}/health"
CONTAINER_NAME="itcorner_web"

echo "[HEALTHCHECK] Memeriksa respon HTTP 200 OK dari ${HEALTH_URL}..."
sleep 5

HTTP_STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" || echo "000")

if [ "${HTTP_STATUS}" -eq 200 ]; then
  echo "[HEALTHCHECK] SUKSES! Layanan merespons HTTP ${HTTP_STATUS} OK."
  exit 0
else
  echo "[HEALTHCHECK] GAGAL! Layanan merespons HTTP ${HTTP_STATUS}. Memulai ROLLBACK otomatis..."
  ssh -o StrictHostKeyChecking=no "${WEB_SERVER_USER}@${WEB_SERVER_IP}" "
    docker stop ${CONTAINER_NAME} || true &&
    docker rm ${CONTAINER_NAME} || true &&
    docker run -d --name ${CONTAINER_NAME} --restart always -p 5000:5000 itcorner-app:rollback
  "
  echo "[ROLLBACK] Kontainer telah dikembalikan ke versi stabil sebelumnya."
  exit 1
fi