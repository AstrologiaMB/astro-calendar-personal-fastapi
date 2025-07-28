"""
Script para comparar los resultados de los tres calculadores de eclipses.
"""
from datetime import datetime
import pytz
from src.core.location import Location
from src.calculators.eclipse_calculator_factory import EclipseCalculatorFactory

def main():
    # Crear un observador
    observer = Location(
        lat=-34.60,
        lon=-58.45,
        name="Buenos_Aires",
        timezone="America/Argentina/Buenos_Aires",
        elevation=25
    ).create_ephem_observer()
    
    # Definir período
    start_date = datetime(2025, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(2026, 1, 1, tzinfo=pytz.UTC)
    
    # Crear calculadores
    standard_calculator = EclipseCalculatorFactory.create_calculator(observer)
    precise_calculator = EclipseCalculatorFactory.create_calculator(observer, use_precise=True)
    immanuel_calculator = EclipseCalculatorFactory.create_calculator(observer, use_immanuel=True)
    
    # Calcular eclipses
    print("Calculando eclipses con el calculador estándar...")
    standard_eclipses = standard_calculator.calculate_eclipses(start_date, end_date)
    
    print("\nCalculando eclipses con el calculador de alta precisión...")
    precise_eclipses = precise_calculator.calculate_eclipses(start_date, end_date)
    
    print("\nCalculando eclipses con el calculador basado en Immanuel...")
    immanuel_eclipses = immanuel_calculator.calculate_eclipses(start_date, end_date)
    
    # Mostrar resultados
    print("\n" + "="*80)
    print("COMPARACIÓN DE CALCULADORES DE ECLIPSES PARA 2025")
    print("="*80)
    
    print("\nEclipses calculados con el calculador estándar:")
    print("-"*80)
    for eclipse in standard_eclipses:
        print(f"{eclipse.fecha_utc.strftime('%Y-%m-%d %H:%M')} - {eclipse.descripcion}")
    
    print("\nEclipses calculados con el calculador de alta precisión:")
    print("-"*80)
    for eclipse in precise_eclipses:
        print(f"{eclipse.fecha_utc.strftime('%Y-%m-%d %H:%M')} - {eclipse.descripcion}")
    
    print("\nEclipses calculados con el calculador basado en Immanuel:")
    print("-"*80)
    for eclipse in immanuel_eclipses:
        print(f"{eclipse.fecha_utc.strftime('%Y-%m-%d %H:%M')} - {eclipse.descripcion}")
    
    # Comparar cantidad de eclipses encontrados
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"Calculador estándar:      {len(standard_eclipses)} eclipses")
    print(f"Calculador alta precisión: {len(precise_eclipses)} eclipses")
    print(f"Calculador Immanuel:      {len(immanuel_eclipses)} eclipses")

if __name__ == "__main__":
    main()
