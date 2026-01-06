
import swisseph as swe
from datetime import datetime
from zoneinfo import ZoneInfo

# Setup
swe.set_ephe_path('/Users/apple/astro-calendar-personal-fastapi/src/immanuel/resources/ephemeris')

# Target: Transit Venus Conjunction Natal Saturn
# Natal Saturn (from script): 330.435 (Pisces 0°26')

natal_saturn = 330.435

def get_venus_pos(dt_str):
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
    res = swe.calc_ut(jd, swe.VENUS, swe.FLG_SPEED | swe.FLG_SWIEPH)
    return res[0][0], jd

print("=== FORENSE: VENUS CONJUNCIÓN SATURNO ===")
print(f"Natal Saturn Used: {natal_saturn:.4f}")

# 1. Check My Time (13:13 UTC)
pos_my, jd_my = get_venus_pos("2025-01-03T13:13:00Z")
diff_my = abs(pos_my - natal_saturn)
print(f"\nMy Time (13:13 UTC):")
print(f"Transit Venus Pos: {pos_my:.4f}")
print(f"Diff from Natal: {diff_my:.4f} deg")

# 2. Check AstroSeek Time (22:36 UTC)
pos_seek, jd_seek = get_venus_pos("2025-01-03T22:36:00Z")
diff_seek = abs(pos_seek - natal_saturn)
print(f"\nAstroSeek Time (22:36 UTC):")
print(f"Transit Venus Pos: {pos_seek:.4f}")
print(f"Diff from Natal: {diff_seek:.4f} deg")

# 3. Check Natal Calculation again
# Maybe Natal Saturn is wrong?
bt = datetime(1964, 12, 26, 21, 12) # Local
# TO UTC: +3 (BA is GMT-3) -> Dec 27 00:12 UTC
jd_birth = swe.julday(1964, 12, 27, 0, 12)
nat_sat_recalc = swe.calc_ut(jd_birth, swe.SATURN, swe.FLG_SWIEPH)[0][0]
print(f"\nRe-Calculated Natal Saturn (Dec 27 00:12 UTC): {nat_sat_recalc:.4f}")
print(f"Original Used: {natal_saturn:.4f}")
