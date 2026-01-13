
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo
import pytz

# Setup Swisseph (Moshier fallback)
swe.set_ephe_path('')

def calculate_natal():
    # User Data
    # 26/12/1964 21:12 Buenos Aires
    # Timezone: -3 (ART)
    local_dt = datetime(1964, 12, 26, 21, 12, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    
    print(f"Fecha Local: {local_dt}")
    print(f"Fecha UTC:   {utc_dt}")
    
    # Julian Day
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
    print(f"Julian Day:  {jd}")
    
    # Lat/Lon for Buenos Aires (Standard)
    lat = -34.6037
    lon = -58.3816
    
    # Calculate Planets
    # IDs match POC constants
    # SUN=0...PLUTO=9
    planet_names = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    
    print("\nNATAL_DATA = {")
    print('    "name": "Maria Blaquier (Real)",')
    print('    "points": {')
    
    for i, name in enumerate(planet_names):
        # We need Topocentric positions for exactness? Usually Geocentric is standard for charts.
        # Let's stick to standard Geocentric (swe.calc_ut) as POC does.
        # If user wants Topo, we need to set topo.
        res = swe.calc_ut(jd, i, swe.FLG_MOSEPH)
        lon_deg = res[0][0]
        print(f'        "{name}": {{"longitude": {lon_deg:.6f}}},')
        
    print('    }')
    print("}")

if __name__ == "__main__":
    calculate_natal()
