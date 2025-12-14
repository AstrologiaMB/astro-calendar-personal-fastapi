import sys
import os
from datetime import datetime

# Add root to path
sys.path.append(os.getcwd())

from src.services.cycles_service import get_active_cycles
from src.api.schemas import LocationData

def verify_pluto_cycle():
    print("Verifying Pluto Cycle Detection...")
    
    # Target: Dec 11, 2025 (Last Quarter in Virgo)
    target_date = datetime(2025, 12, 11)
    
    # Location: Buenos Aires
    location = LocationData(
        latitude=-34.6037,
        longitude=-58.3816,
        name="Buenos Aires",
        timezone="America/Argentina/Buenos_Aires"
    )
    
    # Birth Date (for Metonic) - e.g. 1980-01-01 (Example)
    birth_date = datetime(1980, 1, 1)
    
    print(f"Target Date: {target_date}")
    
    result = get_active_cycles(target_date, location, birth_date)
    
    print(f"Active Cycles Found: {len(result.active_cycles)}")
    
    for cycle in result.active_cycles:
        print(f"\nFAMILY SIGN: {cycle.family_sign}")
        print(f"Metonic Index: {cycle.metonic_index}")
        print(f"Seed (NM): {cycle.seed.date} ({cycle.seed.sign})")
        if cycle.action:
            print(f"Action (FQ): {cycle.action.date} ({cycle.action.sign})")
        if cycle.fruition:
            print(f"Fruition (FM): {cycle.fruition.date} ({cycle.fruition.sign})")
        if cycle.release:
            print(f"Release (LQ): {cycle.release.date} ({cycle.release.sign})")
            
        # Assertion Logic
        if cycle.family_sign == "Virgo" and cycle.release and "2025-12" in cycle.release.date:
            print("\n✅ SUCCESS: Detected Virgo Family Release Phase in Dec 2025!")
            seed_year = datetime.fromisoformat(cycle.seed.date).year
            if seed_year == 2023:
                print("✅ SUCCESS: Seed traced back to 2023 correctly.")
            else:
                print(f"❌ FAIL: Expected Seed 2023, got {seed_year}")
                
if __name__ == "__main__":
    verify_pluto_cycle()
