
from datetime import datetime, timezone
import re
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory

# 1. AstroSeek Data (Parsed from ICS)
# Format: (DateUTC, P1, Aspect, P2)
astroseek_data = [
    ("2025-01-02T21:07:00Z", "Mercury", "square", "Mars"),
    ("2025-01-03T22:36:00Z", "Venus", "conjunction", "Saturn"),
    ("2025-01-04T20:54:00Z", "Saturn", "opposition", "Uranus"),
    ("2025-01-04T22:28:00Z", "Sun", "trine", "Uranus"),
    ("2025-01-06T09:27:00Z", "Sun", "trine", "Pluto"),
    ("2025-01-06T12:59:00Z", "Sun", "trine", "Jupiter"),
    ("2025-01-08T04:15:00Z", "Venus", "sextile", "Sun"),
    ("2025-01-09T00:47:00Z", "Mercury", "sextile", "Saturn"),
    ("2025-01-09T05:03:00Z", "Sun", "sextile", "Neptune"),
    ("2025-01-09T13:17:00Z", "Sun", "square", "Moon"),
    ("2025-01-12T02:16:00Z", "Mercury", "conjunction", "Sun"),
    ("2025-01-12T07:13:00Z", "Sun", "trine", "Mars"),
    ("2025-01-12T10:17:00Z", "Venus", "square", "Venus"),
    ("2025-01-17T17:39:00Z", "Venus", "opposition", "Uranus"),
    ("2025-01-18T11:25:00Z", "Mercury", "trine", "Uranus"),
    ("2025-01-19T07:03:00Z", "Venus", "opposition", "Pluto"),
    ("2025-01-19T10:42:00Z", "Mercury", "trine", "Pluto"),
    ("2025-01-19T10:52:00Z", "Venus", "sextile", "Jupiter"),
    ("2025-01-19T13:03:00Z", "Mercury", "trine", "Jupiter"),
    ("2025-01-21T07:19:00Z", "Mercury", "sextile", "Neptune"),
    ("2025-01-21T07:40:00Z", "Saturn", "opposition", "Pluto"),
    ("2025-01-21T12:43:00Z", "Mercury", "square", "Moon"),
    ("2025-01-22T02:25:00Z", "Venus", "square", "Mercury"),
    ("2025-01-22T09:03:00Z", "Venus", "trine", "Neptune"),
    ("2025-01-22T19:49:00Z", "Saturn", "sextile", "Jupiter"),
    ("2025-01-23T07:39:00Z", "Mercury", "trine", "Mars"),
    ("2025-01-25T21:21:00Z", "Venus", "opposition", "Mars"),
    ("2025-01-26T06:13:00Z", "Mars", "sextile", "Mars"),
    ("2025-01-29T06:48:00Z", "Sun", "sextile", "Venus"),
]

# 2. Setup Calculator (AstroSeek Natal Data)
natal_data = {
    'points': {
        'Sun': {'longitude': 275.267},     # Capricorn 5°16'
        'Moon': {'longitude': 199.517},    # Libra 19°31'
        'Mercury': {'longitude': 258.917}, # Sagittarius 18°55' (Retrograde?) Wait. 18 Sag = 240+18 = 258.
        'Venus': {'longitude': 249.600},   # Sagittarius 9°36' = 240+9.6 = 249.6
        'Mars': {'longitude': 172.317},    # Virgo 22°19' = 150+22.31 = 172.317. PREVIOUS WAS 163 (Virgo 13). HUGE DIFF.
        'Jupiter': {'longitude': 46.450},  # Taurus 16°27' = 30+16.45
        'Saturn': {'longitude': 330.833},  # Pisces 0°50' = 330 + 0.833
        'Uranus': {'longitude': 164.817},  # Virgo 14°49' = 150 + 14.81
        'Neptune': {'longitude': 229.167}, # Scorpio 19°10' = 210 + 19.16
        'Pluto': {'longitude': 166.300}    # Virgo 16°18' = 150 + 16.3
    },
    'location': {
        'latitude': -34.6037,
        'longitude': -58.3816,
        'timezone': 'America/Argentina/Buenos_Aires'
    }
}

calc = TransitsCalculatorFactory.create_calculator(natal_data, calculator_type="vectorized")

# Calculate
start = datetime(2025, 1, 1, tzinfo=timezone.utc)
end = datetime(2025, 1, 31, 23, 59, tzinfo=timezone.utc)
my_events = calc.calculate_all(start, end)

# 3. Comparator
print(f"=== COMPARATIVA ENERO 2025 (AstroSeek vs Vectorized) ===")
print(f"{'AstroSeek Date':<20} | {'My Date':<20} | {'Event':<40} | {'Diff (min)':<10}")
print("-" * 100)

matches = 0
total = len(astroseek_data)

# Helper Mappings
trans_map = {
    "Mercurio": "Mercury", "Venus": "Venus", "Marte": "Mars", 
    "Júpiter": "Jupiter", "Saturno": "Saturn", "Urano": "Uranus", 
    "Neptuno": "Neptune", "Plutón": "Pluto", "Sol": "Sun", "Luna": "Moon"
}
aspect_map = {
    "Conjunción": "conjunction", "Oposición": "opposition", 
    "Cuadratura": "square", "Trígono": "trine", "Sextil": "sextile"
}

for item in astroseek_data:
    seek_dt = datetime.fromisoformat(item[0].replace('Z', '+00:00'))
    p1 = item[1]
    asp = item[2]
    p2 = item[3]
    
    # Try to find match in my_events
    found = None
    for me in my_events:
        mp1 = trans_map.get(me.planeta1)
        mp2 = trans_map.get(me.planeta2)
        masp = aspect_map.get(me.tipo_aspecto)
        
        # Check matching planets and aspect
        if mp1 == p1 and mp2 == p2 and masp == asp:
            # Check date proximity (< 24 hours to be safe, but usually minutes)
            delta = abs((seek_dt - me.fecha_utc).total_seconds())
            if delta < 86400: # Same day match
                found = me
                break
    
    if found:
        matches += 1
        diff_min = (found.fecha_utc - seek_dt).total_seconds() / 60
        my_date_str = found.fecha_utc.strftime("%Y-%m-%d %H:%M")
        seek_date_str = seek_dt.strftime("%Y-%m-%d %H:%M")
        print(f"{seek_date_str:<20} | {my_date_str:<20} | {p1} {asp} {p2:<20} | {diff_min:>10.1f}")
    else:
        print(f"{item[0]:<20} | {'MISSING':<20} | {p1} {asp} {p2:<20} | {'---':>10}")

print("-" * 100)
print(f"Resumen: {matches}/{total} coincidencias encontradas.")
