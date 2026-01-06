
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.poc_vectorized_transits import PocVectorizedTransitsCalculator

# Hardcoded constants (matching POC)
SUN=0; MOON=1; MERCURY=2; VENUS=3; MARS=4;
JUPITER=5; SATURN=6; URANUS=7; NEPTUNE=8; PLUTO=9

NATAL_DATA = {
    "name": "Test User",
    "points": {
        "Sun": {"longitude": 275.40}, 
        "Moon": {"longitude": 185.20}, 
        "Mercury": {"longitude": 265.1},
        "Venus": {"longitude": 240.5},
        "Mars": {"longitude": 170.2},
        # Arbitrary positions to trigger aspects
        "Jupiter": {"longitude": 10.0}, 
        "Saturn": {"longitude": 330.1},
        "Uranus": {"longitude": 160.5},
        "Neptune": {"longitude": 230.2},
        "Pluto": {"longitude": 155.4}
    }
}

def verify_retrograde():
    print("=== VERIFICANDO RETROGRADACIONES (MERCURIO 2025) ===")
    
    calc = PocVectorizedTransitsCalculator(NATAL_DATA)
    start = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end = datetime(2025, 12, 31, tzinfo=ZoneInfo("UTC"))
    
    events = calc.calculate_all(start, end)
    
    # Filtrar solo eventos de Mercurio
    mercury_events = [e for e in events if e.planeta1 == "Mercurio"]
    
    # Buscar patrones de repetición (mismo aspecto 3 veces)
    print(f"Total eventos Mercurio: {len(mercury_events)}")
    
    # Agrupar por descripción para ver repetidos
    aspect_counts = {}
    for e in mercury_events:
        desc = f"{e.tipo_aspecto} {e.planeta2}"
        if desc not in aspect_counts:
            aspect_counts[desc] = []
        aspect_counts[desc].append(e)
        
    found_retro_loop = False
    for desc, evs in aspect_counts.items():
        if len(evs) >= 3:
            # Check dates to see if they are close (within 2-3 months)
            dates = [e.fecha_utc for e in evs]
            dates.sort()
            
            # Simple heuristic: if we have 3 events of exact same type in < 90 days, it's a retrograde loop
            if (dates[-1] - dates[0]).days < 100:
                print(f"\n[DETECTADO BUCLE RETRÓGRADO]: {desc}")
                for e in evs:
                    print(f"  - {e.fecha_utc.strftime('%Y-%m-%d')} | Orbe: {e.orbe:.5f}")
                found_retro_loop = True

    if not found_retro_loop:
        print("\nNo se detectaron bucles triples obvios con estos datos natales de prueba.")
        print("Esto puede ser porque los planetas natales no caen en los grados de retrogradación de 2025.")
        print("Listando todos los eventos de Mercurio para inspección manual:")
        for e in mercury_events[:10]:
             print(f"  - {e.fecha_utc.strftime('%Y-%m-%d')} {e.descripcion}")
    else:
        print("\nCONCLUSIÓN: El algoritmo detecta múltiples pasos por el mismo punto (Directo/Retrógrado/Directo).")

if __name__ == "__main__":
    verify_retrograde()
