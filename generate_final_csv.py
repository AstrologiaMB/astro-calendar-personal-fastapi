
import csv
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory

# Ensure Ephemeris Path
swe.set_ephe_path('/Users/apple/astro-calendar-personal-fastapi/src/immanuel/resources/ephemeris')

def generate_csv():
    # 1. Setup Natal Data (26/12/1964 21:12 BA)
    # We calculate Natal Positions dynamically to be consistent with the Engine's native logic (NASA Files)
    # verifying consistency.
    
    birth_dt_local = datetime(1964, 12, 26, 21, 12, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    birth_dt_utc = birth_dt_local.astimezone(ZoneInfo("UTC"))
    
    jd_birth = swe.julday(birth_dt_utc.year, birth_dt_utc.month, birth_dt_utc.day, 
                          birth_dt_utc.hour + birth_dt_utc.minute/60.0 + birth_dt_utc.second/3600.0)
    
    planet_map = {
        0: "Sun", 1: "Moon", 2: "Mercury", 3: "Venus", 4: "Mars", 
        5: "Jupiter", 6: "Saturn", 7: "Uranus", 8: "Neptune", 9: "Pluto"
    }
    
    points = {}
    print("Calculando Carta Natal (Geocéntrica / Mean Equinox)...")
    for pid, name in planet_map.items():
        res = swe.calc_ut(jd_birth, pid, swe.FLG_SPEED | swe.FLG_SWIEPH)
        points[name] = {'longitude': res[0][0]}
        print(f"  {name}: {res[0][0]:.4f}")

    natal_data = {
        'points': points,
        'location': {
            'latitude': -34.6037,
            'longitude': -58.3816,
            'timezone': 'America/Argentina/Buenos_Aires'
        }
    }

    # 2. Instantiate Vectorized Calculator
    calc = TransitsCalculatorFactory.create_calculator(natal_data, calculator_type="vectorized")
    
    # 3. Calculate 2025
    start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end_date = datetime(2025, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
    
    print("\nCalculando Tránsitos 2025 (Motor Vectorial)...")
    events = calc.calculate_all(start_date, end_date)
    print(f"Eventos encontrados: {len(events)}")
    
    # 4. Write CSV
    filename = "eventos_2025_vectorized.csv"
    print(f"\nGenerando {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Fecha (UTC)", "Fecha (Local)", "Planeta 1", "Aspecto", "Planeta 2", "Descripción", "Posición 1", "Posición 2"])
        
        for e in events:
            dt_utc = e.fecha_utc
            dt_local = e.fecha_utc.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
            
            # Use metadata for formatted positions if available
            p1_pos = e.metadata.get("posicion1", "")
            p2_pos = e.metadata.get("posicion2", "")
            
            writer.writerow([
                dt_utc.strftime("%Y-%m-%d %H:%M:%S"),
                dt_local.strftime("%Y-%m-%d %H:%M:%S"),
                e.planeta1,
                e.tipo_aspecto,
                e.planeta2,
                e.descripcion,
                p1_pos,
                p2_pos
            ])
            
    print("✅ ¡Listo!")

if __name__ == "__main__":
    generate_csv()
