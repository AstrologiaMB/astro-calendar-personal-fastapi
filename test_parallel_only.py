"""
Script para probar el rendimiento del calculador de tránsitos paralelo.
"""
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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

    # Período de prueba (tres meses)
    start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))
    end_date = datetime(2025, 3, 31, tzinfo=ZoneInfo("UTC"))

    print("=" * 60)
    print("PRUEBA DE RENDIMIENTO DEL CALCULADOR DE TRÁNSITOS PARALELO")
    print("=" * 60)
    print(f"Período de prueba: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print(f"Duración: {(end_date - start_date).days} días")
    print("-" * 60)

    # Calcular con método paralelo
    print("\nIniciando cálculo con método paralelo...")
    start_time = time.time()
    
    # Crear calculador y ejecutar
    parallel_calc = ParallelTransitsCalculator(natal_data)
    parallel_results = parallel_calc.calculate_all(start_date, end_date)
    
    # Medir tiempo total
    total_time = time.time() - start_time
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    print(f"Tiempo total de cálculo: {total_time:.2f} segundos")
    print(f"Eventos encontrados: {len(parallel_results)}")
    print(f"Rendimiento: {(end_date - start_date).days / total_time:.2f} días procesados por segundo")
    
    # Mostrar algunos eventos de ejemplo
    print("\nPrimeros 5 eventos encontrados:")
    for i, event in enumerate(parallel_results[:5]):
        print(f"  {i+1}. {event.fecha_utc} - {event.descripcion} (Orbe: {event.orbe})")
    
    print("\nÚltimos 5 eventos encontrados:")
    for i, event in enumerate(parallel_results[-5:]):
        print(f"  {i+1}. {event.fecha_utc} - {event.descripcion} (Orbe: {event.orbe})")

if __name__ == "__main__":
    main()
