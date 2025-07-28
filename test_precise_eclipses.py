"""
Script para probar y comparar los calculadores de eclipses.
Compara los resultados del calculador original con el calculador de alta precisión.
"""
from datetime import datetime
import pytz
import time
from src.core.location import Location
from src.calculators.eclipse_calculator_factory import EclipseCalculatorFactory

def main():
    # Configurar ubicación (Buenos Aires por defecto)
    location = Location(
        lat=-34.60,
        lon=-58.45,
        name="Buenos_Aires",
        timezone="America/Argentina/Buenos_Aires",
        elevation=25
    )
    observer = location.create_ephem_observer()
    
    # Crear calculadores
    original_calculator = EclipseCalculatorFactory.create_calculator(observer, use_precise=False)
    precise_calculator = EclipseCalculatorFactory.create_calculator(observer, use_precise=True)
    precise_calculator_all = EclipseCalculatorFactory.create_calculator(observer, use_precise=True)
    
    # Configurar período de prueba (años 2025-2026)
    start_date = datetime(2025, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(2027, 1, 1, tzinfo=pytz.UTC)
    
    # Calcular eclipses con los calculadores
    print("\nCalculando eclipses con el calculador original...")
    start_time = time.time()
    original_eclipses = original_calculator.calculate_eclipses(start_date, end_date)
    original_time = time.time() - start_time
    print(f"Completado en {original_time:.2f} segundos")
    
    print("\nCalculando eclipses con el calculador de alta precisión (solo visibles)...")
    start_time = time.time()
    precise_eclipses = precise_calculator.calculate_eclipses(start_date, end_date, only_visible_solar=True)
    precise_time = time.time() - start_time
    print(f"Completado en {precise_time:.2f} segundos")
    
    print("\nCalculando eclipses con el calculador de alta precisión (todos)...")
    start_time = time.time()
    precise_all_eclipses = precise_calculator_all.calculate_eclipses(start_date, end_date, only_visible_solar=False)
    precise_all_time = time.time() - start_time
    print(f"Completado en {precise_all_time:.2f} segundos")
    
    # Mostrar resultados
    print("\n=== Eclipses calculados con el método original ===")
    for event in original_eclipses:
        print(f"{event.fecha_utc.strftime('%Y-%m-%d %H:%M')} UTC: {event.descripcion}")
    
    print("\n=== Eclipses calculados con el método de alta precisión (solo visibles) ===")
    for event in precise_eclipses:
        print(f"{event.fecha_utc.strftime('%Y-%m-%d %H:%M')} UTC: {event.descripcion}")
        
    print("\n=== Eclipses calculados con el método de alta precisión (todos) ===")
    for event in precise_all_eclipses:
        visibilidad = f" [{event.visibilidad_local}]" if event.visibilidad_local else ""
        print(f"{event.fecha_utc.strftime('%Y-%m-%d %H:%M')} UTC: {event.descripcion}{visibilidad}")
    
    # Comparar resultados
    print("\n=== Comparación de resultados ===")
    print(f"Eclipses encontrados (original): {len(original_eclipses)}")
    print(f"Eclipses encontrados (preciso, solo visibles): {len(precise_eclipses)}")
    print(f"Eclipses encontrados (preciso, todos): {len(precise_all_eclipses)}")
    
    # Comparar tiempos
    print(f"\nTiempo de cálculo (original): {original_time:.2f} segundos")
    print(f"Tiempo de cálculo (preciso, solo visibles): {precise_time:.2f} segundos")
    print(f"Tiempo de cálculo (preciso, todos): {precise_all_time:.2f} segundos")
    
    # Comparar fechas y tipos
    print("\n=== Comparación detallada ===")
    
    # Organizar eclipses por tipo y fecha
    original_dict = {(e.tipo_evento.value, e.fecha_utc.strftime('%Y-%m-%d')): e for e in original_eclipses}
    precise_dict = {(e.tipo_evento.value, e.fecha_utc.strftime('%Y-%m-%d')): e for e in precise_eclipses}
    precise_all_dict = {(e.tipo_evento.value, e.fecha_utc.strftime('%Y-%m-%d')): e for e in precise_all_eclipses}
    
    # Encontrar eclipses en ambos conjuntos
    common_keys_orig_prec = set(original_dict.keys()) & set(precise_dict.keys())
    common_keys_orig_all = set(original_dict.keys()) & set(precise_all_dict.keys())
    only_original = set(original_dict.keys()) - set(precise_all_dict.keys())
    only_precise_all = set(precise_all_dict.keys()) - set(original_dict.keys())
    
    print(f"Eclipses encontrados por original y preciso (solo visibles): {len(common_keys_orig_prec)}")
    print(f"Eclipses encontrados por original y preciso (todos): {len(common_keys_orig_all)}")
    print(f"Eclipses encontrados solo por el método original: {len(only_original)}")
    print(f"Eclipses encontrados solo por el método preciso (todos): {len(only_precise_all)}")
    
    # Comparar diferencias de tiempo para eclipses comunes
    print("\n=== Diferencias de tiempo para eclipses comunes (original vs. preciso todos) ===")
    for key in common_keys_orig_all:
        orig = original_dict[key]
        prec = precise_all_dict[key]
        
        # Calcular diferencia en minutos
        diff_seconds = abs((orig.fecha_utc - prec.fecha_utc).total_seconds())
        diff_minutes = diff_seconds / 60
        
        visibilidad = f" [{prec.visibilidad_local}]" if prec.visibilidad_local else ""
        
        print(f"{key[0]} ({key[1]}): {diff_minutes:.2f} minutos de diferencia")
        print(f"  Original: {orig.fecha_utc.strftime('%Y-%m-%d %H:%M:%S')} - {orig.descripcion}")
        print(f"  Preciso:  {prec.fecha_utc.strftime('%Y-%m-%d %H:%M:%S')} - {prec.descripcion}{visibilidad}")
        print()

if __name__ == "__main__":
    main()
