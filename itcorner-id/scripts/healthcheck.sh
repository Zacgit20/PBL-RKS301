#!/usr/bin/env bash
set -euo pipefail

WEB_SERVER_IP="${WEB_SERVER_IP:-10.10.10.2}"
WEB_SERVER_USER="${WEB_SERVER_USER:-rks301}"
HEALTH_URL="https://${WEB_SERVER_IP}/health"
CONTAINER_NAME="itcorner_web"

echo "[HEALTHCHECK] Memeriksa endpoint ${HEALTH_URL}..."
for i in {1..5}; do
  STATUS_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" || echo "000")
  if [ "${STATUS_CODE}" == "200" ]; then
    echo "[HEALTHCHECK] Sukses! Aplikasi merespons HTTP 200 OK."
    exit 0
  fi
  echo "[HEALTHCHECK] Percobaan ${i}/5 gagal (HTTP ${STATUS_CODE}), menunggu 3 detik..."
  sleep 3
done

echo "[ROLLBACK] Healthcheck gagal! Mengembalikan kontainer ke image stabil (itcorner-app:rollback)..."
ssh -o StrictHostKeyChecking=no "${WEB_SERVER_USER}@${WEB_SERVER_IP}" "
  if docker images -q itcorner-app:rollback | grep -q .; then
    docker stop ${CONTAINER_NAME} || true
    docker rm ${CONTAINER_NAME} || true
    docker run -d --name ${CONTAINER_NAME} \
      --restart always \
      -p 127.0.0.1:5000:5000 \
      -e FLASK_ENV=production \
      -e DB_HOST=10.10.30.2 \
      -e DB_PORT=5432 \
      -e DB_NAME=itcorner_db \
      -e DB_USER=postgres \
      -e DB_PASSWORD=postgrespassword \
      itcorner-app:rollback
    echo '[ROLLBACK] Pemulihan otomatis ke versi stabil berhasil.'
  else
    echo '[ROLLBACK] Tidak ada image rollback sebelumnya.'
  fi
"
exit 1
