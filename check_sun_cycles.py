import swisseph as swe
import pytz
from datetime import datetime
import ephem

def julian_day(dt):
    if dt.tzinfo:
        dt = dt.astimezone(pytz.UTC)
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

def fmt_pos(deg):
    signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    s = int(deg / 30)
    d = deg % 30
    return f"{signs[s]} {d:.2f}°"

def check_sun_cycles():
    # Natal Sun: Capricorn 5°16'
    # Cap is sign 9. 9*30 + 5.27 = 275.27
    natal_sun = 275.27
    print(f"Natal Sun: {fmt_pos(natal_sun)} (Abs: {natal_sun:.2f})")
    
    # 1. Investigate Dec 2025 New Moon (The missing one)
    start_dec25 = ephem.Date("2025/12/01")
    nm_date = ephem.next_new_moon(start_dec25)
    dt_nm = ephem.Date(nm_date).datetime().replace(tzinfo=pytz.UTC)
    
    jd_nm = julian_day(dt_nm)
    sun_nm = swe.calc_ut(jd_nm, swe.SUN)[0][0]
    moon_nm = swe.calc_ut(jd_nm, swe.MOON)[0][0] # Should be same
    
    print(f"\n--- Investigating New Moon Dec 2025 ---")
    print(f"Time (UTC): {dt_nm}")
    print(f"Sun/Moon Pos: {fmt_pos(moon_nm)} (Abs: {moon_nm:.2f})")
    
    dist = abs(moon_nm - natal_sun)
    if dist > 180: dist = 360 - dist
    
    print(f"Distance to Natal Sun: {dist:.2f}°")
    print(f"Should it appear (Limit 4.0°)? {'YES' if dist <= 4.0 else 'NO'}")
    
    # 2. Analyze Mar 22, 2025 (Last Quarter)
    # User says: 2° 5' Capricorn
    start_mar25 = ephem.Date("2025/3/15")
    lq_date = ephem.next_last_quarter_moon(start_mar25)
    dt_lq = ephem.Date(lq_date).datetime().replace(tzinfo=pytz.UTC)
    jd_lq = julian_day(dt_lq)
    moon_lq = swe.calc_ut(jd_lq, swe.MOON)[0][0]
    
    print(f"\n--- Event: Mar 22, 2025 (Last Quarter) ---")
    print(f"Time (UTC): {dt_lq}")
    print(f"Moon Pos: {fmt_pos(moon_lq)} (Abs: {moon_lq:.2f})")
    
    # Trace Ancestor (LQ completes a cycle started 27 months ago?)
    # LQ is 270 deg ahead of Sun.
    # We want to find the New Moon of this family.
    # Family is defined by same degree.
    # Antecedent NM should be ~ Dec 2022.
    
    # Let's just calculate Dec 2022 New Moon to see if it matches degree
    start_dec22 = ephem.Date("2022/12/01")
    nm_22 = ephem.next_new_moon(start_dec22)
    dt_nm22 = ephem.Date(nm_22).datetime().replace(tzinfo=pytz.UTC)
    jd_nm22 = julian_day(dt_nm22)
    moon_nm22 = swe.calc_ut(jd_nm22, swe.MOON)[0][0]
    
    print(f"-> Potential Ancestor (NM Dec 2022): {dt_nm22}")
    print(f"   Pos: {fmt_pos(moon_nm22)}")
    print(f"   Diff: {abs(moon_lq - moon_nm22):.2f}°")

    # 3. Analyze Sept 29, 2025 (First Quarter)
    # User says: 7° 6' Capricorn
    start_sep25 = ephem.Date("2025/9/15")
    fq_date = ephem.next_first_quarter_moon(start_sep25)
    dt_fq = ephem.Date(fq_date).datetime().replace(tzinfo=pytz.UTC)
    jd_fq = julian_day(dt_fq)
    moon_fq = swe.calc_ut(jd_fq, swe.MOON)[0][0]
    
    print(f"\n--- Event: Sept 29, 2025 (First Quarter) ---")
    print(f"Time (UTC): {dt_fq}")
    print(f"Moon Pos: {fmt_pos(moon_fq)} (Abs: {moon_fq:.2f})")
    
    # Ancestor (FQ is month 9). NM should be ~ Dec 2024.
    start_dec24 = ephem.Date("2024/12/15")
    nm_24 = ephem.next_new_moon(start_dec24)
    dt_nm24 = ephem.Date(nm_24).datetime().replace(tzinfo=pytz.UTC)
    jd_nm24 = julian_day(dt_nm24)
    moon_nm24 = swe.calc_ut(jd_nm24, swe.MOON)[0][0]
    
    print(f"-> Potential Ancestor (NM Dec 2024): {dt_nm24}")
    print(f"   Pos: {fmt_pos(moon_nm24)}")
    print(f"   Diff: {abs(moon_fq - moon_nm24):.2f}°")

if __name__ == "__main__":
    check_sun_cycles()
