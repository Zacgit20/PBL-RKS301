#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# SKRIP PENGUJIAN DETEKSI WAF MODSECURITY (SQLi & XSS) - ITCORNER.ID
# ============================================================================

TARGET_URL="${1:-https://10.10.10.2}"

echo "=== [1/3] Menguji Akses Normal ke Katalog Produk ==="
NORMAL_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "${TARGET_URL}/products")
echo "Status Akses Normal: HTTP ${NORMAL_CODE} (Ekspektasi: 200)"

echo "=== [2/3] Menguji Serangan SQL Injection pada Filter Produk ==="
SQLI_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "${TARGET_URL}/products?q=1'%20OR%20'1'='1")
echo "Status Serangan SQLi: HTTP ${SQLI_CODE} (Ekspektasi: 403 Forbidden dari WAF)"

echo "=== [3/3] Menguji Serangan Cross-Site Scripting (XSS) ==="
XSS_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "${TARGET_URL}/products?q=<script>alert(1)</script>")
echo "Status Serangan XSS : HTTP ${XSS_CODE} (Ekspektasi: 403 Forbidden dari WAF)"