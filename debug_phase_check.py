import sys
import os
from datetime import datetime
import pytz
import ephem
from zoneinfo import ZoneInfo
import swisseph as swe

# Basic conversions
def julian_day(dt):
    # Convert to UTC if not
    if dt.tzinfo:
        dt = dt.astimezone(pytz.UTC)
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

def _calcular_orbe(pos1: float, pos2: float) -> float:
    diff = abs(pos1 - pos2)
    if diff > 180:
        diff = 360 - diff
    return diff

def debug_check():
    # 1. Setup Natal Data
    # 1964-12-26 21:12 Buenos Aires (-3)
    local_dt = datetime(1964, 12, 26, 21, 12, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    utc_dt = local_dt.astimezone(pytz.UTC)
    jd_natal = julian_day(utc_dt)
    
    # Scan 2024-2026 for phases conjunct Pluto
    start_dt = datetime(2024, 1, 1, tzinfo=pytz.UTC)
    end_dt = datetime(2026, 12, 31, tzinfo=pytz.UTC)
    
    # Calculate Pluto Natal
    res = swe.calc_ut(jd_natal, swe.PLUTO)
    pluto_abs = res[0][0]
    print(f"Plutón Natal: {pluto_abs:.4f}° (Virgo)")
    
    print("\n--- Escaneando Fases en Conjunción con Plutón (Orb 4°) 2024-2026 ---")
    
    curr = ephem.Date(start_dt)
    end = ephem.Date(end_dt)
    
    # Helper to process a date
    def check_date(name, d_ephem):
        dt = ephem.Date(d_ephem).datetime()
        dt = pytz.utc.localize(dt)
        if dt > end_dt: return
        
        jd = julian_day(dt)
        m_pos = swe.calc_ut(jd, swe.MOON)[0][0]
        orb = _calcular_orbe(m_pos, pluto_abs)
        
        if orb <= 5.0: # Check a bit wider to see near misses
            print(f"{dt.date()} {name:<16} Moon: {m_pos:.2f}° Orb: {orb:.2f}° {'✅' if orb <= 4.0 else '❌'}")

    while curr < end:
        # Get next 4 phases
        nm = ephem.next_new_moon(curr)
        fq = ephem.next_first_quarter_moon(curr)
        fm = ephem.next_full_moon(curr)
        lq = ephem.next_last_quarter_moon(curr)
        
        # Find the earliest one to advance loop
        next_event = min(nm, fq, fm, lq)
        
        if next_event == nm: check_date("Luna Nueva", nm)
        elif next_event == fq: check_date("Cuarto Creciente", fq)
        elif next_event == fm: check_date("Luna Llena", fm)
        elif next_event == lq: check_date("Cuarto Menguante", lq)
        
        curr = next_event + 0.01 # Advance slightly



if __name__ == "__main__":
    debug_check()
