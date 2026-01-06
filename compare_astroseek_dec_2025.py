
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.calculators.poc_vectorized_transits import PocVectorizedTransitsCalculator
import swisseph as swe

# Patch for safety
swe.set_ephe_path('')

NATAL_DATA = {
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

# Mapping AstroSeek names to POC names
# AstroSeek: "Transit Mars" -> POC: "Marte"
# AstroSeek: "Moon" -> POC: "Luna"
# AstroSeek: "Merc." -> POC: "Mercurio"

def run_december_check():
    print("=== VERIFICACIÓN EXACTITUD VS ASTROSEEK (DIC 2025 - REAL) ===")
    
    calc = PocVectorizedTransitsCalculator(NATAL_DATA)
    start = datetime(2025, 12, 1, tzinfo=ZoneInfo("UTC"))
    end = datetime(2025, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
    
    events = calc.calculate_all(start, end)
    
    # Target events from user's provided list (AstroSeek GMT-3)
    targets = [
        {"p1": "Marte", "p2": "Luna", "asp": "Sextil", "seek_time": "Dec 1, 04:42"},
        {"p1": "Venus", "p2": "Saturno", "asp": "Cuadratura", "seek_time": "Dec 1, 09:26"},
        {"p1": "Sol", "p2": "Venus", "asp": "Conjunción", "seek_time": "Dec 1, 10:33"},
        {"p1": "Mercurio", "p2": "Marte", "asp": "Sextil", "seek_time": "Dec 4, 03:12"},
        {"p1": "Sol", "p2": "Urano", "asp": "Cuadratura", "seek_time": "Dec 6, 13:59"},
        {"p1": "Sol", "p2": "Plutón", "asp": "Cuadratura", "seek_time": "Dec 8, 01:06"},
        {"p1": "Venus", "p2": "Venus", "asp": "Conjunción", "seek_time": "Dec 8, 08:39"},
        {"p1": "Sol", "p2": "Mercurio", "asp": "Conjunción", "seek_time": "Dec 10, 14:57"},
        {"p1": "Marte", "p2": "Sol", "asp": "Conjunción", "seek_time": "Dec 22, 03:58"},
        {"p1": "Sol", "p2": "Sol", "asp": "Conjunción", "seek_time": "Dec 26, 16:25"}, # Solar Return
        {"p1": "Venus", "p2": "Sol", "asp": "Conjunción", "seek_time": "Dec 28, 18:06"}
    ]
    
    print(f"{'EVENTO':<40} | {'POC (UTC)':<20} | {'POC (BsAs)':<20} | {'ASTROSEEK':<15} | {'DIFERENCIA':<10}")
    print("-" * 115)
    
    found_count = 0
    
    for t in targets:
        # Find matching event in POC results
        match = None
        for e in events:
            # Map names if needed, but POC uses Spanish names already
            if (e.planeta1 == t["p1"] and 
                e.planeta2 == t["p2"] and 
                e.tipo_aspecto == t["asp"]):
                
                # Check if date is close (Dec +/- 1 day) to handle duplicate aspects
                # AstroSeek "Dec 1" means 2025-12-01
                # Parse seek day
                seek_day = int(t["seek_time"].split(",")[0].split(" ")[1])
                if abs(e.fecha_utc.day - seek_day) <= 1:
                    match = e
                    break
        
        if match:
            found_count += 1
            # Convert POC to Buenos Aires for comparison
            bsas_tz = ZoneInfo("America/Argentina/Buenos_Aires")
            dt_bsas = match.fecha_utc.astimezone(bsas_tz)
            
            # Print row
            event_str = f"{t['p1']} {t['asp']} {t['p2']}"
            poc_utc = match.fecha_utc.strftime("%d %H:%M")
            poc_local = dt_bsas.strftime("%d %H:%M")
            
            # Calc timediff roughly (assuming AstroSeek is Local)
            # Parse AstroSeek time "Dec 1, 04:42"
            try:
                parts = t["seek_time"].replace(",", "").split(" ")
                day = int(parts[1])
                hm = parts[2].split(":")
                h, m = int(hm[0]), int(hm[1])
                dt_seek = datetime(2025, 12, day, h, m, tzinfo=bsas_tz)
                
                diff_minutes = (dt_bsas - dt_seek).total_seconds() / 60
                diff_str = f"{diff_minutes:+.1f} min"
            except:
                diff_str = "?"
                
            print(f"{event_str:<40} | {poc_utc:<20} | {poc_local:<20} | {t['seek_time']:<15} | {diff_str:<10}")
        else:
             print(f"MISSING: {t}")

    print("-" * 115)
    print(f"Total eventos analizados: {len(events)} en Diciembre")

if __name__ == "__main__":
    run_december_check()
