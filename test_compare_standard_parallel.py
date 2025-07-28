"""
Script para comparar directamente el rendimiento entre los calculadores estándar y paralelo.
"""
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.calculators.all_transits import AllTransitsCalculator
from src.calculators.all_transits_parallel import ParallelTransitsCalculator

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

    # Período de prueba (un mes para que la prueba no tarde demasiado)
    start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end_date = datetime(2025, 1, 31, tzinfo=ZoneInfo("UTC"))

    print("=" * 60)
    print("COMPARACIÓN DIRECTA DE CALCULADORES DE TRÁNSITOS")
    print("=" * 60)
    print(f"Período de prueba: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print(f"Duración: {(end_date - start_date).days} días")
    print("-" * 60)

    # Calcular con método estándar
    print("\nCalculando con método estándar...")
    start_time = time.time()
    standard_calc = AllTransitsCalculator(natal_data)
    standard_results = standard_calc.calculate_all(start_date, end_date)
    standard_time = time.time() - start_time
    print(f"Método estándar: {len(standard_results)} eventos en {standard_time:.2f} segundos")
    print(f"Rendimiento estándar: {(end_date - start_date).days / standard_time:.2f} días/segundo")

    # Calcular con método paralelo
    print("\nCalculando con método paralelo...")
    start_time = time.time()
    parallel_calc = ParallelTransitsCalculator(natal_data)
    parallel_results = parallel_calc.calculate_all(start_date, end_date)
    parallel_time = time.time() - start_time
    print(f"Método paralelo: {len(parallel_results)} eventos en {parallel_time:.2f} segundos")
    print(f"Rendimiento paralelo: {(end_date - start_date).days / parallel_time:.2f} días/segundo")

    # Comparar resultados
    print("\n" + "=" * 60)
    print("RESULTADOS DE LA COMPARACIÓN")
    print("=" * 60)
    print(f"Aceleración: {standard_time/parallel_time:.2f}x más rápido")
    print(f"Eventos encontrados (estándar): {len(standard_results)}")
    print(f"Eventos encontrados (paralelo): {len(parallel_results)}")
    print(f"Diferencia en número de eventos: {abs(len(standard_results) - len(parallel_results))}")

    # Verificar eventos que están en el estándar pero no en el paralelo
    standard_descriptions = {f"{e.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{e.descripcion}" for e in standard_results}
    parallel_descriptions = {f"{e.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{e.descripcion}" for e in parallel_results}
    
    missing_events = standard_descriptions - parallel_descriptions
    if missing_events:
        print("\nEventos presentes en el método estándar pero ausentes en el paralelo:")
        for i, event_desc in enumerate(sorted(missing_events)):
            print(f"  {i+1}. {event_desc}")
    
    extra_events = parallel_descriptions - standard_descriptions
    if extra_events:
        print("\nEventos presentes en el método paralelo pero ausentes en el estándar:")
        for i, event_desc in enumerate(sorted(extra_events)):
            print(f"  {i+1}. {event_desc}")

    print("\n" + "=" * 60)
    print("CONCLUSIÓN")
    print("=" * 60)
    if len(standard_results) == len(parallel_results) and not missing_events and not extra_events:
        print("✅ Ambos métodos encontraron exactamente los mismos eventos.")
    elif len(standard_results) == len(parallel_results):
        print("⚠️ Ambos métodos encontraron el mismo número de eventos, pero hay diferencias en los eventos específicos.")
    else:
        print(f"⚠️ Hay una diferencia de {abs(len(standard_results) - len(parallel_results))} eventos entre los métodos.")
    
    print(f"✅ El método paralelo es {standard_time/parallel_time:.2f}x más rápido que el método estándar.")
    
    # Proyección para un año completo
    days_in_year = 365
    projected_standard_time = (days_in_year * standard_time) / (end_date - start_date).days
    projected_parallel_time = (days_in_year * parallel_time) / (end_date - start_date).days
    
    print("\nProyección para un año completo:")
    print(f"Método estándar: {projected_standard_time/60:.1f} minutos ({projected_standard_time/3600:.1f} horas)")
    print(f"Método paralelo: {projected_parallel_time/60:.1f} minutos ({projected_parallel_time/3600:.1f} horas)")
    print(f"Tiempo ahorrado: {(projected_standard_time - projected_parallel_time)/60:.1f} minutos")

if __name__ == "__main__":
    main()
