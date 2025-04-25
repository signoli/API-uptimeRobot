import requests
import os
import json
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
UPTIMEROBOT_API_KEY = os.getenv("UPTIMEROBOT_API_KEY", "clave_por_defecto")
BASE_URL = "https://api.uptimerobot.com/v2"
OUTPUT_FILE = "data/uptime_status.json"
TZ_ARG = timezone(timedelta(hours=-3))

def save_data(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def fetch_all_monitors():
    monitors = []
    limit = 50
    offset = 0

    while True:
        data = {
            "api_key": UPTIMEROBOT_API_KEY,
            "format": "json",
            "limit": limit,
            "offset": offset
        }
        try:
            response = requests.post(f"{BASE_URL}/getMonitors", data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if "monitors" not in result:
                return []
            monitors.extend(result["monitors"])
            if len(result["monitors"]) < limit:
                break
            offset += limit
        except requests.RequestException as e:
            raise RuntimeError(f"Error en getMonitors: {e}")
    return monitors

def fetch_psps():
    data = {
        "api_key": UPTIMEROBOT_API_KEY,
        "format": "json"
    }
    try:
        response = requests.post(f"{BASE_URL}/getPSPs", data=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("psps", [])
    except requests.RequestException as e:
        raise RuntimeError(f"Error en getPSPs: {e}")

def build_grouped_output(monitors_raw, psps):
    monitor_lookup = {}
    timestamp = datetime.now(TZ_ARG).strftime('%Y-%m-%d %H:%M:%S')

    for m in monitors_raw:
        status = "Up" if m["status"] == 2 else "Down" if m["status"] == 9 else "Unknown"
        monitor_lookup[str(m["id"])] = {
            "status": status,
            "friendly_name": m["friendly_name"],
            "url": m["url"],
            "incidents": [] if status == "Up" else [{"last_down": timestamp, "resolved": None}]
        }

    grouped = {"monitors": []}

    for psp in psps:
        psp_entry = {
            "friendly_name": psp["friendly_name"],
            "monitor_total": len(psp["monitors"]),
            "monitor_down": 0,
            "custom_url": psp.get("custom_url", ""),
            "monitors_id": {}
        }

        for monitor_id in psp["monitors"]:
            monitor_id_str = str(monitor_id)
            if monitor_id_str in monitor_lookup:
                info = monitor_lookup[monitor_id_str]
                psp_entry["monitors_id"][monitor_id_str] = info
                if info["status"] == "Down":
                    psp_entry["monitor_down"] += 1

        grouped["monitors"].append(psp_entry)

    return grouped

def main_loop():
    while True:
        try:
            print("🟢 Ejecutando actualización de estado...")
            monitors = fetch_all_monitors()
            psps = fetch_psps()
            grouped_output = build_grouped_output(monitors, psps)
            save_data(OUTPUT_FILE, grouped_output)
            print(f"✅ Estado guardado en {OUTPUT_FILE} - {datetime.now(TZ_ARG)}")
            time.sleep(60)
        except Exception as e:
            print(f"🔴 Error: {e}")
            print("🔁 Reintentando en 3 segundos...")
            time.sleep(3)

if __name__ == "__main__":
    main_loop()
