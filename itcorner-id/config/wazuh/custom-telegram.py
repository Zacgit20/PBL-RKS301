#!/usr/bin/env python3
"""
Skrip Integrasi Real-Time Alerting Wazuh SIEM ke Telegram Bot API
Proyek: PBL-RKS301 - ITCorner.id (Well Architected SOC 1)
Lokasi di Server Wazuh (10.10.40.2): /var/ossec/integrations/custom-telegram
"""

import json
import os
import sys
import urllib.request
import urllib.error

def send_telegram_notification(alert_file_path: str, api_key: str, hook_url: str = "") -> None:
    # 1. Baca file JSON alert yang dikirimkan oleh Wazuh Integrator
    with open(alert_file_path, "r", encoding="utf-8") as alert_file:
        alert_json = json.load(alert_file)

    # 2. Ekstrak informasi utama sesuai spesifikasi RPP Final
    rule = alert_json.get("rule", {})
    agent = alert_json.get("agent", {})
    data = alert_json.get("data", {})

    rule_id = rule.get("id", "N/A")
    severity_level = rule.get("level", "N/A")
    description = rule.get("description", "Tidak ada deskripsi")
    agent_name = agent.get("name", "Unknown Host")
    agent_ip = agent.get("ip", "Unknown IP")
    src_ip = data.get("srcip") or alert_json.get("data", {}).get("client_ip", "Tidak diketahui")
    timestamp = alert_json.get("timestamp", "N/A")

    # 3. Ambil Chat ID Grup Telegram SOC
    if "|" in api_key:
        bot_token, chat_id = api_key.split("|", 1)
    else:
        bot_token = api_key
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    telegram_endpoint = hook_url or f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # 4. Susun format pesan notifikasi untuk proses Triase Analis SOC
    message_text = (
        "🚨 *ITCORNER.ID SOC SECURITY ALERT* 🚨\n\n"
        f"• *Rule ID:* `{rule_id}`\n"
        f"• *Tingkat Keparahan (Level):* `{severity_level}`\n"
        f"• *Sumber Kejadian (Agent):* `{agent_name} ({agent_ip})`\n"
        f"• *IP Penyerang / Sumber:* `{src_ip}`\n"
        f"• *Waktu Kejadian:* `{timestamp}`\n"
        f"• *Ringkasan Event:* {description}\n\n"
        "_Segera lakukan triase pada Wazuh Dashboard (10.10.40.2) & eskalasi Case ke TheHive (10.10.40.3)._"
    )

    payload = json.dumps({
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown",
    }).encode("utf-8")

    # 5. Kirim request HTTPS (TCP 443) ke Telegram Bot API
    req = urllib.request.Request(
        telegram_endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()
    except urllib.error.URLError as err:
        sys.stderr.write(f"[ERROR] Gagal mengirim alert ke Telegram: {err}\n")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: custom-telegram <alert_file> <BOT_TOKEN|CHAT_ID> [hook_url]\n")
        sys.exit(1)

    send_telegram_notification(
        alert_file_path=sys.argv[1],
        api_key=sys.argv[2],
        hook_url=sys.argv[3] if len(sys.argv) > 3 else "",
    )
