
import swisseph as swe
from datetime import datetime

# Setup
swe.set_ephe_path('/Users/apple/astro-calendar-personal-fastapi/src/immanuel/resources/ephemeris')

# Target: Venus Conjunction Saturn
# AstroSeek Time: Jan 3 22:36 UTC
# AstroSeek Natal Saturn: 330.833 (Pisces 0°50')

seek_time = "2025-01-03T22:36:00Z"
target_natal_saturn = 330.833

def get_venus(dt_str, flag):
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
    res = swe.calc_ut(jd, swe.VENUS, swe.FLG_SPEED | flag)
    return res[0][0]

print("=== FORENSE: ¿AstroSeek usa Moshier? ===")
print(f"Target Natal Saturn: {target_natal_saturn}")
print(f"AstroSeek Time: 22:36 UTC")

# 1. JPL (Files)
pos_jpl = get_venus(seek_time, swe.FLG_SWIEPH)
diff_jpl = abs(pos_jpl - target_natal_saturn)
print(f"\n[NASA Files] Venus Pos: {pos_jpl:.4f}")
print(f"Diff: {diff_jpl:.4f} deg")

# 2. Moshier (Analytic)
pos_mos = get_venus(seek_time, swe.FLG_MOSEPH)
diff_mos = abs(pos_mos - target_natal_saturn)
print(f"\n[Moshier]    Venus Pos: {pos_mos:.4f}")
print(f"Diff: {diff_mos:.4f} deg")

if diff_mos < diff_jpl:
    print("\n💡 HIPÓTESIS: AstroSeek parece usar Moshier (o algo muy similar).")
else:
    print("\n💡 HIPÓTESIS: AstroSeek parece usar JPL.")
