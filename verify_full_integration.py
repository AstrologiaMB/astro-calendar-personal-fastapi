
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory
from src.core.constants import EventType

# 1. Setup Data (Real User Data)
natal_data = {
    'points': {
        'Sun': {'longitude': 275.279}, # Capricorn 5°16'
        'Moon': {'longitude': 199.532}, # Libra 19°31'
        'Mercury': {'longitude': 262.203},
        'Venus': {'longitude': 255.485},
        'Mars': {'longitude': 163.635},
        'Jupiter': {'longitude': 46.992},
        'Saturn': {'longitude': 330.435},
        'Uranus': {'longitude': 163.784},
        'Neptune': {'longitude': 229.475},
        'Pluto': {'longitude': 166.452}
    },
    'location': {
        'latitude': -34.6037,
        'longitude': -58.3816,
        'timezone': 'America/Argentina/Buenos_Aires'
    }
}

print("=== VERIFICACIÓN INTEGRACIÓN VECTORIZADA ===")

# 2. Instantiate via Factory (Testing Factory Update)
print("1. Probando Factory con 'vectorized'...")
try:
    calculator = TransitsCalculatorFactory.create_calculator(natal_data, calculator_type="vectorized")
    print(f"✅ Calculador creado: {type(calculator)}")
except Exception as e:
    print(f"❌ Error creando calculador: {e}")
    exit(1)

# 3. Validation Run (2025 Full Year)
start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
end_date = datetime(2025, 12, 31, tzinfo=ZoneInfo("UTC"))

print("\n2. Ejecutando Cálculo (2025 Completo)...")
t0 = time.time()
events = calculator.calculate_all(start_date, end_date)
t1 = time.time()
elapsed = t1 - t0

print(f"✅ Cálculo finalizado en {elapsed:.4f} segundos")
print(f"   Eventos generados: {len(events)}")

if elapsed > 1.0:
    print("⚠️ ALERTA: Rendimiento sospechoso (>1s). Verificar si es V4 disfrazado.")
else:
    print("🚀 CONFIRMADO: Rendimiento Vectorizado (<1s).")

# 4. Check for New Aspects (Sextiles/Trines)
sextiles = [e for e in events if "Sextil" in e.tipo_aspecto]
trines = [e for e in events if "Trígono" in e.tipo_aspecto]

print("\n3. Verificando Nuevos Aspectos:")
print(f"   Sextiles encontrados: {len(sextiles)}")
print(f"   Trígonos encontrados: {len(trines)}")

if len(sextiles) > 0 and len(trines) > 0:
    print("✅ Feature Upgrade Confirmado: Sextiles y Trígonos presentes.")
else:
    print("❌ ERROR: No se encontraron Sextiles/Trígonos. ¿Es el calculador correcto?")

# 5. Spot Check (Real Verified Event)
# Target: Jan 2 2025: Luna Sextile Venus
# Verified via dump: 2025-01-02 14:05:51+00:00 - Luna Sextil Venus Natal (Luna vs Venus)
print("\n4. Validación de Precisión (Spot Check):")

target_event = None
for e in events:
    # Check for Moon/Venus interaction
    if e.planeta1 == "Luna" and e.planeta2 == "Venus" and e.tipo_aspecto == "Sextil":
        # Check date (Jan 2)
        if e.fecha_utc.month == 1 and e.fecha_utc.day == 2:
            target_event = e
            break

if target_event:
    print(f"   Evento encontrado: {target_event.descripcion}")
    print(f"   Posición 1: {target_event.metadata['posicion1']}")
    print(f"   Posición 2: {target_event.metadata['posicion2']}")
    print(f"   Fecha UTC: {target_event.fecha_utc}")
    print("   Validación: OK (Este evento es un Sextil, ¡prueba de fuego del upgrade!)")
else:
    print("❌ Evento Target (Luna Sextil Venus) NO encontrado.")

print("\n=== FIN DE VERIFICACIÓN ===")
