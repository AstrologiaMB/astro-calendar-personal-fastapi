import sys
import os
import json
from fastapi.testclient import TestClient
sys.path.append(os.getcwd())
from app import app

client = TestClient(app)

def generate_baseline():
    print("📸 Generando Snapshot Baseline...")
    
    # Payload complejo para ejercitar toda la lógica (tránsitos, fases, eclipses, etc.)
    # Usamos una fecha futura para asegurar cálculos reales
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
        "year": 2025 # Año solicitado en app.py default
    }

    try:
        response = client.post("/calculate-personal-calendar-dynamic", json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error al generar baseline: {response.text}")
            sys.exit(1)
            
        data = response.json()
        
        # Eliminar campos volátiles (tiempo de cálculo) para comparación determinista
        if "calculation_time" in data:
            del data["calculation_time"]
            
        with open("tests/baseline_response.json", "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            
        print(f"✅ Baseline guardado en tests/baseline_response.json ({len(data['events'])} eventos)")
        
    except Exception as e:
        print(f"❌ Excepción fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_baseline()
