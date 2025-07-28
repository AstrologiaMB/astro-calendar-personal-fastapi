"""
Calculador de tránsitos utilizando la biblioteca Immanuel.
Proporciona cálculos rápidos y precisos para tránsitos planetarios
utilizando directamente las funciones find.next() de Immanuel.
Implementa procesamiento paralelo para aprovechar múltiples núcleos.
"""
import swisseph as swe
from datetime import datetime
import math
import pytz
import time
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple

from immanuel.tools import find, ephemeris
from immanuel.const import chart, calc

from ..core.constants import EventType
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day

# Mapeo de IDs a nombres de planetas
PLANET_NAMES = {
    chart.SUN: "Sol",
    chart.MOON: "Luna",
    chart.MERCURY: "Mercurio",
    chart.VENUS: "Venus",
    chart.MARS: "Marte",
    chart.JUPITER: "Júpiter",
    chart.SATURN: "Saturno",
    chart.URANUS: "Urano",
    chart.NEPTUNE: "Neptuno",
    chart.PLUTO: "Plutón"
}

# Lista de planetas a procesar
PLANETS_TO_CHECK = [
    chart.SUN,
    chart.MERCURY,
    chart.VENUS,
    chart.MARS,
    chart.JUPITER,
    chart.SATURN,
    chart.URANUS,
    chart.NEPTUNE,
    chart.PLUTO
]

# Mapeo de aspectos
ASPECT_NAMES = {
    calc.CONJUNCTION: "Conjunción",
    calc.OPPOSITION: "Oposición",
    calc.SQUARE: "Cuadratura"
}

# Lista de aspectos a verificar
ASPECTS_TO_CHECK = [
    calc.CONJUNCTION,
    calc.OPPOSITION,
    calc.SQUARE
]

# Mapeo de movimiento
MOVEMENT_NAMES = {
    calc.DIRECT: "Directo",
    calc.RETROGRADE: "Retrógrado",
    calc.STATIONARY: "Estacionario"
}

# Mapeo de estado del aspecto
ASPECT_STATE = {
    calc.APPLICATIVE: "Aplicativo",
    calc.EXACT: "Exacto",
    calc.SEPARATIVE: "Separativo"
}


