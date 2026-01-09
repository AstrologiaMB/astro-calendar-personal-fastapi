
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import swisseph as swe

# Add src to path
sys.path.append(os.getcwd())

from src.calculators.vectorized_transits_calculator import VectorizedTransitsCalculator, ASPECTS

# Verify ASPECTS definition
print("--- DEFINICIÓN DE ASPECTOS EN EL CÓDIGO ---")
for name, ang in ASPECTS.items():
    print(f"  {name}: {ang}")
    
# Manual Natal Positions (User's data)
natal_positions = {
    "points": {
        "Moon": {"longitude": 199.5167} # 19°31' Libra
    }
}

def main():
    print("\n--- PRUEBA DE COBERTURA DE CUADRATURAS ---")
    
    calc = VectorizedTransitsCalculator(natal_positions)
    
    # 1. Check Closing Square (Mars in Cancer) - Sep 2026
    start_dt = datetime(2026, 9, 9, tzinfo=ZoneInfo("UTC"))
    end_dt = datetime(2026, 9, 11, tzinfo=ZoneInfo("UTC"))
    
    print(f"\nBuscando eventos para Mars en Cancer (Sep 2026)...")
    events = calc.calculate_all(start_dt, end_dt)
    
    found_sep = False
    for e in events:
        if e.planeta1 == "Marte" and "Luna" in e.planeta2 and "Cuadratura" in e.tipo_aspecto:
            print(f"  ✅ ENCONTRADO: {e.fecha_utc} | {e.descripcion}")
            found_sep = True
            
    # 2. Check Opening Square (Mars in Capricorn) - Jan 2026
    start_dt_jan = datetime(2026, 1, 8, tzinfo=ZoneInfo("UTC"))
    end_dt_jan = datetime(2026, 1, 10, tzinfo=ZoneInfo("UTC"))
    
    print(f"\nBuscando eventos para Mars en Capricorn (Jan 2026)...")
    events_jan = calc.calculate_all(start_dt_jan, end_dt_jan)
    
    found_jan = False
    for e in events_jan:
        if e.planeta1 == "Marte" and "Luna" in e.planeta2 and "Cuadratura" in e.tipo_aspecto:
             print(f"  ✅ ENCONTRADO: {e.fecha_utc} | {e.descripcion}")
             found_jan = True
             
    if found_sep and found_jan:
        print("\n✅ ÉXITO TOTAL: Ambos aspectos (Creciente y Menguante) detectados correctamente.")
    else:
        print("\n❌ FALLO: No se detectaron ambos aspectos.")

if __name__ == "__main__":
    main()
