
import swisseph as swe
import immanuel.tools.ephemeris as eth
from immanuel.setup import settings
import os

print("=== VERIFICACIÓN CONFIGURACIÓN SWISSEPH ===")
# Force intialization if lazy
try:
    eth.planet(0, 2460000)
except:
    pass

# Inspect settings
print(f"Settings attributes: {dir(settings)}")
# Try common names
try:
    path = getattr(settings, 'EPHEMERIS_PATH', None) or getattr(settings, 'ephemeris_path', None)
    print(f"Ephemeris Path found: {path}")
    
    if path and os.path.exists(path):
        files = os.listdir(path)
        se1_files = [f for f in files if f.endswith('.se1')]
        print(f"Archivos .se1 encontrados: {len(se1_files)}")
except Exception as e:
    print(f"Error checking path: {e}")

# Check valid execution
try:
    jd = 2460676.5 # Jan 1 2026 roughly
    pid = 1 # Moon (fast mover, high parallax/error potential)
    
    # 1. Default Calculation (What Production Uses)
    res_default = swe.calc_ut(jd, pid)
    pos_default = res_default[0][0]
    
    # 2. Forced Moshier Calculation
    res_moshier = swe.calc_ut(jd, pid, swe.FLG_MOSEPH)
    pos_moshier = res_moshier[0][0]
    
    print(f"\nResultados para Luna (JD {jd}):")
    print(f"Default Pos: {pos_default:.6f}")
    print(f"Moshier Pos: {pos_moshier:.6f}")
    print(f"Diferencia:  {abs(pos_default - pos_moshier):.6f}")
    
    if abs(pos_default - pos_moshier) < 0.00001:
        print("\n⚠️  ¡ALERTA! El resultado Default es IDÉNTICO a Moshier.")
        print("    Esto significa que el sistema NO está encontrando los archivos SwissEph y ha hecho fallback a Moshier silenciosamente.")
    else:
        print("\n✅  ¡CONFIRMADO! El resultado Default DIFIERE de Moshier.")
        print("    Esto significa que el sistema ESTÁ USANDO los archivos de efemérides (NASA/SwissEph).")

except swe.Error as e:
    print(f"❌ Error calculando: {e}")

