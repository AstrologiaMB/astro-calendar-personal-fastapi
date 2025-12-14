import ephem
import swisseph as swe
from datetime import datetime
import pytz
import math

# Utilities
def to_jd(dt):
    if dt.tzinfo:
        dt = dt.astimezone(pytz.UTC)
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

def normalize_deg(d):
    return d % 360

def check_precision():
    # Setup Feb 2025 calculation
    start_date = datetime(2025, 1, 1, tzinfo=pytz.UTC)
    date_ephem = ephem.Date(start_date)
    
    # 1. Get Time from Ephem (Current Method)
    # Finding the Feb 5th First Quarter
    next_q = ephem.next_first_quarter_moon(date_ephem)
    # Advance to Feb
    while True:
        dt = ephem.Date(next_q).datetime()
        dt = pytz.utc.localize(dt)
        if dt.month == 2 and dt.year == 2025:
            break
        next_q = ephem.next_first_quarter_moon(next_q + 1)
        
    print(f"1. PyEphem Time (Current Code): {dt}")
    
    # 2. Check Exact Angle using Swiss Ephemeris at that time
    jd_ephem = to_jd(dt)
    
    # Flags: Speed + Gregor
    flags = swe.FLG_SPEED | swe.FLG_SWIEPH
    
    res_sun = swe.calc_ut(jd_ephem, swe.SUN, flags)
    res_moon = swe.calc_ut(jd_ephem, swe.MOON, flags)
    
    sun_lon = res_sun[0][0]
    moon_lon = res_moon[0][0]
    
    diff = normalize_deg(moon_lon - sun_lon)
    
    print(f"   Sun Position (SE): {sun_lon:.6f}°")
    print(f"   Moon Position (SE): {moon_lon:.6f}°")
    print(f"   Angle (Moon - Sun): {diff:.6f}°")
    print(f"   Expected Angle: 90.000000°")
    print(f"   Error: {abs(diff - 90.0):.6f}°")
    
    # 3. Find TRUE Swiss Ephemeris Time (Iterative Search)
    # We want Moon - Sun = 90
    
    def get_angle_err(jd):
        s = swe.calc_ut(jd, swe.SUN, flags)[0][0]
        m = swe.calc_ut(jd, swe.MOON, flags)[0][0]
        d = normalize_deg(m - s)
        return d - 90.0

    # Newton-Raphson approximation
    t = jd_ephem
    for i in range(5):
        err = get_angle_err(t)
        # Relative speed of Moon vs Sun is approx 12-13 degrees per day
        # So dt = err / 12.0
        step = err / 12.0
        t -= step
        if abs(err) < 0.000001:
            break
            
    true_jd = t
    true_dt = swe.revjul(true_jd, swe.GREG_CAL)
    # True dt format: (y, m, d, h) h is decimal
    h_decimal = true_dt[3]
    h = int(h_decimal)
    m = int((h_decimal - h) * 60)
    s = int(((h_decimal - h) * 60 - m) * 60)
    
    print(f"\n2. Swiss Ephemeris True Time: {true_dt[0]}-{true_dt[1]}-{true_dt[2]} {h}:{m}:{s} UTC")
    
    # Difference in time
    time_diff_days = abs(jd_ephem - true_jd)
    time_diff_secs = time_diff_days * 24 * 3600
    
    print(f"\nCONCLUSION:")
    print(f"Time Discrepancy: {time_diff_secs:.2f} seconds")
    
    # Moon movement in that error time
    # Moon speed approx 0.5 deg / hour = 0.0083 deg / min = 0.00013 deg / sec
    moon_speed = res_moon[0][3] # deg/day
    pos_error = abs(time_diff_days * moon_speed)
    
    print(f"Moon Position Error caused by timing: {pos_error:.6f} degrees")
    
    if pos_error < 0.01:
        print("Verdict: IMPECCABLE (Error < 0.01°)")
    else:
        print("Verdict: MARGIN OF ERROR DETECTED")

if __name__ == "__main__":
    check_precision()
