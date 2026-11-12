#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# SKRIP DEPLOYMENT DEVSECOPS ITCORNER.ID (RPP Rev.3 - 12 VM Architecture)
# Sumber: Management Server Runner (10.10.20.2 - VLAN 20 DevOps/Mgmt)
# Target: Web/App Server DMZ (10.10.10.2 - VLAN 10 DMZ)
# Jalur  : Direct SSH melalui Inter-VLAN Routing OPNsense / Tailscale VPN
# ============================================================================

WEB_SERVER_IP="${WEB_SERVER_IP:-10.10.10.2}"
WEB_SERVER_USER="${WEB_SERVER_USER:-ubuntu}"
CONTAINER_NAME="itcorner_web"
HEALTHCHECK_SCRIPT="$(dirname "$0")/healthcheck.sh"

SSH_OPTS=(-o StrictHostKeyChecking=no -o ConnectTimeout=10)

echo "[DEPLOY] Menyimpan snapshot kontainer aktif untuk persiapan auto-rollback..."
ssh "${SSH_OPTS[@]}" "${WEB_SERVER_USER}@${WEB_SERVER_IP}" "
  if docker ps -a --format '{{.Names}}' | grep -Eq \"^${CONTAINER_NAME}\$\"; then
    docker commit ${CONTAINER_NAME} itcorner-app:rollback || true
  fi
"

echo "[DEPLOY] Mengirim dan menerapkan image Docker terbaru ke Web Server DMZ (${WEB_SERVER_IP})..."
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

echo "[DEPLOY] Kontainer baru berjalan. Menjalankan verifikasi health check..."
if [ -f "${HEALTHCHECK_SCRIPT}" ]; then
  bash "${HEALTHCHECK_SCRIPT}"
else
  echo "[DEPLOY] Deployment selesai tanpa eksekusi healthcheck terpisah."
fi
