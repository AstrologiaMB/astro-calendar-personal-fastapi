"""
Script para probar y comparar los calculadores de tránsitos estándar y adaptativo.
Guarda los resultados del método estándar en un archivo para evitar recalcularlos en cada ejecución.
"""
import time
import json
import os
import pickle
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.calculators.all_transits import AllTransitsCalculator
from src.calculators.all_transits_adaptive import AdaptiveTransitsCalculator
from src.core.base_event import AstroEvent

# Función para serializar un objeto AstroEvent a un diccionario
def event_to_dict(event):
    return {
        'fecha_utc': event.fecha_utc.isoformat(),
        'tipo_evento': event.tipo_evento,
        'descripcion': event.descripcion,
        'planeta1': event.planeta1,
        'planeta2': event.planeta2,
        'longitud1': event.longitud1,
        'longitud2': event.longitud2,
        'tipo_aspecto': event.tipo_aspecto,
        'orbe': event.orbe,
        'es_aplicativo': event.es_aplicativo,
        'signo': event.signo,
        'grado': event.grado,
        'casa_natal': event.casa_natal
    }

# Función para deserializar un diccionario a un objeto AstroEvent
def dict_to_event(data):
    event = AstroEvent(
        fecha_utc=datetime.fromisoformat(data['fecha_utc']),
        tipo_evento=data['tipo_evento'],
        descripcion=data['descripcion']
    )
    event.planeta1 = data['planeta1']
    event.planeta2 = data['planeta2']
    event.longitud1 = data['longitud1']
    event.longitud2 = data['longitud2']
    event.tipo_aspecto = data['tipo_aspecto']
    event.orbe = data['orbe']
    event.es_aplicativo = data['es_aplicativo']
    event.signo = data['signo']
    event.grado = data['grado']
    event.casa_natal = data['casa_natal']
    return event

