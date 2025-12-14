import swisseph as swe
import pytz
from datetime import datetime
from zoneinfo import ZoneInfo

def julian_day(dt):
    if dt.tzinfo:
        dt = dt.astimezone(pytz.UTC)
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

def get_positions(dt_str, label):
    # Parse YYYY-MM-DD HH:MM
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    dt = dt.replace(tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    
    jd = julian_day(dt)
    
    sun = swe.calc_ut(jd, swe.SUN)[0][0]
    moon = swe.calc_ut(jd, swe.MOON)[0][0]
    jup = swe.calc_ut(jd, swe.JUPITER)[0][0]
    
    # helper for sign
    signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    def fmt(deg):
        s = int(deg / 30)
        d = deg % 30
        return f"{signs[s]} {d:.2f}°"
        
    print(f"\n--- {label} ({dt}) ---")
    print(f"Sun: {fmt(sun)}")
    print(f"Moon: {fmt(moon)}")
    print(f"Jupiter: {fmt(jup)}")
    return sun, moon

def verify_dates():
    pluto_natal = 166.31
    print(f"Natal Pluto: {pluto_natal:.2f}° (Virgo 16°18')")
    
    # 1. Check 01:55 UTC (The user's claimed time, and approximate New Moon time)
    dt1_str = "2024-09-03 01:55"
    dt1 = datetime.strptime(dt1_str, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.UTC)
    jd1 = julian_day(dt1)
    
    sun1 = swe.calc_ut(jd1, swe.SUN)[0][0]
    moon1 = swe.calc_ut(jd1, swe.MOON)[0][0]
    orb1 = abs(moon1 - pluto_natal)
    
    print(f"\n--- AT 01:55 UTC (Official New Moon Time) ---")
    print(f"Sun : {sun1:.2f}° (Virgo {sun1%30:.2f})")
    print(f"Moon: {moon1:.2f}° (Virgo {moon1%30:.2f})")
    print(f"Diff Sun-Moon: {abs(sun1-moon1):.4f}° (Exact Phase!)")
    print(f"Dist to Pluto: {orb1:.2f}°")
    print(f"Detected (<=4.0)? {'YES' if orb1 <=4.0 else 'MO NO'}")
    
    # 2. Check 04:55 UTC (01:55 BA Time)
    dt2_str = "2024-09-03 04:55"
    dt2 = datetime.strptime(dt2_str, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.UTC)
    jd2 = julian_day(dt2)
    
    sun2 = swe.calc_ut(jd2, swe.SUN)[0][0]
    moon2 = swe.calc_ut(jd2, swe.MOON)[0][0]
    orb2 = abs(moon2 - pluto_natal)
    
    print(f"\n--- AT 04:55 UTC (01:55 AM Buenos Aires) ---")
    print(f"Sun : {sun2:.2f}°")
    print(f"Moon: {moon2:.2f}° (User Data was 12°33' -> 12.55°)")
    print(f"Diff Sun-Moon: {abs(sun2-moon2):.4f}° (Past Phase)")
    print(f"Dist to Pluto: {orb2:.2f}°")
    print(f"Detected (<=4.0)? {'YES' if orb2 <=4.0 else 'NO'}")


if __name__ == "__main__":
    verify_dates()
