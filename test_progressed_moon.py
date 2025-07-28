"""
Script de prueba para el calculador de conjunciones de Luna progresada.
"""
import json
import os
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
    
    # Añadir fecha de nacimiento específica (26/12/1964 21:12 Buenos Aires)
    # Esta fecha se usará para calcular la Luna progresada
    natal_data['date'] = "1964-12-26T21:12:00-03:00"
    print(f"Usando fecha de nacimiento: 26/12/1964 21:12 Buenos Aires, Argentina")
    
    # Definir período de prueba (un año)
    year = 2025
    start_date = datetime(year, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(year, 12, 31, 23, 59, tzinfo=pytz.UTC)
    
    # Crear calculador de Luna progresada
    calculator = TransitsCalculatorFactory.create_calculator(
        natal_data,
        calculator_type="progressed_moon"
    )
    
    # Calcular conjunciones
    print(f"\nCalculando conjunciones de Luna progresada para {year}...")
    events = calculator.calculate_all(start_date, end_date)
    
    # Mostrar resultados
    print(f"\nSe encontraron {len(events)} conjunciones de Luna progresada:")
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event.descripcion}")
        print(f"   Fecha: {event.fecha_utc.strftime('%Y-%m-%d')}")
        print(f"   Orbe: {event.orbe:.2f}°")
        if hasattr(event, 'metadata') and event.metadata:
            print(f"   Estado: {event.metadata.get('estado', 'N/A')}")

if __name__ == "__main__":
    main()
