from flask import Flask, jsonify
import os
import json

app = Flask(__name__)

OUTPUT_FILE = "monitors_down.json"

@app.route("/alerts", methods=["GET"])
def get_alerts():
    """
    Devuelve los monitores caídos desde el archivo JSON.
    """
    if not os.path.exists(OUTPUT_FILE):
        return jsonify({"error": "No se ha generado el archivo de monitores aún"}), 404

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Error al leer el archivo: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
