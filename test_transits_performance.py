"""
Script para comparar el rendimiento y los resultados del calculador de tránsitos optimizado
con el calculador paralelo, que sabemos funciona correctamente.
"""
import json
import time
from datetime import datetime
import pytz
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory

def compare_events(parallel_events, optimized_events):
    """
    Compara los eventos generados por ambos calculadores.
    
    Args:
        parallel_events: Lista de eventos del calculador paralelo
        optimized_events: Lista de eventos del calculador optimizado
        
    Returns:
        Diccionario con resultados de la comparación
    """
    # Ordenar eventos por fecha
    parallel_events = sorted(parallel_events, key=lambda x: x.fecha_utc)
    optimized_events = sorted(optimized_events, key=lambda x: x.fecha_utc)
    
    # Verificar cantidad de eventos
    if len(parallel_events) != len(optimized_events):
        print(f"\nDiferencia en cantidad de eventos: Paralelo={len(parallel_events)}, Optimizado={len(optimized_events)}")
    
    # Comparar eventos uno a uno
    matches = 0
    differences = []
    
    # Crear diccionario para eventos paralelos para búsqueda más eficiente
    parallel_dict = {}
    for event in parallel_events:
        key = f"{event.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{event.planeta1}-{event.planeta2}-{event.tipo_aspecto}"
        parallel_dict[key] = event
    
    # Verificar cada evento optimizado
    for opt_event in optimized_events:
        key = f"{opt_event.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{opt_event.planeta1}-{opt_event.planeta2}-{opt_event.tipo_aspecto}"
        
        if key in parallel_dict:
            # Evento encontrado, verificar detalles
            par_event = parallel_dict[key]
            
            # Verificar orbe con tolerancia de 0.001 grados
            orb_diff = abs(opt_event.orbe - par_event.orbe)
            if orb_diff > 0.001:
                differences.append({
                    'tipo': 'orbe',
                    'evento': key,
                    'paralelo': par_event.orbe,
                    'optimizado': opt_event.orbe,
                    'diferencia': orb_diff
                })
            else:
                matches += 1
        else:
            # Evento no encontrado
            differences.append({
                'tipo': 'evento_faltante',
                'evento': key,
                'optimizado': True,
                'paralelo': False
            })
    
    # Verificar eventos en paralelo que no están en optimizado
    for par_event in parallel_events:
        key = f"{par_event.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{par_event.planeta1}-{par_event.planeta2}-{par_event.tipo_aspecto}"
        
        # Buscar en optimizado
        found = False
        for opt_event in optimized_events:
            opt_key = f"{opt_event.fecha_utc.strftime('%Y-%m-%d %H:%M')}-{opt_event.planeta1}-{opt_event.planeta2}-{opt_event.tipo_aspecto}"
            if opt_key == key:
                found = True
                break
        
        if not found:
            differences.append({
                'tipo': 'evento_faltante',
                'evento': key,
                'optimizado': False,
                'paralelo': True
            })
    
    return {
        'total_parallel': len(parallel_events),
        'total_optimized': len(optimized_events),
        'matches': matches,
        'differences': differences
    }

