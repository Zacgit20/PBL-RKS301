#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# SKRIP DEPLOYMENT DEVSECOPS ITCORNER.ID
# Sumber: Management Server Runner (10.10.20.2)
# Target: Web/App Server DMZ (10.10.10.2) | Bastion Host DMZ (10.10.10.3)
# ============================================================================

WEB_SERVER_IP="${WEB_SERVER_IP:-10.10.10.2}"
WEB_SERVER_USER="${WEB_SERVER_USER:-ubuntu}"
BASTION_IP="${BASTION_IP:-10.10.10.3}"
BASTION_USER="${BASTION_USER:-ubuntu}"
USE_BASTION_JUMP="${USE_BASTION_JUMP:-false}" # Set 'true' jika SSH diwajibkan lewat Bastion Host
CONTAINER_NAME="itcorner_web"

# Susun opsi SSH 
SSH_OPTS=(-o StrictHostKeyChecking=no)
if [ "${USE_BASTION_JUMP}" = "true" ]; then
  echo "[DEPLOY] Menggunakan Bastion Host (${BASTION_IP}) sebagai SSH Jump Host..."
  SSH_OPTS+=(-J "${BASTION_USER}@${BASTION_IP}")
fi

echo "[DEPLOY] Menyimpan snapshot kontainer aktif untuk persiapan Rollback..."
ssh "${SSH_OPTS[@]}" "${WEB_SERVER_USER}@${WEB_SERVER_IP}" "
  if docker ps -a --format '{{.Names}}' | grep -Eq \"^${CONTAINER_NAME}\$\"; then
    docker commit ${CONTAINER_NAME} itcorner-app:rollback || true
  fi
"

echo "[DEPLOY] Mengirim image Docker terbaru ke Web/App Server DMZ (${WEB_SERVER_IP})..."
docker save itcorner-app:latest | ssh "${SSH_OPTS[@]}" "${WEB_SERVER_USER}@${WEB_SERVER_IP}" "
  docker load &&
  docker stop ${CONTAINER_NAME} || true &&
  docker rm ${CONTAINER_NAME} || true &&
  docker run -d --name ${CONTAINER_NAME} \
    --restart always \
    -p 5000:5000 \
    -e FLASK_ENV=production \
    -e DB_HOST=10.10.30.2 \
    -e DB_PORT=5432 \
    -e DB_NAME=itcorner_db \
    itcorner-app:latest
"
echo "[DEPLOY] Deployment ke Web/App Server (${WEB_SERVER_IP}) selesai."