import time
import subprocess

while True:
    try:
        print("Ejecutando uptime_checker.py...")
        subprocess.run(["python3", "uptime_checker.py"], check=True)
        print("Ejecución exitosa. Esperando 60 segundos...")
        time.sleep(60)
    except subprocess.CalledProcessError as e:
        print(f"Error en el script: {e}. Reintentando en 10 segundos...")
        time.sleep(10)
