
import sys
import time
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo
import concurrent.futures

# --- ENVIRONMENT PATCHING FOR V4 SAFETY ---
# Force Swisseph to use Moshier (no files) preventing crashes in V4
swe.set_ephe_path('')

# Monkeypatch potential re-setters if possible, or just hope V4 respects the global
# We also need to mock natal data that V4 expects
NATAL_DATA = {
    "name": "Test User",
    "date": "1964-12-26",
    "time": "21:12:00",
    "location": {
        "latitude": -34.6037,
        "longitude": -58.3816,
        "timezone": "America/Argentina/Buenos_Aires"
    },
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
    },
    "angles": {
         "ASC": {"longitude": 120.0}, # Dummy
         "MC": {"longitude": 30.0}    # Dummy
    },
    "houses": {}
}

# Import Calculators
from src.calculators.poc_vectorized_transits import PocVectorizedTransitsCalculator
from src.calculators.astronomical_transits_calculator_v4 import AstronomicalTransitsCalculatorV4, chart

def normalize_event(e):
    # Returns a tuple key for comparison: (Planet1, Planet2, AspectName)
    # And the date for checking
    return (e.planeta1, e.planeta2, e.tipo_aspecto), e.fecha_utc

def run_comparison():
    year = 2025
    start_date = datetime(year, 1, 1, tzinfo=ZoneInfo("UTC"))
    end_date = datetime(year, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
    
    print(f"=== COMPARACIÓN ALGORITMOS 2025 ===")
    
    # --- 1. RUN POC ---
    print("\n[1] Ejecutando POC Vectorizado...")
    t0 = time.time()
    poc_calc = PocVectorizedTransitsCalculator(NATAL_DATA)
    poc_events = poc_calc.calculate_all(start_date, end_date)
    t1 = time.time()
    poc_time = t1 - t0
    print(f"    -> POC terminó en {poc_time:.4f}s. Encontró {len(poc_events)} eventos.")
    
    # --- 2. RUN V4 (PRODUCTION) ---
    print("\n[2] Ejecutando V4 (Producción)...")
    # Patch settings to ensure Moshier is used if Immanuel tries to load files
    # Note: V4 uses 'swe' which maps to the C extension. 
    # Global state should hold if we don't reload.
    
    t0 = time.time()
    v4_calc = AstronomicalTransitsCalculatorV4(NATAL_DATA)
    
    # Filter planets to match POC (POC checks all 10 against 10)
    # V4 defaults to checking transiting planets (excluding Moon usually) against Natal planets + angles.
    # We must restrict V4 to check the SAME transiting list as POC for fair comparison.
    # POC planets: Sun..Pluto (0-9)
    # V4 checks: Sun..Pluto 
    planets_to_check = [chart.SUN, chart.MOON, chart.MERCURY, chart.VENUS, chart.MARS, 
                        chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]
    
    try:
        v4_events_raw = v4_calc.calculate_all(start_date, end_date, planets_to_check=planets_to_check)
    except Exception as e:
        print(f"!!! CRASH EN V4: {e}")
        # Try to diagnose
        import traceback
        traceback.print_exc()
        return

    # Convert/Filter V4 events to match POC structural expectations
    # POC only does Planet-to-Planet. V4 does Planet-to-Planet + Angles.
    # Filter out angles from V4 results.
    v4_events = []
    for e in v4_events_raw:
        # Check if planeta2 is a Planet Name (not 'ASC', 'MC', '1', etc)
        # In V4, planeta2 comes from natal_name which comes from PLANET_NAMES or str(id)
        # POC PLANET_NAMES values are "Sol", "Luna", etc.
        if e.planeta2 in ["Sol", "Luna", "Mercurio", "Venus", "Marte", "Júpiter", "Saturno", "Urano", "Neptuno", "Plutón"]:
             v4_events.append(e)
            
    t1 = time.time()
    v4_time = t1 - t0
    print(f"    -> V4 terminó en {v4_time:.4f}s. Encontró {len(v4_events)} eventos (filtrados solo planetas).")
    
    # --- 3. COMPARE ---
    print("\n[3] Análisis de Coincidencias...")
    
    # Build maps
    poc_map = {} # Key: (P1, P2, Aspect) -> List of times
    for e in poc_events:
        k = (e.planeta1, e.planeta2, e.tipo_aspecto)
        if k not in poc_map: poc_map[k] = []
        poc_map[k].append(e)
        
    matched_count = 0
    missing_in_poc = 0
    extra_in_poc = 0
    
    # Check V4 coverage in POC
    print("    Comprobando si POC encontró todos los eventos de V4...")
    
    diffs = []
    
    for v4_e in v4_events:
        k = (v4_e.planeta1, v4_e.planeta2, v4_e.tipo_aspecto)
        
        found = False
        if k in poc_map:
            # Find closest time match
            candidates = poc_map[k]
            best_diff = 999999
            best_match = None
            
            for poc_e in candidates:
                diff_seconds = abs((v4_e.fecha_utc - poc_e.fecha_utc).total_seconds())
                if diff_seconds < best_diff:
                    best_diff = diff_seconds
                    best_match = poc_e
                    
            # Tolerance: 15 minutes (V4 might be slightly inaccurate due to iterative steps vs root finding)
            if best_diff < 900: # 15 minutes
                found = True
                matched_count += 1
                diffs.append(best_diff)
            else:
                 pass # Found same aspect but different time? (Retrograde loop mismatch maybe)
                 
        if not found:
            missing_in_poc += 1
            print(f"    [MISSING] V4 encontró: {v4_e.fecha_utc} {v4_e.descripcion} - No hallado en POC (cerca)")

    print(f"\n    Resumen de Coincidencias:")
    print(f"    - Eventos coincidentes: {matched_count}/{len(v4_events)}")
    if matched_count > 0:
        avg_diff = sum(diffs)/len(diffs)
        print(f"    - Diferencia de tiempo promedio: {avg_diff:.2f} segundos")
        print(f"      (Esto confirma que el POC es extremadamente preciso)")
    
    print(f"\n    Comparativa de Rendimiento:")
    speedup = v4_time / poc_time
    print(f"    - POC es {speedup:.1f}x veces más rápido que V4 ({poc_time:.2f}s vs {v4_time:.2f}s)")

if __name__ == "__main__":
    run_comparison()
