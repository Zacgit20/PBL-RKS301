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
EOF

chmod +x itcorner-id/scripts/deploy.sh itcorner-id/scripts/healthcheck.sh

# 3. Tambahkan job build-and-deploy (Self-Hosted Runner) ke .github/workflows/ci-cd.yml
cat << 'EOF' > .github/workflows/ci-cd.yml
name: ITCorner.id DevSecOps Pipeline

on:
  push:
    branches: [ "main", "development" ]
  pull_request:
    branches: [ "main", "development" ]

jobs:
  security-and-testing:
    name: Security Scan (Gitleaks, Bandit, pip-audit) & Pytest
    runs-on: ubuntu-latest

    steps:
      - name: 1. Checkout Repository Code
        uses: actions/checkout@v4

      - name: 2. Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: 3. Install Dependencies & Security Tools
        run: |
          python -m pip install --upgrade pip
          if [ -d "itcorner-id" ]; then cd itcorner-id; fi
          pip install -r requirements.txt

      - name: 4. Secret Scanning (Gitleaks CLI)
        run: |
          wget -q https://github.com/gitleaks/gitleaks/releases/download/v8.18.4/gitleaks_8.18.4_linux_x64.tar.gz
          tar -xzf gitleaks_8.18.4_linux_x64.tar.gz gitleaks
          chmod +x gitleaks
          ./gitleaks detect --source . --no-git -v

      - name: 5. Static Application Security Testing (Bandit SAST)
        run: |
          if [ -d "itcorner-id" ]; then cd itcorner-id; fi
          bandit -r app/ -ll

      - name: 6. Dependency Vulnerability Audit (pip-audit)
        run: |
          if [ -d "itcorner-id" ]; then cd itcorner-id; fi
          pip-audit -r requirements.txt || true

      - name: 7. Run Automated Unit Tests (Pytest)
        run: |
          if [ -d "itcorner-id" ]; then cd itcorner-id; fi
          PYTHONPATH=. pytest tests/unit/ -v

  build-and-deploy:
    name: Trivy Scan, Docker Build, & Deploy to DMZ (10.10.10.2)
    needs: security-and-testing
    if: github.event_name == 'push' && (github.ref == 'refs/heads/development' || github.ref == 'refs/heads/main')
    runs-on: self-hosted

    steps:
      - name: 1. Checkout Repository Code
        uses: actions/checkout@v4

      - name: 2. Build Production Docker Image
        run: |
          if [ -d "itcorner-id" ]; then cd itcorner-id; fi
          docker build -t itcorner-app:latest .

      - name: 3. Container Vulnerability Scan (Trivy)
        run: |
          trivy image --severity HIGH,CRITICAL --exit-code 0 itcorner-app:latest

      - name: 4. Deploy Container to Web Server DMZ (10.10.10.2)
        run: |
          if [ -d "itcorner-id" ]; then cd itcorner-id; fi
          bash scripts/deploy.sh

      - name: 5. Verify Deployment & Auto-Rollback Check
        run: |
          if [ -d "itcorner-id" ]; then cd itcorner-id; fi
          bash scripts/healthcheck.sh