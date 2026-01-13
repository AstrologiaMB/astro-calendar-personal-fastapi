
import csv
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory

# Ensure Ephemeris Path
swe.set_ephe_path('/Users/apple/astro-calendar-personal-fastapi/src/immanuel/resources/ephemeris')

RAG_CSV_PATH = '/Users/apple/astro_interpretador_rag_fastapi/eventos_con_interpretacion.csv'
OUTPUT_CSV = 'reporte_faltantes_rag.csv'

def load_known_Interpretations():
    known = set()
    try:
        with open(RAG_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            # Find 'descripcion' column index
            try:
                desc_idx = headers.index('descripcion')
            except ValueError:
                print("Error: Columna 'descripcion' no encontrada en CSV RAG.")
                return known

            for row in reader:
                if len(row) > desc_idx:
                    desc = row[desc_idx].strip()
                    if desc:
                        known.add(desc)
    except Exception as e:
        print(f"Error leyendo CSV RAG: {e}")
    
    print(f"Interpretaciones Conocidas Cargadas: {len(known)}")
    return known

def generate_report():
    # 1. Load Known
    known_titles = load_known_Interpretations()
    
    # 2. Calculate 2025 Events (Same Logic as generate_final_csv.py)
    planet_map = {
        0: "Sun", 1: "Moon", 2: "Mercury", 3: "Venus", 4: "Mars", 
        5: "Jupiter", 6: "Saturn", 7: "Uranus", 8: "Neptune", 9: "Pluto"
    }
    
    # Natal Data (AstroSeek / User confirmed)
    birth_dt_local = datetime(1964, 12, 26, 21, 12, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    birth_dt_utc = birth_dt_local.astimezone(ZoneInfo("UTC"))
    jd_birth = swe.julday(birth_dt_utc.year, birth_dt_utc.month, birth_dt_utc.day, 
                          birth_dt_utc.hour + birth_dt_utc.minute/60.0 + birth_dt_utc.second/3600.0)
    
    points = {}
    for pid, name in planet_map.items():
        res = swe.calc_ut(jd_birth, pid, swe.FLG_SPEED | swe.FLG_SWIEPH)
        points[name] = {'longitude': res[0][0]}

    natal_data = {
        'points': points,
        'location': {
            'latitude': -34.6037,
            'longitude': -58.3816,
            'timezone': 'America/Argentina/Buenos_Aires'
        }
    }

    print("Calculando Tránsitos 2025...")
    calc = TransitsCalculatorFactory.create_calculator(natal_data, calculator_type="vectorized")
    start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end_date = datetime(2025, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
    events = calc.calculate_all(start_date, end_date)
    print(f"Total Eventos 2025: {len(events)}")
    
    # 3. Find Missing
    missing_events = []
    seen_missing = set() # To avoid duplicates in report
    
    for e in events:
        desc = e.descripcion.strip()
        if desc not in known_titles:
            if desc not in seen_missing:
                missing_events.append(e)
                seen_missing.add(desc)
    
    print(f"Eventos Faltantes (Sin Interpretación): {len(missing_events)}")
    
    # 4. Write CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Titulo_Requerido", "Fecha_Ejemplo", "Planeta1", "Aspecto", "Planeta2"])
        
        for e in missing_events:
            writer.writerow([
                e.descripcion,
                e.fecha_utc.strftime("%Y-%m-%d"),
                e.planeta1,
                e.tipo_aspecto,
                e.planeta2
            ])
            
    print(f"✅ Reporte generado: {OUTPUT_CSV}")

if __name__ == "__main__":
    generate_report()
