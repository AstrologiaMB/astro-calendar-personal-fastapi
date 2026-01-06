
import csv
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.poc_vectorized_transits import PocVectorizedTransitsCalculator

# Patch environment for safety (Moshier fallback)
swe.set_ephe_path('')

# Same test data as used in benchmarks
NATAL_DATA = {
    "name": "Test User",
    "points": {
        "Sun": {"longitude": 275.40}, 
        "Moon": {"longitude": 185.20}, 
        "Mercury": {"longitude": 265.1},
        "Venus": {"longitude": 240.5},
        "Mars": {"longitude": 170.2},
        "Jupiter": {"longitude": 10.0}, 
        "Saturn": {"longitude": 330.1},
        "Uranus": {"longitude": 160.5},
        "Neptune": {"longitude": 230.2},
        "Pluto": {"longitude": 155.4}
    }
}

def generate_csv():
    print("Generando eventos para 2025 con POC Vectorizado...")
    calc = PocVectorizedTransitsCalculator(NATAL_DATA)
    start = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end = datetime(2025, 12, 31, tzinfo=ZoneInfo("UTC"))
    
    events = calc.calculate_all(start, end)
    
    filename = "events_2025_poc.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            "Fecha (UTC)", 
            "Planeta Transito", 
            "Aspecto", 
            "Planeta Natal", 
            "Orbe (Grados)", 
            "Pos. Transito", 
            "Pos. Natal"
        ])
        
        for e in events:
            writer.writerow([
                e.fecha_utc.strftime("%Y-%m-%d %H:%M:%S"),
                e.planeta1,
                e.tipo_aspecto,
                e.planeta2,
                f"{e.orbe:.6f}",
                f"{e.longitud1:.6f}",
                f"{e.longitud2:.6f}"
            ])
            
    print(f"✅ Archivo generado exitosamente: {filename}")
    print(f"Total eventos exportados: {len(events)}")

if __name__ == "__main__":
    generate_csv()