class ImmanuelTransitsCalculator:
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de tránsitos basado en Immanuel.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
        """
        self.natal_data = natal_data
        
        # Crear diccionario de posiciones natales
        self.natal_positions = {}
        for planet_name, data in natal_data['points'].items():
            if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                             'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                planet_id = getattr(chart, planet_name.upper())
                self.natal_positions[planet_id] = data['longitude']
    
    def _jd_to_datetime(self, jd: float) -> datetime:
        """
        Convierte un día juliano a un objeto datetime con zona horaria.
        
        Args:
            jd: Día juliano
            
        Returns:
            Objeto datetime con zona horaria UTC
        """
        dt_tuple = swe.jdut1_to_utc(jd)
        dt = datetime(dt_tuple[0], dt_tuple[1], dt_tuple[2], 
                     dt_tuple[3], dt_tuple[4], int(dt_tuple[5]))
        return pytz.utc.localize(dt)
    
    def _get_aspect_state(self, planet_id: int, jd: float, aspect: float, natal_lon: float) -> Dict[str, Any]:
        """
        Determina el estado del aspecto (aplicativo, exacto, separativo).
        
        Args:
            planet_id: ID del planeta transitante
            jd: Día juliano
            aspect: Ángulo del aspecto
            natal_lon: Longitud natal
            
        Returns:
            Diccionario con información del aspecto
        """
        # Obtener posición actual
        planet_data = ephemeris.planet(planet_id, jd)
        
        # Calcular diferencia angular
        diff = abs(swe.difdeg2n(planet_data['lon'], natal_lon + aspect))
        
        # Determinar si es aplicativo o separativo
        # Si el planeta es retrógrado, la lógica se invierte
        is_retrograde = planet_data['speed'] < 0
        
        if diff < 0.001:  # Aspecto exacto
            state = calc.EXACT
        elif (is_retrograde and diff > 0) or (not is_retrograde and diff < 0):
            state = calc.APPLICATIVE
        else:
            state = calc.SEPARATIVE
            
        return {
            'planet_lon': planet_data['lon'],
            'diff': abs(diff),
            'state': state,
            'movement': calc.RETROGRADE if is_retrograde else calc.DIRECT,
            'speed': planet_data['speed']
        }
    
    def _calculate_aspects_for_combination(self, transit_planet: int, natal_planet: int, 
                                         natal_lon: float, aspect: float, 
                                         jd_start: float, jd_end: float) -> List[AstroEvent]:
        """
        Calcula todos los aspectos para una combinación específica de planeta transitante,
        planeta natal y tipo de aspecto.
        
        Args:
            transit_planet: ID del planeta transitante
            natal_planet: ID del planeta natal
            natal_lon: Longitud natal
            aspect: Tipo de aspecto
            jd_start: Día juliano de inicio
            jd_end: Día juliano de fin
            
        Returns:
            Lista de eventos AstroEvent
        """
        events = []
        
        # Iniciar búsqueda desde el inicio del período
        jd = jd_start
        
        # Buscar todos los aspectos en el período
        while jd < jd_end:
            try:
                # Encontrar próximo aspecto
                # Para tránsitos, necesitamos encontrar cuándo el planeta transitante forma un aspecto con una posición fija
                jd_aspect = None
                
                # Crear un "planeta ficticio" en la posición natal + aspecto
                # Esto nos permite usar find.next() para encontrar cuándo el planeta transitante
                # llega a la posición que forma el aspecto con la posición natal
                if aspect == calc.CONJUNCTION:
                    # Para conjunción, buscamos cuando el planeta transitante llega a la misma longitud que el natal
                    target_lon = natal_lon
                elif aspect == calc.OPPOSITION:
                    # Para oposición, buscamos cuando el planeta transitante llega a 180° del natal
                    target_lon = (natal_lon + 180) % 360
                elif aspect == calc.SQUARE:
                    # Para cuadratura, buscamos cuando el planeta transitante llega a 90° o 270° del natal
                    # Primero intentamos con 90°
                    target_lon_90 = (natal_lon + 90) % 360
                    target_lon_270 = (natal_lon + 270) % 360
                    
                    # Encontrar el próximo momento en que el planeta transitante llega a cada posición
                    try:
                        # Usar find.next() para encontrar cuándo el planeta transitante llega a target_lon_90
                        jd_90 = find.next(transit_planet, chart.NONE, jd, calc.CONJUNCTION, target_lon_90)
                    except Exception:
                        # Si hay un error, asumir que no hay aspecto en el período
                        jd_90 = float('inf')
                        
                    try:
                        # Usar find.next() para encontrar cuándo el planeta transitante llega a target_lon_270
                        jd_270 = find.next(transit_planet, chart.NONE, jd, calc.CONJUNCTION, target_lon_270)
                    except Exception:
                        # Si hay un error, asumir que no hay aspecto en el período
                        jd_270 = float('inf')
                    
                    # Tomar el que ocurra primero
                    if jd_90 < jd_270 and jd_90 < jd_end:
                        jd_aspect = jd_90
                        target_lon = target_lon_90
                    elif jd_270 < jd_end:
                        jd_aspect = jd_270
                        target_lon = target_lon_270
                    else:
                        # Ninguno ocurre dentro del período, avanzar y continuar
                        jd += 30
                        continue
                else:
                    raise ValueError(f"Aspecto no soportado: {aspect}")
                
                # Si no es una cuadratura, calcular el aspecto directamente
                if aspect != calc.SQUARE:
                    try:
                        # Usar find.next() para encontrar cuándo el planeta transitante llega a target_lon
                        jd_aspect = find.next(transit_planet, chart.NONE, jd, calc.CONJUNCTION, target_lon)
                    except Exception as e:
                        # Si hay un error, avanzar y continuar
                        jd += 30
                        continue
                
                # Si el aspecto ocurre después del final del período, salir del bucle
                if jd_aspect >= jd_end:
                    break
                    
                # Obtener información del aspecto
                aspect_info = self._get_aspect_state(transit_planet, jd_aspect, aspect, natal_lon)
                
                # Convertir a datetime
                dt = self._jd_to_datetime(jd_aspect)
                
                # Crear descripción del evento
                descripcion = (f"{PLANET_NAMES[transit_planet]} {ASPECT_NAMES[aspect]} "
                             f"{PLANET_NAMES[natal_planet]} Natal")
                
                # Crear objeto AstroEvent
                event = AstroEvent(
                    fecha_utc=dt,
                    tipo_evento=EventType.ASPECTO,
                    descripcion=descripcion,
                    planeta1=PLANET_NAMES[transit_planet],
                    planeta2=PLANET_NAMES[natal_planet],
                    longitud1=aspect_info['planet_lon'],
                    longitud2=natal_lon,
                    tipo_aspecto=ASPECT_NAMES[aspect],
                    orbe=aspect_info['diff'],
                    es_aplicativo=(aspect_info['state'] == calc.APPLICATIVE),
                    metadata={
                        'movimiento': MOVEMENT_NAMES[aspect_info['movement']],
                        'estado': ASPECT_STATE[aspect_info['state']]
                    }
                )
                
                # Añadir evento a la lista
                events.append(event)
                
                # Avanzar un poco más allá del aspecto para encontrar el siguiente
                jd = jd_aspect + 1
                
            except Exception as e:
                # Avanzar un día para evitar bucle infinito
                jd += 1
        
        return events
    
    def calculate_all(self, start_date: datetime = None, end_date: datetime = None) -> List[AstroEvent]:
        """
        Calcula todos los tránsitos para el período especificado usando find.next()
        y procesamiento paralelo para aprovechar múltiples núcleos.
        
        Args:
            start_date: Fecha inicial (default: 1 enero del año actual)
            end_date: Fecha final (default: 31 diciembre del año actual)
            
        Returns:
            Lista de eventos de tránsitos
        """
        # Si no se especifican fechas, usar el año actual completo
        if not start_date:
            start_date = datetime(datetime.now().year, 1, 1, tzinfo=pytz.UTC)
        if not end_date:
            end_date = datetime(datetime.now().year, 12, 31, 23, 59, tzinfo=pytz.UTC)
        
        # Convertir fechas a días julianos
        jd_start = julian_day(start_date)
        jd_end = julian_day(end_date)
        
        # Registrar tiempo de inicio
        start_time = time.time()
        print("\nCalculando tránsitos con el método Immanuel (procesamiento paralelo)...")
        
        # Crear lista de trabajos (combinaciones de planeta-planeta-aspecto)
        jobs = []
        for transit_planet in PLANETS_TO_CHECK:
            for natal_planet, natal_lon in self.natal_positions.items():
                for aspect in ASPECTS_TO_CHECK:
                    jobs.append((transit_planet, natal_planet, natal_lon, aspect))
        
        print(f"Procesando {len(jobs)} combinaciones en paralelo usando 8 núcleos...")
        
        # Procesar en paralelo
        all_events = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            # Mapear cada trabajo a un proceso
            futures = [executor.submit(self._calculate_aspects_for_combination, 
                                      job[0], job[1], job[2], job[3], 
                                      jd_start, jd_end) 
                      for job in jobs]
            
        # Mostrar progreso
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                events = future.result()
                all_events.extend(events)
                
                # Actualizar progreso
                completed += 1
                print(f"Progreso: {completed}/{len(jobs)} combinaciones completadas ({completed*100/len(jobs):.1f}%)")
                
            except Exception as e:
                print(f"Error en un proceso: {e}")
                print(f"Detalles del error: {str(e)}")
        
        # Ordenar eventos por fecha
        all_events.sort(key=lambda x: x.fecha_utc)
        
        # Filtrar eventos para asegurarnos de que estén dentro del período especificado
        filtered_events = []
        for event in all_events:
            # Convertir a UTC para comparar con start_date y end_date
            event_utc = event.fecha_utc.astimezone(pytz.UTC)
            if start_date <= event_utc <= end_date:
                filtered_events.append(event)
        
        # Mostrar resumen
        elapsed = time.time() - start_time
        print(f"\nCálculo completado en {elapsed:.2f} segundos")
        print(f"Total de eventos encontrados: {len(filtered_events)}")
        
        return filtered_events
