
import swisseph as swe
from datetime import datetime

# Setup
swe.set_ephe_path('/Users/apple/astro-calendar-personal-fastapi/src/immanuel/resources/ephemeris')

# Target: Venus Conjunction Saturn
# AstroSeek Time: Jan 3 22:36 UTC
# Target Natal Saturn: 330.833

seek_time = "2025-01-03T22:36:00Z"
target_natal_saturn = 330.833

def get_venus(dt_str, flag):
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
    res = swe.calc_ut(jd, swe.VENUS, swe.FLG_SPEED | flag)
    return res[0][0]

print("=== FORENSE: ¿True Positions (Apparent) vs Mean? ===")
print(f"Target Natal Saturn: {target_natal_saturn}")
print(f"AstroSeek Time: 22:36 UTC")

# 1. Geometric (Mean Equinox) - CURRENT
pos_geo = get_venus(seek_time, swe.FLG_SWIEPH)
diff_geo = abs(pos_geo - target_natal_saturn)
print(f"\n[Geometric/Mean] Venus Pos: {pos_geo:.4f}")
print(f"Diff: {diff_geo:.4f} deg")

# 2. True (Apparent - Nutation + Aberration)
pos_true = get_venus(seek_time, swe.FLG_SWIEPH | swe.FLG_TRUEPOS)
diff_true = abs(pos_true - target_natal_saturn)
print(f"\n[True/Apparent]  Venus Pos: {pos_true:.4f}")
print(f"Diff: {diff_true:.4f} deg")

if diff_true < diff_geo:
    print("\n✅ EUREKA: Usar FLG_TRUEPOS reduce el error.")
    msg = "AstroSeek usa Posiciones Aparentes (True Equinox)."
else:
    print("\n❌ Falló: FLG_TRUEPOS no mejoró o empeoró.")
    msg = "La causa es otra (Topocéntrica?)"

print(msg)
