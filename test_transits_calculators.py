"""
Script para comparar los resultados de los diferentes calculadores de tránsitos.
Compara el calculador paralelo (all_transits_parallel.py) con el optimizado (optimized_transits_calculator.py).
"""
import json
import time
import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.all_transits_parallel import ParallelTransitsCalculator
from src.calculators.optimized_transits_calculator import OptimizedTransitsCalculator
from src.core.constants import EventType

def load_natal_data(filename):
    """Carga datos natales desde un archivo JSON."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_event(event):
    """
    Formatea un evento para comparación.
    Usa solo la información esencial: planeta, aspecto y planeta natal.
    Ignora la descripción, fecha exacta y orbe para permitir comparaciones más flexibles.
    """
    return (
        event.fecha_utc.strftime('%Y-%m-%d'),  # Solo fecha, no hora
        event.planeta1,  # Planeta transitante
        event.planeta2,  # Planeta natal
        event.tipo_aspecto  # Tipo de aspecto
    )

def compare_with_astroseek(events, max_events=30):
    """
    Compara los eventos calculados con los datos de AstroSeek.
    
    Args:
        events: Lista de eventos calculados
        max_events: Número máximo de eventos a mostrar
    """
    # Datos de AstroSeek para enero 2025 (solo conjunciones, oposiciones y cuadraturas)
    astroseek_data = [
        ("2025-01-02 18:07", "Mercury", "square", "Mars"),
        ("2025-01-03 19:36", "Venus", "conjunction", "Saturn"),
        ("2025-01-04 17:54", "Saturn", "opposition", "Uranus"),
        ("2025-01-09 10:17", "Sun", "square", "Moon"),
        ("2025-01-11 23:16", "Mercury", "conjunction", "Sun"),
        ("2025-01-12 07:17", "Venus", "square", "Venus"),
        ("2025-01-17 14:39", "Venus", "opposition", "Uranus"),
        ("2025-01-19 04:03", "Venus", "opposition", "Pluto"),
        ("2025-01-21 04:40", "Saturn", "opposition", "Pluto"),
        ("2025-01-21 09:43", "Mercury", "square", "Moon"),
        ("2025-01-21 23:25", "Venus", "square", "Mercury"),
        ("2025-01-25 18:21", "Venus", "opposition", "Mars")
    ]
    
    # Convertir aspectos a formato español
    aspect_translation = {
        "conjunction": "Conjunción",
        "opposition": "Oposición",
        "square": "Cuadratura"
    }
    
    # Convertir planetas a español
    planet_translation = {
        "Sun": "Sol",
        "Moon": "Luna",
        "Mercury": "Mercurio",
        "Venus": "Venus",
        "Mars": "Marte",
        "Jupiter": "Júpiter",
        "Saturn": "Saturno",
        "Uranus": "Urano",
        "Neptune": "Neptuno",
        "Pluto": "Plutón"
    }
    
    # Filtrar solo eventos de aspecto
    aspect_events = [e for e in events if e.tipo_evento == EventType.ASPECTO]
    
    # Ordenar por fecha
    aspect_events.sort(key=lambda e: e.fecha_utc)
    
    print("\n=== Comparación con AstroSeek ===")
    print(f"Total de eventos calculados: {len(aspect_events)}")
    print(f"Total de eventos en AstroSeek (solo conjunciones, oposiciones y cuadraturas): {len(astroseek_data)}")
    
    # Crear diccionario para búsqueda rápida de eventos AstroSeek
    astroseek_dict = {}
    for date_str, planet1, aspect, planet2 in astroseek_data:
        key = (planet_translation.get(planet1, planet1), 
               planet_translation.get(planet2, planet2), 
               aspect_translation.get(aspect, aspect))
        astroseek_dict[key] = date_str
    
    # Encontrar coincidencias
    matches = []
    missing = []
    extra = []
    
    for event in aspect_events:
        key = (event.planeta1, event.planeta2, event.tipo_aspecto)
        if key in astroseek_dict:
            astroseek_time = astroseek_dict[key]
            event_time = event.fecha_utc.strftime('%Y-%m-%d %H:%M')
            matches.append((event, astroseek_time))
        else:
            extra.append(event)
    
    # Encontrar eventos de AstroSeek que faltan
    for date_str, planet1, aspect, planet2 in astroseek_data:
        key = (planet_translation.get(planet1, planet1), 
               planet_translation.get(planet2, planet2), 
               aspect_translation.get(aspect, aspect))
        found = False
        for event in aspect_events:
            if (event.planeta1, event.planeta2, event.tipo_aspecto) == key:
                found = True
                break
        if not found:
            missing.append((date_str, planet1, aspect, planet2))
    
    # Mostrar coincidencias
    print(f"\nCoincidencias encontradas: {len(matches)}")
    for event, astroseek_time in matches[:max_events]:
        event_time = event.fecha_utc.strftime('%Y-%m-%d %H:%M')
        print(f"- {event.planeta1} {event.tipo_aspecto} {event.planeta2}: Calculado: {event_time}, AstroSeek: {astroseek_time}")
        if 'posicion1' in event.metadata:
            print(f"  Posición: {event.metadata['posicion1']}, Orbe: {event.orbe:.2f}°")
    
    # Mostrar eventos que faltan
    print(f"\nEventos de AstroSeek no encontrados: {len(missing)}")
    for date_str, planet1, aspect, planet2 in missing[:max_events]:
        print(f"- {date_str}: {planet1} {aspect} {planet2}")
    
    # Mostrar eventos extra
    print(f"\nEventos adicionales calculados: {len(extra)}")
    for event in extra[:max_events]:
        event_time = event.fecha_utc.strftime('%Y-%m-%d %H:%M')
        print(f"- {event_time}: {event.planeta1} {event.tipo_aspecto} {event.planeta2}")
        if 'posicion1' in event.metadata:
            print(f"  Posición: {event.metadata['posicion1']}, Orbe: {event.orbe:.2f}°")

def display_month_events(events, month, year, filter_aspects=None, only_exact=True, exclude_angles=True):
    """
    Muestra los eventos de un mes específico en formato similar a AstroSeek.
    
    Args:
        events: Lista de eventos calculados
        month: Número del mes (1-12)
        year: Año
        filter_aspects: Lista opcional de aspectos a filtrar (ej. ["Conjunción", "Oposición", "Cuadratura"])
        only_exact: Si es True, solo muestra el evento más exacto para cada combinación planeta-aspecto-planeta
        exclude_angles: Si es True, excluye aspectos a puntos como MC, IC, ASC, DESC
    """
    # Filtrar eventos del mes especificado
    month_events = [e for e in events if e.fecha_utc.month == month and e.tipo_evento == EventType.ASPECTO]
    
    # Filtrar por aspectos si se especifica
    if filter_aspects:
        month_events = [e for e in month_events if e.tipo_aspecto in filter_aspects]
    
    # Excluir aspectos a ángulos si se solicita
    if exclude_angles:
        month_events = [e for e in month_events if e.planeta2 not in ['MC', 'IC', 'ASC', 'DESC']]
    
    # Si only_exact es True, filtrar para mostrar solo el evento más exacto para cada combinación
    if only_exact:
        # Crear un diccionario para agrupar eventos por combinación planeta-aspecto-planeta
        event_groups = {}
        for event in month_events:
            key = (event.planeta1, event.tipo_aspecto, event.planeta2)
            if key not in event_groups or event.orbe < event_groups[key].orbe:
                event_groups[key] = event
        
        # Usar solo los eventos más exactos
        month_events = list(event_groups.values())
    
    # Ordenar por fecha
    month_events.sort(key=lambda e: e.fecha_utc)
    
    # Obtener nombre del mes
    month_name = datetime(year, month, 1).strftime('%B')
    
    print(f"\n=== Eventos para {month_name} {year} ===")
    print(f"Total de eventos: {len(month_events)}")
    
    # Mostrar eventos en formato similar a AstroSeek
    for event in month_events:
        date_str = event.fecha_utc.strftime('%b %d, %H:%M')
        print(f"{date_str}\tTransit {event.planeta1}  - {event.tipo_aspecto} -  {event.planeta2}")
        if 'posicion1' in event.metadata:
            print(f"  Posición: {event.metadata['posicion1']}, Orbe: {event.orbe:.2f}°")
    
    return month_events

def export_events_to_csv(events, filename, filter_aspects=None, exclude_angles=True, only_exact=False):
    """
    Exporta los eventos a un archivo CSV.
    
    Args:
        events: Lista de eventos a exportar
        filename: Nombre del archivo CSV
        filter_aspects: Lista opcional de aspectos a filtrar (ej. ["Conjunción", "Oposición", "Cuadratura"])
        exclude_angles: Si es True, excluye aspectos a puntos como MC, IC, ASC, DESC
        only_exact: Si es True, solo incluye aspectos con estado "Exacto"
    """
    # Filtrar solo eventos de aspecto
    aspect_events = [e for e in events if e.tipo_evento == EventType.ASPECTO]
    
    # Filtrar por aspectos si se especifica
    if filter_aspects:
        aspect_events = [e for e in aspect_events if e.tipo_aspecto in filter_aspects]
    
    # Excluir aspectos a ángulos si se solicita
    if exclude_angles:
        aspect_events = [e for e in aspect_events if e.planeta2 not in ['MC', 'IC', 'ASC', 'DESC']]
    
    # Filtrar solo aspectos exactos si se solicita
    if only_exact:
        aspect_events = [e for e in aspect_events if e.metadata.get('estado', '') == 'Exacto']
    
    # Ordenar por fecha
    aspect_events.sort(key=lambda e: e.fecha_utc)
    
    # Crear directorio de salida si no existe
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Escribir eventos al archivo CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Escribir encabezado
        writer.writerow([
            'Fecha', 'Hora', 'Planeta Transitante', 'Aspecto', 'Planeta Natal',
            'Posición', 'Signo', 'Orbe', 'Movimiento', 'Estado'
        ])
        
        # Escribir datos
        for event in aspect_events:
            # Extraer posición y signo
            posicion = event.metadata.get('posicion1', '')
            signo = ''
            if ' ' in posicion:
                posicion, signo = posicion.split(' ', 1)
            
            # Escribir fila
            writer.writerow([
                event.fecha_utc.strftime('%Y-%m-%d'),
                event.fecha_utc.strftime('%H:%M'),
                event.planeta1,
                event.tipo_aspecto,
                event.planeta2,
                posicion,
                signo,
                f"{event.orbe:.2f}°",
                event.metadata.get('movimiento', ''),
                event.metadata.get('estado', '')
            ])
    
    print(f"\nEventos exportados a: {filename}")
    print(f"Total de eventos exportados: {len(aspect_events)}")
    
    return aspect_events

def test_optimized_calculator(natal_data, year, max_events=30, export_csv=True):
    """
    Prueba el calculador optimizado para todo el año.
    
    Args:
        natal_data: Datos natales del usuario
        year: Año para calcular los tránsitos
        max_events: Número máximo de eventos a mostrar
        export_csv: Si es True, exporta los eventos a un archivo CSV
    """
    # Definir fechas de inicio y fin para todo el año (usando GMT-3 para coincidir con AstroSeek)
    start_date = datetime(year, 1, 1, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    end_date = datetime(year, 12, 31, 23, 59, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))  # Todo el año
    
    # Inicializar calculador optimizado
    print("\n=== Inicializando calculador optimizado ===")
    optimized_calc = OptimizedTransitsCalculator(natal_data)
    
    # Calcular tránsitos con el calculador optimizado
    print("\n=== Calculando tránsitos con el calculador optimizado para todo el año ===")
    start_time = time.time()
    optimized_events = optimized_calc.calculate_all(start_date, end_date)
    optimized_time = time.time() - start_time
    print(f"Tiempo total: {optimized_time:.2f} segundos")
    print(f"Eventos encontrados: {len(optimized_events)}")
    
    # Filtrar solo eventos de aspecto
    optimized_aspects = [e for e in optimized_events if e.tipo_evento == EventType.ASPECTO]
    
    # Mostrar resumen por mes
    print("\n=== Resumen de eventos por mes ===")
    events_by_month = {}
    for event in optimized_aspects:
        month = event.fecha_utc.month
        if month not in events_by_month:
            events_by_month[month] = []
        events_by_month[month].append(event)
    
    for month in sorted(events_by_month.keys()):
        month_name = datetime(year, month, 1).strftime('%B')
        print(f"{month_name}: {len(events_by_month[month])} eventos")
    
    # Comparar con AstroSeek (solo para enero)
    january_events = [e for e in optimized_events if e.fecha_utc.month == 1]
    compare_with_astroseek(january_events)
    
    # Mostrar eventos de febrero (solo conjunciones, oposiciones y cuadraturas)
    february_events = display_month_events(
        optimized_events, 
        2, 
        year, 
        filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
    )
    
    # Mostrar eventos de marzo (solo conjunciones, oposiciones y cuadraturas)
    march_events = display_month_events(
        optimized_events, 
        3, 
        year, 
        filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
    )
    
    # Exportar eventos a CSV si se solicita
    if export_csv:
        csv_filename = f"/Users/apple/astro_calendar_personal_v3/output/transitos_{year}.csv"
        export_events_to_csv(
            optimized_events,
            csv_filename,
            filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
        )
    
    return optimized_events

def show_month(events, month, year=2025):
    """
    Función auxiliar para mostrar eventos de un mes específico.
    
    Args:
        events: Lista de eventos calculados
        month: Número del mes (1-12)
        year: Año (default: 2025)
    """
    return display_month_events(
        events, 
        month, 
        year, 
        filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
    )

def test_astronomical_calculator(natal_data, year, max_events=30, export_csv=True):
    """
    Prueba el calculador astronómico para todo el año.
    
    Args:
        natal_data: Datos natales del usuario
        year: Año para calcular los tránsitos
        max_events: Número máximo de eventos a mostrar
        export_csv: Si es True, exporta los eventos a un archivo CSV
    """
    # Definir fechas de inicio y fin para todo el año (usando GMT-3 para coincidir con AstroSeek)
    start_date = datetime(year, 1, 1, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    end_date = datetime(year, 12, 31, 23, 59, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))  # Todo el año
    
    # Inicializar calculador astronómico
    print("\n=== Inicializando calculador astronómico ===")
    from src.calculators.astronomical_transits_calculator import AstronomicalTransitsCalculator
    astronomical_calc = AstronomicalTransitsCalculator(natal_data)
    
    # Calcular tránsitos con el calculador astronómico
    print("\n=== Calculando tránsitos con el calculador astronómico para todo el año ===")
    start_time = time.time()
    astronomical_events = astronomical_calc.calculate_all(start_date, end_date)
    astronomical_time = time.time() - start_time
    print(f"Tiempo total: {astronomical_time:.2f} segundos")
    print(f"Eventos encontrados: {len(astronomical_events)}")
    
    # Filtrar solo eventos de aspecto
    astronomical_aspects = [e for e in astronomical_events if e.tipo_evento == EventType.ASPECTO]
    
    # Mostrar resumen por mes
    print("\n=== Resumen de eventos por mes ===")
    events_by_month = {}
    for event in astronomical_aspects:
        month = event.fecha_utc.month
        if month not in events_by_month:
            events_by_month[month] = []
        events_by_month[month].append(event)
    
    for month in sorted(events_by_month.keys()):
        month_name = datetime(year, month, 1).strftime('%B')
        print(f"{month_name}: {len(events_by_month[month])} eventos")
    
    # Comparar con AstroSeek (solo para enero)
    january_events = [e for e in astronomical_events if e.fecha_utc.month == 1]
    compare_with_astroseek(january_events)
    
    # Mostrar eventos de febrero (solo conjunciones, oposiciones y cuadraturas)
    february_events = display_month_events(
        astronomical_events, 
        2, 
        year, 
        filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
    )
    
    # Mostrar eventos de marzo (solo conjunciones, oposiciones y cuadraturas)
    march_events = display_month_events(
        astronomical_events, 
        3, 
        year, 
        filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
    )
    
    # Exportar eventos a CSV si se solicita
    if export_csv:
        csv_filename = f"/Users/apple/astro_calendar_personal_v3/output/transitos_astronomicos_{year}.csv"
        export_events_to_csv(
            astronomical_events,
            csv_filename,
            filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
        )
    
    return astronomical_events

def test_astronomical_calculator_v2(natal_data, year, max_events=30, export_csv=True):
    """
    Prueba el calculador astronómico v2 para todo el año.
    
    Args:
        natal_data: Datos natales del usuario
        year: Año para calcular los tránsitos
        max_events: Número máximo de eventos a mostrar
        export_csv: Si es True, exporta los eventos a un archivo CSV
    """
    # Definir fechas de inicio y fin para todo el año (usando GMT-3 para coincidir con AstroSeek)
    start_date = datetime(year, 1, 1, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
    end_date = datetime(year, 12, 31, 23, 59, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))  # Todo el año
    
    # Inicializar calculador astronómico v2
    print("\n=== Inicializando calculador astronómico v2 ===")
    from src.calculators.astronomical_transits_calculator_v2 import AstronomicalTransitsCalculatorV2
    astronomical_calc_v2 = AstronomicalTransitsCalculatorV2(natal_data)
    
    # Calcular tránsitos con el calculador astronómico v2
    print("\n=== Calculando tránsitos con el calculador astronómico v2 para todo el año ===")
    start_time = time.time()
    astronomical_events_v2 = astronomical_calc_v2.calculate_all(start_date, end_date)
    astronomical_time_v2 = time.time() - start_time
    print(f"Tiempo total: {astronomical_time_v2:.2f} segundos")
    print(f"Eventos encontrados: {len(astronomical_events_v2)}")
    
    # Filtrar solo eventos de aspecto
    astronomical_aspects_v2 = [e for e in astronomical_events_v2 if e.tipo_evento == EventType.ASPECTO]
    
    # Mostrar resumen por mes
    print("\n=== Resumen de eventos por mes ===")
    events_by_month = {}
    for event in astronomical_aspects_v2:
        month = event.fecha_utc.month
        if month not in events_by_month:
            events_by_month[month] = []
        events_by_month[month].append(event)
    
    for month in sorted(events_by_month.keys()):
        month_name = datetime(year, month, 1).strftime('%B')
        print(f"{month_name}: {len(events_by_month[month])} eventos")
    
    # Comparar con AstroSeek (solo para enero)
    january_events = [e for e in astronomical_events_v2 if e.fecha_utc.month == 1]
    compare_with_astroseek(january_events)
    
    # Mostrar eventos de febrero (solo conjunciones, oposiciones y cuadraturas)
    february_events = display_month_events(
        astronomical_events_v2, 
        2, 
        year, 
        filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
    )
    
    # Mostrar eventos de marzo (solo conjunciones, oposiciones y cuadraturas)
    march_events = display_month_events(
        astronomical_events_v2, 
        3, 
        year, 
        filter_aspects=["Conjunción", "Oposición", "Cuadratura"]
    )
    
    # Exportar eventos a CSV si se solicita
    if export_csv:
        csv_filename = f"/Users/apple/astro_calendar_personal_v3/output/transitos_astronomicos_v2_{year}.csv"
        export_events_to_csv(
            astronomical_events_v2,
            csv_filename,
            filter_aspects=["Conjunción", "Oposición", "Cuadratura"],
            only_exact=True
        )
    
    return astronomical_events_v2

if __name__ == "__main__":
    # Usar la carta natal específica proporcionada por el usuario
    natal_file = "/Users/apple/astro_calendar_personal_v3/output/carta_natal_lmopti.json"
    print(f"Usando archivo de carta natal: {natal_file}")
    
    # Cargar datos natales
    natal_data = load_natal_data(natal_file)
    
    # Elegir qué calculador probar
    calculator_type = "astronomical_v2"  # Opciones: "optimized", "astronomical", "astronomical_v2"
    
    if calculator_type == "optimized":
        # Probar el calculador optimizado para todo el año 2025
        all_events = test_optimized_calculator(natal_data, 2025)
    elif calculator_type == "astronomical":
        # Probar el calculador astronómico para todo el año 2025
        all_events = test_astronomical_calculator(natal_data, 2025)
    elif calculator_type == "astronomical_v2":
        # Probar el calculador astronómico v2 para todo el año 2025
        all_events = test_astronomical_calculator_v2(natal_data, 2025)
    
    # Mostrar eventos de febrero (solo conjunciones, oposiciones y cuadraturas)
    # Para mostrar otros meses, cambiar el número del mes (1-12)
    # show_month(all_events, 2)  # Febrero
