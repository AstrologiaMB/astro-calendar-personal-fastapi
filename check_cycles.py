import swisseph as swe
import pytz
from datetime import datetime, timedelta
import ephem

def julian_day(dt):
    if dt.tzinfo:
        dt = dt.astimezone(pytz.UTC)
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

def fmt_pos(deg):
    return f"Virgo {deg:.2f}°"

def check_cycles():
    # Natal Positions
    # Uranus: Virgo 14.81 (14°49')
    # Pluto:  Virgo 16.30 (16°18')
    # Mars:   Virgo 22.32 (22°19')
    uranus = 164.81
    pluto = 166.30
    mars = 172.32
    
    # 1. Verify Event 1: June 3, 2025 (First Quarter)
    # User says: 12° 50' Virgo (162.83°)
    d1 = datetime(2025, 6, 3, 0, 40) # Local time? Or UTC? User says "00:40". Check UTC.
    # Ephem usually gives UTC. Let's find exact FQ.
    
    start_jun = ephem.Date("2025/6/1")
    fq_date = ephem.next_first_quarter_moon(start_jun)
    dt_fq = ephem.Date(fq_date).datetime().replace(tzinfo=pytz.UTC)
    
    jd_fq = julian_day(dt_fq)
    moon_fq = swe.calc_ut(jd_fq, swe.MOON)[0][0]
    
    print(f"\n--- Event 1: June 3, 2025 ---")
    print(f"Time (UTC): {dt_fq}")
    print(f"Moon Pos: {fmt_pos(moon_fq % 30)} (Abs: {moon_fq:.2f})")
    
    # Check User's Conjunctions
    print(f"Dist to Uranus ({uranus:.2f}): {abs(moon_fq - uranus):.2f}°")
    print(f"Dist to Pluto ({pluto:.2f}): {abs(moon_fq - pluto):.2f}°")
    
    # Trace Family 1 (Back 9 months to New Moon)
    # New Moon should be ~ Sept 2024
    start_sep24 = ephem.Date("2024/8/25")
    nm_date = ephem.next_new_moon(start_sep24)
    dt_nm = ephem.Date(nm_date).datetime().replace(tzinfo=pytz.UTC)
    jd_nm = julian_day(dt_nm)
    moon_nm = swe.calc_ut(jd_nm, swe.MOON)[0][0]
    
    print(f"-> Family Ancestor (New Moon -9mo): {dt_nm}")
    print(f"   Moon Pos: {fmt_pos(moon_nm % 30)} (Abs: {moon_nm:.2f})")
    print(f"   Link: {abs(moon_fq - moon_nm):.2f}° difference")

    # 2. Verify Event 2: Dec 11, 2025 (Last Quarter)
    # User says: 20° 4' Virgo
    start_dec = ephem.Date("2025/12/1")
    lq_date = ephem.next_last_quarter_moon(start_dec)
    dt_lq = ephem.Date(lq_date).datetime().replace(tzinfo=pytz.UTC)
    
    jd_lq = julian_day(dt_lq)
    moon_lq = swe.calc_ut(jd_lq, swe.MOON)[0][0]
    
    print(f"\n--- Event 2: Dec 11, 2025 ---")
    print(f"Time (UTC): {dt_lq}")
    print(f"Moon Pos: {fmt_pos(moon_lq % 30)} (Abs: {moon_lq:.2f})")
    
    # Check User's Conjunctions
    print(f"Dist to Pluto ({pluto:.2f}): {abs(moon_lq - pluto):.2f}°")
    print(f"Dist to Mars ({mars:.2f}): {abs(moon_lq - mars):.2f}°")

    # Trace Family 2 (Back 27 months to New Moon? Or just check if Sept 2023 matches)
    # Sequence: NM (Sep 23) -> FQ (Jun 24) -> FM (Mar 25) -> LQ (Dec 25)
    start_sep23 = ephem.Date("2023/9/10")
    nm_date_2 = ephem.next_new_moon(start_sep23)
    dt_nm_2 = ephem.Date(nm_date_2).datetime().replace(tzinfo=pytz.UTC)
    jd_nm_2 = julian_day(dt_nm_2)
    moon_nm_2 = swe.calc_ut(jd_nm_2, swe.MOON)[0][0]
    
    print(f"-> Family Ancestor (New Moon -27mo?): {dt_nm_2}")
    print(f"   Moon Pos: {fmt_pos(moon_nm_2 % 30)} (Abs: {moon_nm_2:.2f})")
    print(f"   Link: {abs(moon_lq - moon_nm_2):.2f}° difference")

if __name__ == "__main__":
    check_cycles()
