
import csv
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.poc_vectorized_transits import PocVectorizedTransitsCalculator

# Patch environment for safety (Moshier fallback)
swe.set_ephe_path('')

# REAL NATAL DATA CALCULATED FOR 26/12/1964 21:12 BUENOS AIRES
NATAL_DATA_REAL = {
    "name": "Maria Blaquier (Real)",
    "points": {
        "Sun": {"longitude": 275.279053},
        "Moon": {"longitude": 199.532341},
        "Mercury": {"longitude": 258.929193},
        "Venus": {"longitude": 249.611417},
        "Mars": {"longitude": 172.330921},
        "Jupiter": {"longitude": 46.462691},
        "Saturn": {"longitude": 330.848502},
        "Uranus": {"longitude": 164.826466},
        "Neptune": {"longitude": 229.183063},
        "Pluto": {"longitude": 166.312380},
    }
}

def generate_csv():
    print("Generando CSV REAL 2025...")
    calc = PocVectorizedTransitsCalculator(NATAL_DATA_REAL)
    
    # Year 2025
    start = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end = datetime(2025, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
    
    events = calc.calculate_all(start, end)
    
    filename = "eventos_2025_real.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            "Fecha (UTC)", 
            "Planeta Transito", 
            "Aspecto", 
            "Planeta Natal", 
            "Orbe", 
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
            
    print(f"✅ Archivo generado: {filename}")
    print(f"Total eventos: {len(events)}")

if __name__ == "__main__":
    generate_csv()
