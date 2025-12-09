import sys
import os
import json
import difflib
from fastapi.testclient import TestClient
sys.path.append(os.getcwd())
from app import app

client = TestClient(app)

def verify_refactor():
    print("🧪 Verificando Refactor (Snapshot Test)...")
    
    # 1. Cargar Baseline
    try:
        with open("tests/baseline_response.json", "r") as f:
            baseline_data = json.load(f)
    except FileNotFoundError:
        print("❌ Baseline no encontrado. Ejecuta generate_baseline.py primero.")
        sys.exit(1)

    # 2. Generar nueva respuesta con el mismo Payload
    payload = {
        "name": "Test User",
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "location": {
            "latitude": -34.6037, # Buenos Aires
            "longitude": -58.3816,
            "name": "Buenos Aires",
            "timezone": "America/Argentina/Buenos_Aires"
        },
        "year": 2025
    }

    try:
        response = client.post("/calculate-personal-calendar-dynamic", json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error en la nueva API: {response.text}")
            sys.exit(1)
            
        new_data = response.json()
        
        # Eliminar campos volátiles (tiempo de cálculo)
        if "calculation_time" in new_data:
            del new_data["calculation_time"]
            
        # 3. Comparación Profunda
        # Convertir a JSON string formateado para comparar líneas
        baseline_str = json.dumps(baseline_data, indent=2, sort_keys=True)
        new_str = json.dumps(new_data, indent=2, sort_keys=True)
        
        if baseline_data == new_data:
            print("✅ ÉXITO: El refactor produce EXACTAMENTE el mismo resultado.")
            sys.exit(0)
        else:
            print("❌ FALLO: Hay diferencias en el resultado.")
            # Generar diff
            diff = difflib.unified_diff(
                baseline_str.splitlines(),
                new_str.splitlines(),
                fromfile='Baseline',
                tofile='New Refactor',
                lineterm=''
            )
            print("\n".join(diff))
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Excepción durante la verificación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_refactor()
