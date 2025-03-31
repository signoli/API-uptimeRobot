import requests
import os
import json
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración
UPTIMEROBOT_API_KEY = os.getenv("UPTIMEROBOT_API_KEY", "clave_por_defecto")
BASE_URL = "https://api.uptimerobot.com/v2"
OUTPUT_FILE = "monitors_down.json"
TZ_ARG = timezone(timedelta(hours=-3))  # Zona horaria Argentina (UTC-3)

# Cargar datos previos si existen
def load_previous_data():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"monitors_down": {}}
    return {"monitors_down": {}}

def save_data(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def fetch_all_monitors():
    """
    Obtiene todos los monitores de UptimeRobot utilizando paginación.
    """
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
            print(f"Error en la solicitud a UptimeRobot: {e}")
            return []
    return monitors

def update_monitor_status():
    """
    Obtiene los monitores y actualiza su estado en un archivo JSON.
    """
    try:
        previous_data = load_previous_data()
        monitors = fetch_all_monitors()
        current_status = {}
        
        for monitor in monitors:
            monitor_id = str(monitor["id"])
            friendly_name = monitor["friendly_name"]
            url = monitor["url"]
            status = monitor["status"]
            timestamp = datetime.now(TZ_ARG).strftime('%Y-%m-%d %H:%M:%S')
            
            # Si el monitor no existía en el historial, inicializarlo
            if monitor_id not in previous_data["monitors_down"]:
                previous_data["monitors_down"][monitor_id] = {
                    "friendly_name": friendly_name,
                    "url": url,
                    "status": "Up",
                    "incidents": []
                }
            
            # Si el monitor pasó a Down
            if status == 9 and previous_data["monitors_down"][monitor_id]["status"] != "Down":
                previous_data["monitors_down"][monitor_id]["status"] = "Down"
                previous_data["monitors_down"][monitor_id]["incidents"].append({
                    "last_down": timestamp,
                    "resolved": None
                })
                # Mantener solo las últimas 20 incidencias
                previous_data["monitors_down"][monitor_id]["incidents"] = previous_data["monitors_down"][monitor_id]["incidents"][-60:]
            
            # Si el monitor pasó a Up
            elif status == 2 and previous_data["monitors_down"][monitor_id]["status"] == "Down":
                # Buscar la última incidencia sin resolver y actualizarla
                for incident in reversed(previous_data["monitors_down"][monitor_id]["incidents"]):
                    if incident["resolved"] is None:
                        incident["resolved"] = timestamp
                        break
                previous_data["monitors_down"][monitor_id]["status"] = "Up"

            current_status[monitor_id] = previous_data["monitors_down"][monitor_id]
        
        # Guardar actualización
        save_data({"monitors_down": current_status})
        print(f"Datos actualizados en {OUTPUT_FILE}")
    
    except Exception as e:
        print(f"Error al actualizar monitores: {e}")

if __name__ == "__main__":
    update_monitor_status()