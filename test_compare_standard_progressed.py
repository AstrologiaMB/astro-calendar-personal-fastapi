"""
Script de prueba para comparar el calculador de tránsitos estándar con el calculador de Luna progresada.
"""
import json
import os
import time
from datetime import datetime
import pytz
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory

def main():
    # Cargar datos natales de prueba
    # Buscar un archivo de carta natal en el directorio de salida
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    
    # Buscar archivos de carta natal
    natal_files = [f for f in os.listdir(output_dir) if f.startswith("carta_natal_") and f.endswith(".json")]
    
    if not natal_files:
        print("No se encontraron archivos de carta natal. Por favor ejecute main.py primero.")
        return
    
    # Usar el primer archivo encontrado
    natal_file = os.path.join(output_dir, natal_files[0])
    print(f"Usando carta natal: {natal_file}")
    
    with open(natal_file, "r", encoding="utf-8") as f:
        natal_data = json.load(f)
    
    # Definir período de prueba (un año)
    year = 2025
    start_date = datetime(year, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(year, 12, 31, 23, 59, tzinfo=pytz.UTC)
    
    # Prueba 1: Calculador de tránsitos estándar
    print("\n=== Prueba 1: Calculador de tránsitos estándar ===")
    start_time = time.time()
    standard_calculator = TransitsCalculatorFactory.create_calculator(
        natal_data,
        calculator_type="standard",
        use_parallel=False
    )
    standard_events = standard_calculator.calculate_all(start_date, end_date)
    standard_time = time.time() - start_time
    print(f"Tiempo de cálculo: {standard_time:.2f} segundos")
    print(f"Total de eventos encontrados: {len(standard_events)}")
    
    # Prueba 2: Calculador de tránsitos paralelo
    print("\n=== Prueba 2: Calculador de tránsitos paralelo ===")
    start_time = time.time()
    parallel_calculator = TransitsCalculatorFactory.create_calculator(
        natal_data,
        calculator_type="standard",
        use_parallel=True
    )
    parallel_events = parallel_calculator.calculate_all(start_date, end_date)
    parallel_time = time.time() - start_time
    print(f"Tiempo de cálculo: {parallel_time:.2f} segundos")
    print(f"Total de eventos encontrados: {len(parallel_events)}")
    print(f"Aceleración: {standard_time / parallel_time:.2f}x")
    
    # Prueba 3: Calculador de Luna progresada
    print("\n=== Prueba 3: Calculador de Luna progresada ===")
    start_time = time.time()
    progressed_calculator = TransitsCalculatorFactory.create_calculator(
        natal_data,
        calculator_type="progressed_moon"
    )
    progressed_events = progressed_calculator.calculate_all(start_date, end_date)
    progressed_time = time.time() - start_time
    print(f"Tiempo de cálculo: {progressed_time:.2f} segundos")
    print(f"Total de conjunciones encontradas: {len(progressed_events)}")
    
    # Mostrar algunos ejemplos de eventos de Luna progresada
    if progressed_events:
        print("\nEjemplos de conjunciones de Luna progresada:")
        for i, event in enumerate(progressed_events[:5], 1):
            print(f"\n{i}. {event.descripcion}")
            print(f"   Fecha: {event.fecha_utc.strftime('%Y-%m-%d')}")
            print(f"   Orbe: {event.orbe:.2f}°")
            if hasattr(event, 'metadata') and event.metadata:
                print(f"   Estado: {event.metadata.get('estado', 'N/A')}")
        
        if len(progressed_events) > 5:
            print(f"\n... y {len(progressed_events) - 5} más.")
    
    # Comparar resultados
    print("\n=== Comparación de resultados ===")
    print(f"Eventos de tránsitos estándar: {len(standard_events)}")
    print(f"Eventos de tránsitos paralelo: {len(parallel_events)}")
    print(f"Conjunciones de Luna progresada: {len(progressed_events)}")
    
    # Verificar que los resultados de los calculadores estándar y paralelo sean iguales
    if len(standard_events) == len(parallel_events):
        print("\nLos calculadores estándar y paralelo produjeron la misma cantidad de eventos.")
    else:
        print("\n¡ADVERTENCIA! Los calculadores estándar y paralelo produjeron diferentes cantidades de eventos.")
    
    # Mostrar resumen de tiempos
    print("\n=== Resumen de tiempos ===")
    print(f"Calculador estándar: {standard_time:.2f} segundos")
    print(f"Calculador paralelo: {parallel_time:.2f} segundos")
    print(f"Calculador de Luna progresada: {progressed_time:.2f} segundos")
    print(f"Aceleración paralelo vs. estándar: {standard_time / parallel_time:.2f}x")

if __name__ == "__main__":
    main()