def main():
    # Cargar datos natales (usando los mismos datos de ejemplo)
    try:
        print("Buscando archivo de carta natal...")
        with open("output/natal_charts/test_user.json", "r", encoding='utf-8') as f:
            natal_data = json.load(f)
            print(f"Carta natal cargada para: {natal_data.get('name', 'Usuario desconocido')}")
    except FileNotFoundError:
        print("No se encontró un archivo de carta natal. Usando datos de ejemplo.")
        natal_data = {
            "name": "Test User",
            "points": {
                "Sun": {"longitude": 90.5, "sign": "Cancer", "position": "0°30'00\""},
                "Moon": {"longitude": 120.75, "sign": "Leo", "position": "0°45'00\""},
                "Mercury": {"longitude": 85.25, "sign": "Gemini", "position": "25°15'00\""},
                "Venus": {"longitude": 45.5, "sign": "Taurus", "position": "15°30'00\""},
                "Mars": {"longitude": 160.25, "sign": "Virgo", "position": "10°15'00\""},
                "Jupiter": {"longitude": 210.5, "sign": "Libra", "position": "0°30'00\""},
                "Saturn": {"longitude": 270.75, "sign": "Capricorn", "position": "0°45'00\""},
                "Uranus": {"longitude": 315.25, "sign": "Aquarius", "position": "15°15'00\""},
                "Neptune": {"longitude": 345.5, "sign": "Pisces", "position": "15°30'00\""},
                "Pluto": {"longitude": 30.25, "sign": "Aries", "position": "0°15'00\""}
            }
        }
    
    # Definir período (un mes para pruebas)
    print("\nDefiniendo período de prueba...")
    start_date = datetime(2025, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(2025, 1, 31, tzinfo=pytz.UTC)
    print(f"Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # Probar calculador paralelo
    print("\n" + "="*80)
    print("CALCULADOR PARALELO")
    print("="*80)
    start_time = time.time()
    parallel_calculator = TransitsCalculatorFactory.create_calculator(natal_data, "standard", use_parallel=True)
    parallel_events = parallel_calculator.calculate_all(start_date, end_date)
    parallel_time = time.time() - start_time
    print(f"Completado en {parallel_time:.2f} segundos")
    print(f"Eventos encontrados: {len(parallel_events)}")
    
    # Probar calculador optimizado
    print("\n" + "="*80)
    print("CALCULADOR OPTIMIZADO")
    print("="*80)
    start_time = time.time()
    optimized_calculator = TransitsCalculatorFactory.create_calculator(natal_data, "standard", use_optimized=True)
    optimized_events = optimized_calculator.calculate_all(start_date, end_date)
    optimized_time = time.time() - start_time
    print(f"Completado en {optimized_time:.2f} segundos")
    print(f"Eventos encontrados: {len(optimized_events)}")
    
    # Mostrar métricas detalladas del calculador optimizado
    if hasattr(optimized_calculator, 'metrics'):
        print("\nMétricas del calculador optimizado:")
        
        # Obtener resumen de métricas
        metrics_summary = optimized_calculator.metrics.get_summary()
        segment_stats = optimized_calculator.metrics.get_segment_stats()
        
        total_calcs = metrics_summary['total_calculations']
        cache_hits = metrics_summary['cache_hits']
        total_ops = total_calcs + cache_hits
        
        print(f"- Cálculos de efemérides: {total_calcs}")
        print(f"- Aciertos de caché: {cache_hits}")
        if total_ops > 0:
            print(f"- Tasa de aciertos de caché: {cache_hits / total_ops * 100:.1f}%")
        print(f"- Pasos saltados: {metrics_summary['steps_skipped']}")
        print(f"- Aspectos encontrados: {metrics_summary['aspects_found']}")
        
        # Análisis de eficiencia
        print("\nAnálisis de eficiencia:")
        if metrics_summary['steps_skipped'] > 0:
            print(f"- Pasos evitados gracias a la predicción: {metrics_summary['steps_skipped']:,}")
            print(f"- Tiempo estimado ahorrado: ~{metrics_summary['steps_skipped'] / 60:.1f} minutos de cálculo")
        
        # Mostrar estadísticas de segmentos si hay datos
        if segment_stats:
            print("\nEstadísticas de segmentos:")
            print(f"- Tiempo promedio por segmento: {segment_stats['avg_time']:.2f}s")
            print(f"- Tiempo mínimo: {segment_stats['min_time']:.2f}s")
            print(f"- Tiempo máximo: {segment_stats['max_time']:.2f}s")
            print(f"- Eventos promedio por segmento: {segment_stats['avg_events']:.1f}")
    
    # Mostrar comparación con tiempos de referencia
    print("\n" + "="*80)
    print("COMPARACIÓN DE RENDIMIENTO")
    print("="*80)
    print(f"Paralelo:    {parallel_time:.2f}s")
    print(f"Optimizado:  {optimized_time:.2f}s ({parallel_time/optimized_time:.1f}x más rápido que paralelo)")
    
    # Comparar resultados
    print("\n" + "="*80)
    print("COMPARACIÓN DE RESULTADOS")
    print("="*80)
    
    comparison = compare_events(parallel_events, optimized_events)
    
    print(f"Total eventos paralelo:  {comparison['total_parallel']}")
    print(f"Total eventos optimizado: {comparison['total_optimized']}")
    print(f"Eventos idénticos: {comparison['matches']}")
    
    if len(comparison['differences']) > 0:
        print(f"\nDiferencias encontradas: {len(comparison['differences'])}")
        
        # Agrupar diferencias por tipo
        by_type = {}
        for diff in comparison['differences']:
            diff_type = diff['tipo']
            if diff_type not in by_type:
                by_type[diff_type] = []
            by_type[diff_type].append(diff)
        
        # Mostrar resumen por tipo
        for diff_type, diffs in by_type.items():
            print(f"\n- Tipo: {diff_type} ({len(diffs)} diferencias)")
            
            # Mostrar hasta 5 ejemplos de cada tipo
            for i, diff in enumerate(diffs[:5]):
                if diff_type == 'orbe':
                    print(f"  {i+1}. Evento: {diff['evento']}")
                    print(f"     Orbe paralelo: {diff['paralelo']:.6f}°")
                    print(f"     Orbe optimizado: {diff['optimizado']:.6f}°")
                    print(f"     Diferencia: {diff['diferencia']:.6f}°")
                elif diff_type == 'evento_faltante':
                    if diff['optimizado'] and not diff['paralelo']:
                        print(f"  {i+1}. Evento solo en optimizado: {diff['evento']}")
                    else:
                        print(f"  {i+1}. Evento solo en paralelo: {diff['evento']}")
    else:
        print("\n¡Los resultados son idénticos! El calculador optimizado produce exactamente los mismos eventos que el paralelo.")

if __name__ == "__main__":
    main()
