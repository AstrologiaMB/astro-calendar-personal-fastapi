import swisseph as swe
import sys

print(f"Python Version: {sys.version}")
try:
    print(f"Swisseph Version: {swe.version}")
    # Quick calc check
    jul_day = swe.julday(2025, 1, 1)
    pos = swe.calc_ut(jul_day, swe.SUN)[0]
    print(f"Swisseph Calculation Test (Sun 2025-01-01): {pos[0]}")
    print("ENVIRONMENT STATUS: SAFE")
except Exception as e:
    print(f"ENVIRONMENT ERROR: {e}")
