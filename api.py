# api.py

import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta

DEVICE_IP = "10.10.19.1"
USER      = "admin"
PASSWORD  = "qwerty@12"

# Попробуем HTTP на 8000, а при падении — HTTPS на 443
HTTP_PORT  = 8000
HTTPS_PORT = 443

# Базовые URL
BASE_HTTP_URL  = f"http://{DEVICE_IP}:{HTTP_PORT}/ISAPI"
BASE_HTTPS_URL = f"https://{DEVICE_IP}:{HTTPS_PORT}/ISAPI"

def fetch_access_logs(minutes: int = 5) -> list[dict]:
    now   = datetime.now()
    start = now - timedelta(minutes=minutes)
    ts     = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S")
    url    = (
        f"/AccessControl/Log?format=json"
        f"&startTime={ts(start)}"
        f"&endTime={ts(now)}"
    )
    auth = HTTPDigestAuth(USER, PASSWORD)

    # 1) Сначала пробуем HTTP
    try:
        resp = requests.get(BASE_HTTP_URL + url, auth=auth, timeout=5)
        resp.raise_for_status()
    except Exception as e_http:
        print("HTTP попытка не удалась:", e_http)
        # 2) Падёт на HTTP — пробуем HTTPS (без проверки сертификата)
        try:
            resp = requests.get(
                BASE_HTTPS_URL + url,
                auth=auth,
                timeout=5,
                verify=False
            )
            resp.raise_for_status()
        except Exception as e_https:
            print("HTTPS попытка не удалась:", e_https)
            return []

    data = resp.json().get("data", [])
    return data

if __name__ == "__main__":
    logs = fetch_access_logs(10)
    if not logs:
        print("Нет новых записей или не удалось подключиться.")
    else:
        for ev in logs:
            print(f"{ev['eventTime']} — {ev['personId']} — {ev['entryStatus']}")