def main():
    # Datos natales de ejemplo (simplificados para la prueba)
    natal_data = {
        "points": {
            "Sun": {"longitude": 0, "sign": "Aries", "position": "0°00'00\""},
            "Moon": {"longitude": 90, "sign": "Cancer", "position": "0°00'00\""},
            "Mercury": {"longitude": 45, "sign": "Taurus", "position": "15°00'00\""},
            "Venus": {"longitude": 135, "sign": "Leo", "position": "15°00'00\""},
            "Mars": {"longitude": 180, "sign": "Libra", "position": "0°00'00\""},
            "Jupiter": {"longitude": 225, "sign": "Scorpio", "position": "15°00'00\""},
            "Saturn": {"longitude": 270, "sign": "Capricorn", "position": "0°00'00\""},
            "Uranus": {"longitude": 315, "sign": "Aquarius", "position": "15°00'00\""},
            "Neptune": {"longitude": 30, "sign": "Taurus", "position": "0°00'00\""},
            "Pluto": {"longitude": 60, "sign": "Gemini", "position": "0°00'00\""}
        }
    }

    # Período de prueba (un mes)
    start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end_date = datetime(2025, 1, 31, tzinfo=ZoneInfo("UTC"))

    print("=" * 60)
    print("PRUEBA DE COMPARACIÓN DE CALCULADORES DE TRÁNSITOS")
    print("=" * 60)
    print(f"Período de prueba: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print("-" * 60)

    # Archivo para guardar los resultados del método estándar
    cache_file = 'standard_results_cache.pkl'
    
    # Verificar si existen resultados guardados del método estándar
    if os.path.exists(cache_file):
        print("\nCargando resultados del método estándar desde caché...")
        with open(cache_file, 'rb') as f:
            standard_results = pickle.load(f)
            standard_time = 0  # No se midió el tiempo ya que se cargó desde caché
        print(f"Método estándar (desde caché): {len(standard_results)} eventos")
    else:
        # Calcular con método estándar
        print("\nCalculando con método estándar (primera ejecución)...")
        start_time = time.time()
        standard_calc = AllTransitsCalculator(natal_data)
        standard_results = standard_calc.calculate_all(start_date, end_date)
        standard_time = time.time() - start_time
        print(f"Método estándar: {len(standard_results)} eventos en {standard_time:.2f} segundos")
        
        # Guardar resultados para futuras ejecuciones
        print("Guardando resultados del método estándar en caché...")
        with open(cache_file, 'wb') as f:
            pickle.dump(standard_results, f)

    # Calcular con método adaptativo
    print("\nCalculando con método adaptativo...")
    start_time = time.time()
    adaptive_calc = AdaptiveTransitsCalculator(natal_data)
    adaptive_results = adaptive_calc.calculate_all(start_date, end_date)
    adaptive_time = time.time() - start_time
    print(f"Método adaptativo: {len(adaptive_results)} eventos en {adaptive_time:.2f} segundos")

    # Comparar resultados
    print("\n" + "=" * 60)
    print("RESULTADOS DE LA COMPARACIÓN")
    print("=" * 60)
    if standard_time > 0:
        print(f"Aceleración: {standard_time/adaptive_time:.2f}x más rápido")
    else:
        print("Aceleración: No calculada (usando caché)")
    print(f"Eventos encontrados (estándar): {len(standard_results)}")
    print(f"Eventos encontrados (adaptativo): {len(adaptive_results)}")
    print(f"Diferencia en número de eventos: {abs(len(standard_results) - len(adaptive_results))}")

    # Mostrar todos los eventos encontrados por ambos métodos
    print("\nEventos encontrados por el método estándar:")
    for i, event in enumerate(standard_results):
        print(f"  {i+1}. {event.fecha_utc} - {event.descripcion} (Orbe: {event.orbe})")
        
    print("\nEventos encontrados por el método adaptativo:")
    for i, event in enumerate(adaptive_results):
        print(f"  {i+1}. {event.fecha_utc} - {event.descripcion} (Orbe: {event.orbe})")
    
    # Verificar eventos que están en el estándar pero no en el adaptativo
    standard_descriptions = {f"{e.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{e.descripcion}" for e in standard_results}
    adaptive_descriptions = {f"{e.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{e.descripcion}" for e in adaptive_results}
    
    missing_events = standard_descriptions - adaptive_descriptions
    if missing_events:
        print("\nEventos presentes en el método estándar pero ausentes en el adaptativo:")
        for i, event_desc in enumerate(sorted(missing_events)):
            print(f"  {i+1}. {event_desc}")
    
    extra_events = adaptive_descriptions - standard_descriptions
    if extra_events:
        print("\nEventos presentes en el método adaptativo pero ausentes en el estándar:")
        for i, event_desc in enumerate(sorted(extra_events)):
            print(f"  {i+1}. {event_desc}")

    print("\n" + "=" * 60)
    print("CONCLUSIÓN")
    print("=" * 60)
    if len(standard_results) == len(adaptive_results) and not missing_events and not extra_events:
        print("✅ Ambos métodos encontraron exactamente los mismos eventos.")
    elif len(standard_results) == len(adaptive_results):
        print("⚠️ Ambos métodos encontraron el mismo número de eventos, pero hay diferencias en los eventos específicos.")
    else:
        print(f"⚠️ Hay una diferencia de {abs(len(standard_results) - len(adaptive_results))} eventos entre los métodos.")
    
    if standard_time > 0 and standard_time > adaptive_time:
        print(f"✅ El método adaptativo es {standard_time/adaptive_time:.2f}x más rápido que el método estándar.")
    elif standard_time > 0:
        print(f"⚠️ El método estándar es {adaptive_time/standard_time:.2f}x más rápido que el método adaptativo.")
    else:
        print("ℹ️ No se calculó la aceleración (usando caché para el método estándar).")

    print("\nNota: Para una prueba más completa, ejecute el programa principal con un período más largo.")

if __name__ == "__main__":
    main()
