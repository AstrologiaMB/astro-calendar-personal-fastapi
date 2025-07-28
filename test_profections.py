"""
Script de prueba para el calculador de profecciones anuales.
"""
import json
import os
from datetime import datetime
import pytz
from src.calculators.profections_calculator import ProfectionsCalculator

def main():
    # Cargar datos natales de prueba
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
    natal_data['date'] = "1964-12-26T21:12:00-03:00"
    print(f"Usando fecha de nacimiento: 26/12/1964 21:12 Buenos Aires, Argentina")
    
    # Asegurarse de que el ascendente sea Cáncer (para coincidir con AstroSeek)
    if 'points' in natal_data and 'Asc' in natal_data['points']:
        natal_data['points']['Asc']['sign'] = "Cáncer"
        print(f"Estableciendo Ascendente en: Cáncer")
    
    # Crear calculador de profecciones
    calculator = ProfectionsCalculator(natal_data)
    
    # Mostrar profecciones detalladas para algunas fechas clave
    dates_to_check = [
        datetime(2025, 1, 1, tzinfo=pytz.UTC),  # AstroSeek: Señor del año = Luna
        datetime(2025, 12, 27, tzinfo=pytz.UTC),  # Día después del cumpleaños 61
        datetime(2026, 1, 1, tzinfo=pytz.UTC),
    ]
    
    print("\nProfecciones Anuales (Detalle):")
    print("=" * 70)
    
    for date in dates_to_check:
        print(f"\nFecha de consulta: {date.strftime('%Y-%m-%d')}")
        calculator.display_profection_info(date)
    
    # Verificar profecciones para el período 2025-2035
    print("\nProfecciones Anuales 2025-2035:")
    print("=" * 90)
    print(f"{'Edad':<5} | {'Fecha Inicio':<12} | {'Casa Profectada':<20} | {'Señor del Año':<12} | {'Próximo Señor':<12}")
    print("-" * 90)

    # Usar fechas de cumpleaños para cada año
    for year in range(2024, 2036):
        # Fecha del cumpleaños en ese año
        birthday = datetime(year, 12, 26, tzinfo=pytz.UTC)
        
        # Calcular profección
        profection_data = calculator.calcular_senor_del_anio(birthday)
        
        # Imprimir resultados en formato tabular
        print(f"{profection_data['edad_actual']:<5} | {profection_data['fecha_inicio']:<12} | {profection_data['casa_profectada_actual']:<20} | {profection_data['senor_del_anio_actual']:<12} | {profection_data['proximo_senor_del_anio']:<12}")

    print("=" * 90)

if __name__ == "__main__":
    main()
