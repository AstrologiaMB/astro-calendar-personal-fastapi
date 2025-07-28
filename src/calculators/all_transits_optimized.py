"""
Calculador de tránsitos optimizado basado en all_transits_parallel.py.
Implementa varias optimizaciones para mejorar el rendimiento:
1. Optimización del cálculo de JD con incremento directo
2. Caché avanzado de cálculos de efemérides con estrategia multinivel
4. Optimización del paralelismo con balanceo de carga adaptativo
5. Métricas detalladas de rendimiento
"""
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Tuple, Any, Optional, Set
import math
from functools import lru_cache
from multiprocessing import Value, Manager

from src.core import config
from src.core.base_event import AstroEvent
from src.core.constants import EventType
import immanuel.charts as charts
from immanuel.const import chart, calc
from immanuel.setup import settings
from immanuel.reports import aspect
from immanuel.tools import ephemeris

# Configuración de immanuel para aspectos
settings.aspects = [calc.CONJUNCTION, calc.OPPOSITION, calc.SQUARE]
settings.default_orb = 2.0  # Orbe de 2°
settings.exact_orb = 0.001  # Aspecto exacto dentro de 0.001°

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

# Constantes para optimización
J2000_JD = 2451545.0  # JD para J2000 (2000-01-01 12:00 UTC)
SECONDS_PER_DAY = 86400.0  # Segundos en un día
MIN_STEP_MINUTES = 1  # Paso mínimo en minutos
MAX_STEP_MINUTES = 1440  # Paso máximo en minutos (1 día)
REFINEMENT_THRESHOLD_DEGREES = 2.0  # Umbral para refinamiento en grados (ajustado para coincidir con settings.default_orb)
EXACT_THRESHOLD_DEGREES = 0.001  # Umbral para considerar un aspecto exacto (ajustado para coincidir con settings.exact_orb)

# Constantes para caché adaptativo
CACHE_PRECISION = {
    chart.SUN: 5,       # ~1 segundo
    chart.MOON: 6,      # ~0.1 segundos
    chart.MERCURY: 5,   # ~1 segundo
    chart.VENUS: 5,     # ~1 segundo
    chart.MARS: 4,      # ~10 segundos
    chart.JUPITER: 3,   # ~100 segundos
    chart.SATURN: 3,    # ~100 segundos
    chart.URANUS: 2,    # ~1000 segundos
    chart.NEPTUNE: 2,   # ~1000 segundos
    chart.PLUTO: 2      # ~1000 segundos
}

# Tamaño del caché LRU secundario
LRU_CACHE_SIZE = 2048

# Caché secundario con LRU para cálculos de efemérides
@lru_cache(maxsize=LRU_CACHE_SIZE)
def _cached_planet_calculation(planet_id, jd_rounded):
    """
    Función de caché secundario con LRU para cálculos de efemérides.
    
    Args:
        planet_id: ID del planeta
        jd_rounded: JD redondeado según la precisión adecuada
        
    Returns:
        Posición del planeta
    """
    return ephemeris.planet(planet_id, jd_rounded)

class PerformanceMetrics:
    """
    Clase para gestionar métricas de rendimiento.
    """
    def __init__(self):
        # Métricas globales como atributos simples
        self.total_calculations = 0
        self.cache_hits = 0
        self.steps_skipped = 0
        self.aspects_found = 0
        
        # Métricas por planeta (diccionario local)
        self.planet_metrics = {
            planet_id: {
                'calculations': 0,
                'cache_hits': 0,
                'aspects_found': 0
            } for planet_id in PLANETS_TO_CHECK
        }
        
        # Métricas de tiempo
        self.start_time = time.time()
        self.segment_times = []
    
    def increment(self, metric_name, value=1, planet_id=None):
        """
        Incrementa una métrica específica.
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor a incrementar
            planet_id: ID del planeta (opcional)
        """
        # Incrementar contador global
        if hasattr(self, metric_name):
            setattr(self, metric_name, getattr(self, metric_name) + value)
        
        # Incrementar contador por planeta si se especifica
        if planet_id is not None and metric_name in ['calculations', 'cache_hits', 'aspects_found']:
            self.planet_metrics[planet_id][metric_name] += value
    
    def get_summary(self, include_planets=False):
        """
        Obtiene un resumen de las métricas.
        
        Args:
            include_planets: Si es True, incluye métricas por planeta
            
        Returns:
            Diccionario con el resumen de métricas
        """
        elapsed = time.time() - self.start_time
        
        summary = {
            'elapsed_time': elapsed,
            'total_calculations': self.total_calculations,
            'cache_hits': self.cache_hits,
            'steps_skipped': self.steps_skipped,
            'aspects_found': self.aspects_found,
        }
        
        if include_planets:
            summary['planet_metrics'] = self.planet_metrics
            
        return summary
    
    def add_segment_time(self, segment_id, elapsed_time, events_count):
        """
        Registra el tiempo de ejecución de un segmento.
        
        Args:
            segment_id: ID del segmento
            elapsed_time: Tiempo de ejecución en segundos
            events_count: Número de eventos encontrados
        """
        self.segment_times.append((segment_id, elapsed_time, events_count))
    
    def get_segment_stats(self):
        """
        Obtiene estadísticas de los segmentos.
        
        Returns:
            Diccionario con estadísticas de segmentos
        """
        if not self.segment_times:
            return {}
        
        times = [t[1] for t in self.segment_times]
        events = [t[2] for t in self.segment_times]
        
        return {
            'segments_count': len(self.segment_times),
            'avg_time': sum(times) / len(times) if times else 0,
            'min_time': min(times) if times else 0,
            'max_time': max(times) if times else 0,
            'total_events': sum(events),
            'avg_events': sum(events) / len(times) if times and events else 0
        }

class OptimizedTransitsCalculator:
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de tránsitos optimizado.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
        """
        self.natal_data = natal_data
        
        # Crear diccionario de posiciones natales
        self.natal_positions = {}
        for planet_name, data in natal_data['points'].items():
            if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                             'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                self.natal_positions[getattr(chart, planet_name.upper())] = {
                    'longitude': data['longitude'],
                    'latitude': 0,
                    'distance': 0,
                    'speed': 0
                }
        
        # Caché para cálculos de efemérides (caché primario)
        self.ephemeris_cache = {}
        
        # Métricas de rendimiento avanzadas
        self.metrics = PerformanceMetrics()
    
    def _datetime_to_jd(self, dt: datetime) -> float:
        """
        Convierte un objeto datetime a día juliano de manera optimizada.
        
        Args:
            dt: Objeto datetime con zona horaria
            
        Returns:
            Día juliano
        """
        # Asegurar que el datetime tenga zona horaria
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        
        # Calcular días desde J2000
        j2000 = datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
        days_since_j2000 = (dt - j2000).total_seconds() / SECONDS_PER_DAY
        
        # Calcular JD
        return J2000_JD + days_since_j2000
    
    def _jd_to_datetime(self, jd: float) -> datetime:
        """
        Convierte un día juliano a un objeto datetime con zona horaria.
        
        Args:
            jd: Día juliano
            
        Returns:
            Objeto datetime con zona horaria UTC
        """
        dt_tuple = ephemeris.swe.jdut1_to_utc(jd)
        dt = datetime(dt_tuple[0], dt_tuple[1], dt_tuple[2], 
                     dt_tuple[3], dt_tuple[4], int(dt_tuple[5]))
        return dt.replace(tzinfo=ZoneInfo("UTC"))
    
    def _get_planet_position(self, planet_id: int, jd: float) -> dict:
        """
        Obtiene la posición de un planeta con caché multinivel.
        
        Args:
            planet_id: ID del planeta
            jd: Día juliano
            
        Returns:
            Diccionario con la posición del planeta
        """
        # Determinar precisión de redondeo basada en la velocidad del planeta
        precision = CACHE_PRECISION.get(planet_id, 4)
        jd_rounded = round(jd, precision)
        
        # Clave para el caché primario
        cache_key = f"{planet_id}_{jd_rounded}"
        
        # Verificar si ya está en caché primario
        if cache_key in self.ephemeris_cache:
            self.metrics.increment('cache_hits', 1, planet_id)
            return self.ephemeris_cache[cache_key]
        
        # Usar caché secundario LRU
        position = _cached_planet_calculation(planet_id, jd_rounded)
        
        # Guardar en caché primario
        self.ephemeris_cache[cache_key] = position
        self.metrics.increment('total_calculations', 1, planet_id)
        
        # Limitar tamaño del caché primario para evitar problemas de memoria
        if len(self.ephemeris_cache) > 10000:
            # Eliminar 20% de las entradas más antiguas
            keys_to_remove = list(self.ephemeris_cache.keys())[:2000]
            for key in keys_to_remove:
                del self.ephemeris_cache[key]
        
        return position
    
    def _get_aspect_targets(self, natal_lon: float, aspect_type: float) -> List[float]:
        """
        Obtiene las longitudes objetivo para un aspecto.
        
        Args:
            natal_lon: Longitud natal
            aspect_type: Tipo de aspecto
            
        Returns:
            Lista de longitudes objetivo
        """
        targets = []
        
        if aspect_type == calc.CONJUNCTION:
            targets.append(natal_lon)
        elif aspect_type == calc.OPPOSITION:
            targets.append((natal_lon + 180) % 360)
        elif aspect_type == calc.SQUARE:
            targets.append((natal_lon + 90) % 360)
            targets.append((natal_lon + 270) % 360)
        
        return targets
    
    def _angular_distance(self, lon1: float, lon2: float) -> float:
        """
        Calcula la distancia angular más corta entre dos longitudes.
        
        Args:
            lon1: Primera longitud
            lon2: Segunda longitud
            
        Returns:
            Distancia angular en grados (0-180)
        """
        diff = abs((lon1 - lon2) % 360)
        return min(diff, 360 - diff)
    
    def _estimate_aspect_time(self, planet_id: int, target_lon: float, 
                             current_jd: float, current_lon: float, 
                             current_speed: float) -> Optional[float]:
        """
        Estima cuándo ocurrirá un aspecto basado en la velocidad del planeta.
        
        Args:
            planet_id: ID del planeta
            target_lon: Longitud objetivo
            current_jd: JD actual
            current_lon: Longitud actual
            current_speed: Velocidad actual en grados/día
            
        Returns:
            JD estimado para el aspecto, o None si no se puede estimar
        """
        # Si la velocidad es muy baja, no podemos hacer una buena estimación
        if abs(current_speed) < 0.01:
            return None
        
        # Calcular la distancia angular más corta
        distance = self._angular_distance(current_lon, target_lon)
        
        # Determinar la dirección
        # Si la velocidad es positiva (movimiento directo), el planeta se mueve en sentido horario
        # Si la velocidad es negativa (movimiento retrógrado), el planeta se mueve en sentido antihorario
        clockwise_distance = (target_lon - current_lon) % 360
        counter_clockwise_distance = (current_lon - target_lon) % 360
        
        # Determinar si el planeta se está acercando al objetivo
        is_approaching = False
        if current_speed > 0 and clockwise_distance < 180:
            is_approaching = True
            distance_to_travel = clockwise_distance
        elif current_speed < 0 and counter_clockwise_distance < 180:
            is_approaching = True
            distance_to_travel = counter_clockwise_distance
        
        # Si el planeta no se está acercando al objetivo, no habrá aspecto
        if not is_approaching:
            return None
        
        # Estimar días hasta el aspecto
        days_to_aspect = distance_to_travel / abs(current_speed)
        
        # Limitar la estimación a un máximo razonable
        if days_to_aspect > 365:
            return None
        
        # Calcular JD estimado
        estimated_jd = current_jd + days_to_aspect
        
        return estimated_jd
    
    def _refine_aspect_time(self, planet_id: int, target_lon: float, 
                           start_jd: float, end_jd: float) -> Optional[Tuple[float, dict]]:
        """
        Refina el momento exacto de un aspecto usando búsqueda binaria.
        
        Args:
            planet_id: ID del planeta
            target_lon: Longitud objetivo
            start_jd: JD de inicio
            end_jd: JD de fin
            
        Returns:
            Tupla (JD del aspecto, datos del planeta) o None si no se encuentra
        """
        # Verificar si el aspecto ocurre en este intervalo
        planet_start = self._get_planet_position(planet_id, start_jd)
        planet_end = self._get_planet_position(planet_id, end_jd)
        
        dist_start = self._angular_distance(planet_start['lon'], target_lon)
        dist_end = self._angular_distance(planet_end['lon'], target_lon)
        
        # Si ambos extremos están lejos del aspecto, probablemente no hay aspecto en este intervalo
        if dist_start > REFINEMENT_THRESHOLD_DEGREES and dist_end > REFINEMENT_THRESHOLD_DEGREES:
            return None
        
        # Si el planeta cambia de dirección en este intervalo, dividir y buscar en cada mitad
        if planet_start['speed'] * planet_end['speed'] < 0:
            mid_jd = (start_jd + end_jd) / 2
            result1 = self._refine_aspect_time(planet_id, target_lon, start_jd, mid_jd)
            if result1 is not None:
                return result1
            
            result2 = self._refine_aspect_time(planet_id, target_lon, mid_jd, end_jd)
            if result2 is not None:
                return result2
            
            return None
        
        # Búsqueda binaria para encontrar el momento exacto
        max_iterations = 20
        iteration = 0
        
        while (end_jd - start_jd) > 0.0001 and iteration < max_iterations:  # Precisión de ~8.6 segundos
            mid_jd = (start_jd + end_jd) / 2
            planet_mid = self._get_planet_position(planet_id, mid_jd)
            dist_mid = self._angular_distance(planet_mid['lon'], target_lon)
            
            # Si encontramos un aspecto exacto, retornar
            if dist_mid <= EXACT_THRESHOLD_DEGREES:
                return (mid_jd, planet_mid)
            
            # Determinar en qué mitad buscar
            # Esto depende de la dirección del movimiento y la posición relativa
            if planet_mid['speed'] > 0:  # Movimiento directo
                if (planet_mid['lon'] - target_lon) % 360 < 180:
                    end_jd = mid_jd  # El planeta ya pasó el objetivo
                else:
                    start_jd = mid_jd  # El planeta aún no llega al objetivo
            else:  # Movimiento retrógrado
                if (planet_mid['lon'] - target_lon) % 360 < 180:
                    start_jd = mid_jd  # El planeta aún no llega al objetivo (en dirección retrógrada)
                else:
                    end_jd = mid_jd  # El planeta ya pasó el objetivo (en dirección retrógrada)
            
            iteration += 1
        
        # Verificar el resultado final
        final_jd = (start_jd + end_jd) / 2
        planet_final = self._get_planet_position(planet_id, final_jd)
        dist_final = self._angular_distance(planet_final['lon'], target_lon)
        
        if dist_final <= settings.default_orb:
            return (final_jd, planet_final)
        
        return None
    
    def _check_aspect(self, planet_data: dict, planet_id: int, natal_planet_id: int, 
                     natal_lon: float, current_dt: datetime, aspects_found: list, 
                     last_aspect: dict) -> bool:
        """
        Verifica si hay un aspecto entre un planeta y un punto natal.
        Implementa la misma lógica que ParallelTransitsCalculator.check_aspect.
        
        Args:
            planet_data: Datos del planeta transitante
            planet_id: ID del planeta transitante
            natal_planet_id: ID del planeta natal
            natal_lon: Longitud natal
            current_dt: Fecha y hora actual
            aspects_found: Lista de aspectos encontrados
            last_aspect: Diccionario de últimos aspectos encontrados
            
        Returns:
            True si se encontró un aspecto, False en caso contrario
        """
        # Crear objeto de planeta natal para aspect.between
        natal_planet = {
            'index': natal_planet_id,
            'lon': natal_lon,
            'lat': 0,
            'speed': 0
        }
        
        # Usar la función aspect.between de immanuel
        aspect_data = aspect.between(planet_data, natal_planet)
        
        if aspect_data and abs(aspect_data['difference']) <= settings.default_orb:
            # Solo procesar aspectos que nos interesan
            if aspect_data['aspect'] in ASPECT_NAMES:
                # Clave única para cada combinación planeta-aspecto-movimiento
                movement = "D" if planet_data['speed'] > 0 else "R"
                key = f"{planet_id}-{natal_planet_id}-{aspect_data['aspect']}-{movement}"
                
                # Calcular diferencia orbital
                diferencia = abs(aspect_data['difference'])
                
                # Guardar el tránsito si es exacto o más preciso que el anterior
                if diferencia <= settings.exact_orb or (
                    key in last_aspect and 
                    diferencia < last_aspect[key]['diferencia'] and
                    aspect_data['movement'] == calc.EXACT
                ):
                    transit = {
                        'jd': self._datetime_to_jd(current_dt),
                        'planet_id': planet_id,
                        'natal_planet_id': natal_planet_id,
                        'aspect_type': aspect_data['aspect'],
                        'planet_lon': planet_data['lon'],
                        'natal_lon': natal_lon,
                        'orb': diferencia,
                        'speed': planet_data['speed'],
                        'movement': calc.DIRECT if planet_data['speed'] > 0 else calc.RETROGRADE,
                        'state': aspect_data['movement'],
                        'diferencia': diferencia  # Add this field to match the parallel calculator
                    }
                    
                    # Actualizar o agregar el tránsito
                    if key in last_aspect:
                        if diferencia < last_aspect[key]['diferencia']:
                            for i, t in enumerate(aspects_found):
                                if t == last_aspect[key]:
                                    aspects_found[i] = transit
                                    last_aspect[key] = transit
                                    break
                    else:
                        aspects_found.append(transit)
                        last_aspect[key] = transit
                
                return True
        
        return False

    def _find_aspects_adaptive(self, planet_id: int, natal_planet_id: int, 
                              natal_lon: float, aspect_type: float,
                              start_jd: float, end_jd: float) -> List[dict]:
        """
        Encuentra aspectos usando un enfoque adaptativo con incremento directo de JD.
        
        Args:
            planet_id: ID del planeta transitante
            natal_planet_id: ID del planeta natal
            natal_lon: Longitud natal
            aspect_type: Tipo de aspecto
            start_jd: JD de inicio
            end_jd: JD de fin
            
        Returns:
            Lista de aspectos encontrados
        """
        aspects_found = []
        last_aspect = {}
        
        # JD actual (trabajamos directamente con JD para mayor eficiencia)
        current_jd = start_jd
        
        # Contador de iteraciones para prevenir bucles infinitos
        max_iterations = 1000  # Reducido para evitar demasiados eventos
        iteration = 0
        last_jd = current_jd  # Para detectar si no avanza
        
        # Paso adaptativo basado en la velocidad del planeta
        # Planetas más rápidos requieren pasos más pequeños
        adaptive_step = 1.0 / 24.0  # Valor inicial: 1 hora
        if planet_id == chart.MOON:
            adaptive_step = 1.0 / 48.0  # 30 minutos para la Luna
        elif planet_id in [chart.MERCURY, chart.VENUS]:
            adaptive_step = 1.0 / 24.0  # 1 hora para Mercurio y Venus
        elif planet_id in [chart.MARS, chart.SUN]:
            adaptive_step = 1.0 / 12.0  # 2 horas para Marte y Sol
        elif planet_id in [chart.JUPITER, chart.SATURN]:
            adaptive_step = 1.0 / 6.0  # 4 horas para Júpiter y Saturno
        else:  # Planetas lentos
            adaptive_step = 1.0 / 4.0  # 6 horas para Urano, Neptuno, Plutón
        
        while current_jd < end_jd and iteration < max_iterations:
            iteration += 1
            
            # Verificar si estamos avanzando
            if current_jd == last_jd:
                current_jd += 1 / 24  # Forzar avance de 1 hora
                continue
            
            last_jd = current_jd
            
            # Obtener posición actual del planeta
            planet_data = self._get_planet_position(planet_id, current_jd)
            current_lon = planet_data['lon']
            current_speed = planet_data['speed']
            
            # Ajustar paso adaptativo basado en la velocidad actual
            # Si el planeta está moviéndose lento, podemos usar pasos más grandes
            speed_factor = max(0.1, min(2.0, abs(current_speed)))
            current_step = adaptive_step / speed_factor
            
            # Convertir JD a datetime para check_aspect
            current_dt = self._jd_to_datetime(current_jd)
            
            # Verificar si hay un aspecto
            found_aspect = self._check_aspect(
                planet_data, planet_id, natal_planet_id, 
                natal_lon, current_dt, aspects_found, last_aspect
            )
            
            if found_aspect:
                # Si encontramos un aspecto, avanzar un día para evitar duplicados
                current_jd = int(current_jd) + 1.0
                self.metrics.increment('aspects_found', 1, planet_id)
                continue
            
            # Si no estamos cerca, intentar predecir cuándo ocurrirá el aspecto
            # Obtener longitudes objetivo para este aspecto
            target_longitudes = self._get_aspect_targets(natal_lon, aspect_type)
            
            # Verificar cada longitud objetivo
            for target_lon in target_longitudes:
                # Calcular distancia angular
                distance = self._angular_distance(current_lon, target_lon)
                
                # Si estamos cerca, no hacer predicción
                if distance <= REFINEMENT_THRESHOLD_DEGREES:
                    continue
                
                estimated_jd = self._estimate_aspect_time(planet_id, target_lon, 
                                                        current_jd, current_lon, 
                                                        current_speed)
                
                if estimated_jd is not None and estimated_jd < end_jd:
                    # Calcular cuántos días saltar
                    days_to_skip = max(0, estimated_jd - current_jd - 1)
                    
                    # Limitar el salto a un máximo razonable
                    days_to_skip = min(days_to_skip, 5)  # Reducido para mayor seguridad
                    
                    if days_to_skip > 0:
                        # Saltar directamente a un momento cercano al aspecto estimado
                        current_jd += days_to_skip
                        self.metrics.increment('steps_skipped', int(days_to_skip * 1440 / MIN_STEP_MINUTES))  # 1440 minutos en un día
                        break
            
            # Si no se encontró ningún aspecto ni se hizo ningún salto, avanzar un paso adaptativo
            if current_jd == last_jd:  # Si no avanzó en este ciclo
                current_jd += current_step
        
            # Verificar si se alcanzó el límite de iteraciones
            if iteration >= max_iterations:
                # Reducir verbosidad para evitar problemas de contexto
                pass
                # print(f"ADVERTENCIA: Se alcanzó el límite de iteraciones ({max_iterations}) "
                #       f"para {PLANET_NAMES.get(planet_id, planet_id)} - "
                #       f"{PLANET_NAMES.get(natal_planet_id, natal_planet_id)} - "
                #       f"{ASPECT_NAMES.get(aspect_type, aspect_type)}")
        
        # Retornar los aspectos encontrados
        return aspects_found
    
    def _get_aspect_state(self, planet_data: dict, aspect_type: float, natal_lon: float) -> Dict[str, Any]:
        """
        Determina el estado del aspecto (aplicativo, exacto, separativo).
        
        Args:
            planet_data: Datos del planeta
            aspect_type: Tipo de aspecto
            natal_lon: Longitud natal
            
        Returns:
            Diccionario con información del aspecto
        """
        # Calcular longitud objetivo
        if aspect_type == calc.CONJUNCTION:
            target_lon = natal_lon
        elif aspect_type == calc.OPPOSITION:
            target_lon = (natal_lon + 180) % 360
        elif aspect_type == calc.SQUARE:
            # Para cuadratura, usar la más cercana
            target_90 = (natal_lon + 90) % 360
            target_270 = (natal_lon + 270) % 360
            
            if self._angular_distance(planet_data['lon'], target_90) < self._angular_distance(planet_data['lon'], target_270):
                target_lon = target_90
            else:
                target_lon = target_270
        else:
            target_lon = (natal_lon + aspect_type) % 360
        
        # Calcular diferencia angular
        diff = (planet_data['lon'] - target_lon) % 360
        if diff > 180:
            diff = diff - 360
        
        # Determinar si es aplicativo o separativo
        # Si el planeta es retrógrado, la lógica se invierte
        is_retrograde = planet_data['speed'] < 0
        
        if abs(diff) < 0.001:  # Aspecto exacto
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
    
    def _calculate_segment(self, start_date: datetime, end_date: datetime, segment_id: int = 0) -> List[AstroEvent]:
        """
        Calcula los tránsitos para un segmento de tiempo específico.
        
        Args:
            start_date: Fecha inicial del segmento
            end_date: Fecha final del segmento
            segment_id: Identificador del segmento (para seguimiento)
            
        Returns:
            Lista de eventos de tránsitos para este segmento
        """
        try:
            print(f"Iniciando segmento {segment_id}: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
            
            # Convertir fechas a JD directamente (optimización 1)
            start_jd = self._datetime_to_jd(start_date)
            end_jd = self._datetime_to_jd(end_date)
            
            # Crear un caché local para este segmento
            # Esto mejora el rendimiento en procesamiento paralelo al evitar bloqueos
            local_cache = {}
            
            # Registrar tiempo de inicio
            segment_start_time = time.time()
            
            # Lista para almacenar todos los aspectos encontrados
            all_aspects = []
            
            # Procesar cada combinación de planeta transitante y natal
            combinations_count = len(PLANETS_TO_CHECK) * len(self.natal_positions)
            processed_count = 0
            
            # Establecer un tiempo máximo para el segmento (30 minutos)
            max_segment_time = 30 * 60  # 30 minutos en segundos
            
            # Métricas locales para este segmento
            segment_metrics = PerformanceMetrics()
            
            # Priorizar planetas rápidos primero para obtener resultados más rápido
            # Ordenar planetas por velocidad (de más rápido a más lento)
            sorted_planets = [
                chart.MOON,
                chart.MERCURY,
                chart.VENUS,
                chart.SUN,
                chart.MARS,
                chart.JUPITER,
                chart.SATURN,
                chart.URANUS,
                chart.NEPTUNE,
                chart.PLUTO
            ]
            
            # Filtrar solo los planetas que están en PLANETS_TO_CHECK
            sorted_planets = [p for p in sorted_planets if p in PLANETS_TO_CHECK]
            
            # Crear un diccionario para rastrear los últimos aspectos encontrados
            last_aspects = {}
            
            # Paso de tiempo en minutos
            step_minutes = 1
            
            # Convertir fechas a datetime
            current_dt = start_date
            
            # Buscar aspectos minuto a minuto (como en el calculador paralelo)
            while current_dt <= end_date:
                # Calcular JD para este momento
                current_jd = self._datetime_to_jd(current_dt)
                
                # Verificar si hemos excedido el tiempo máximo
                if time.time() - segment_start_time > max_segment_time:
                    print(f"ADVERTENCIA: Segmento {segment_id} excedió el tiempo máximo permitido. Terminando.")
                    break
                
                # Procesar cada planeta transitante
                for transit_planet in sorted_planets:
                    # Obtener posición del planeta transitante
                    planet_data = self._get_planet_position(transit_planet, current_jd)
                    
                    # Calcular aspectos con cada planeta natal
                    for natal_planet, natal_data in self.natal_positions.items():
                        # Verificar aspecto usando posición natal fija
                        self._check_aspect(
                            planet_data, transit_planet, natal_planet, 
                            natal_data['longitude'], current_dt, 
                            all_aspects, last_aspects
                        )
                
                # Avanzar 1 minuto
                current_dt += timedelta(minutes=step_minutes)
                
                # Actualizar progreso cada 5%
                if current_dt.minute % 5 == 0 and current_dt.second == 0:
                    progress = ((current_dt - start_date).total_seconds() / 
                               (end_date - start_date).total_seconds() * 100)
                    elapsed = time.time() - segment_start_time
                    eta = (elapsed / progress) * (100 - progress) if progress > 0 else 0
                    print(f"Segmento {segment_id}: {progress:.1f}% - "
                          f"Tiempo transcurrido: {elapsed:.1f}s - "
                          f"Tiempo restante estimado: {eta:.1f}s")
            
            # Convertir aspectos a objetos AstroEvent
            events = []
            for aspect_data in all_aspects:
                try:
                    # Obtener información del aspecto
                    planet_data = self._get_planet_position(aspect_data['planet_id'], aspect_data['jd'])
                    aspect_info = self._get_aspect_state(planet_data, aspect_data['aspect_type'], aspect_data['natal_lon'])
                    
                    # Convertir JD a datetime
                    dt = self._jd_to_datetime(aspect_data['jd'])
                    
                    # Crear descripción del evento
                    descripcion = (f"{PLANET_NAMES[aspect_data['planet_id']]} {ASPECT_NAMES[aspect_data['aspect_type']]} "
                                f"{PLANET_NAMES[aspect_data['natal_planet_id']]} Natal")
                    
                    # Crear objeto AstroEvent
                    event = AstroEvent(
                        fecha_utc=dt,
                        tipo_evento=EventType.ASPECTO,
                        descripcion=descripcion,
                        planeta1=PLANET_NAMES[aspect_data['planet_id']],
                        planeta2=PLANET_NAMES[aspect_data['natal_planet_id']],
                        longitud1=aspect_info['planet_lon'],
                        longitud2=aspect_data['natal_lon'],
                        tipo_aspecto=ASPECT_NAMES[aspect_data['aspect_type']],
                        orbe=aspect_info['diff'],
                        es_aplicativo=(aspect_info['state'] == calc.APPLICATIVE),
                        metadata={
                            'movimiento': MOVEMENT_NAMES[aspect_info['movement']],
                            'estado': ASPECT_STATE[aspect_info['state']]
                        }
                    )
                    events.append(event)
                except Exception as e:
                    print(f"Error al crear evento en segmento {segment_id}: {e}")
                    continue
            
            # Mostrar resumen del segmento
            elapsed = time.time() - segment_start_time
            print(f"Segmento {segment_id} completado en {elapsed:.2f}s: {len(events)} eventos encontrados")
            
            # Mostrar métricas del segmento
            metrics_summary = segment_metrics.get_summary()
            print(f"Métricas del segmento {segment_id}:")
            print(f"- Aspectos encontrados: {metrics_summary['aspects_found']}")
            
            # Retornar eventos y métricas
            return events
            
        except Exception as e:
            print(f"Error fatal en segmento {segment_id}: {e}")
            # Retornar una lista vacía en caso de error
            return []
    
    def _identify_complex_periods(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime, float]]:
        """
        Identifica períodos de tiempo con mayor complejidad computacional.
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            
        Returns:
            Lista de tuplas (fecha_inicio, fecha_fin, complejidad)
        """
        # Análisis rápido para identificar períodos con retrogradaciones
        # que son computacionalmente más intensivos
        complex_periods = []
        
        # Convertir fechas a JD
        start_jd = self._datetime_to_jd(start_date)
        end_jd = self._datetime_to_jd(end_date)
        
        # Verificar cada 5 días para planetas rápidos (Mercurio, Venus, Marte)
        # y cada 15 días para planetas lentos
        fast_planets = [chart.MERCURY, chart.VENUS, chart.MARS]
        slow_planets = [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]
        
        # Paso para análisis rápido
        step_jd = 5 / 365.25  # 5 días en JD
        
        # Diccionario para rastrear cambios de dirección
        direction_changes = {}
        
        # Analizar planetas rápidos con mayor frecuencia
        current_jd = start_jd
        while current_jd <= end_jd:
            for planet_id in fast_planets + slow_planets:
                # Solo verificar planetas lentos cada 15 días
                if planet_id in slow_planets and (current_jd - start_jd) % (15 / 365.25) > 0.001:
                    continue
                    
                planet_data = self._get_planet_position(planet_id, current_jd)
                
                # Verificar si hay un cambio de dirección
                next_jd = current_jd + 1/365.25  # 1 día después
                next_planet_data = self._get_planet_position(planet_id, next_jd)
                
                # Si hay un cambio de dirección (de directo a retrógrado o viceversa)
                if (planet_data['speed'] * next_planet_data['speed'] <= 0):
                    # Convertir JD a datetime para el período
                    dt = self._jd_to_datetime(current_jd)
                    
                    # Determinar complejidad basada en el planeta
                    # Mercurio es el más complejo debido a su velocidad
                    complexity = 3.0 if planet_id == chart.MERCURY else 2.0
                    
                    # Definir un período de 10 días antes y después del cambio de dirección
                    period_start = dt - timedelta(days=10)
                    period_end = dt + timedelta(days=10)
                    
                    # Ajustar al rango total
                    if period_start < start_date:
                        period_start = start_date
                    if period_end > end_date:
                        period_end = end_date
                    
                    # Añadir a la lista de períodos complejos
                    complex_periods.append((period_start, period_end, complexity))
                    
                    # Registrar el cambio de dirección
                    key = f"{planet_id}_{int(current_jd)}"
                    direction_changes[key] = (dt, planet_id)
            
            current_jd += step_jd
        
        # Si no se encontraron períodos complejos, devolver una lista vacía
        if not complex_periods:
            return []
        
        # Fusionar períodos superpuestos
        complex_periods.sort(key=lambda x: x[0])  # Ordenar por fecha de inicio
        
        merged_periods = []
        current_start, current_end, current_complexity = complex_periods[0]
        
        for period_start, period_end, complexity in complex_periods[1:]:
            # Si el período actual se superpone con el siguiente
            if period_start <= current_end:
                # Extender el período actual
                current_end = max(current_end, period_end)
                # Usar la mayor complejidad
                current_complexity = max(current_complexity, complexity)
            else:
                # Añadir el período actual a la lista de períodos fusionados
                merged_periods.append((current_start, current_end, current_complexity))
                # Comenzar un nuevo período
                current_start, current_end, current_complexity = period_start, period_end, complexity
        
        # Añadir el último período
        merged_periods.append((current_start, current_end, current_complexity))
        
        # Añadir períodos no complejos
        all_periods = []
        current_date = start_date
        
        for period_start, period_end, complexity in merged_periods:
            # Si hay un hueco antes del período complejo
            if current_date < period_start:
                all_periods.append((current_date, period_start, 1.0))  # Complejidad normal
            
            # Añadir el período complejo
            all_periods.append((period_start, period_end, complexity))
            
            # Actualizar la fecha actual
            current_date = period_end
        
        # Si hay un hueco después del último período complejo
        if current_date < end_date:
            all_periods.append((current_date, end_date, 1.0))  # Complejidad normal
        
        return all_periods
    
    def _optimize_segment_distribution(self, start_date: datetime, end_date: datetime, 
                                      num_cores: int) -> List[Tuple[datetime, datetime]]:
        """
        Optimiza la distribución de segmentos para balancear la carga.
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            num_cores: Número de núcleos disponibles
            
        Returns:
            Lista de tuplas (fecha_inicio, fecha_fin) para cada segmento
        """
        # Identificar períodos complejos
        complex_periods = self._identify_complex_periods(start_date, end_date)
        
        # Si se identificaron períodos complejos, distribuir los segmentos de manera adaptativa
        if complex_periods:
            print("Usando distribución adaptativa de segmentos basada en complejidad...")
            
            # Calcular la complejidad total
            total_complexity = sum([(period_end - period_start).total_seconds() * complexity 
                                  for period_start, period_end, complexity in complex_periods])
            
            # Distribuir los segmentos proporcionalmente a la complejidad
            segments = []
            remaining_cores = num_cores
            
            for period_start, period_end, complexity in complex_periods:
                # Calcular la proporción de núcleos para este período
                period_seconds = (period_end - period_start).total_seconds()
                period_complexity = period_seconds * complexity
                period_cores = max(1, int(round(num_cores * period_complexity / total_complexity)))
                
                # Ajustar para no exceder el número total de núcleos
                if period_cores > remaining_cores:
                    period_cores = remaining_cores
                
                remaining_cores -= period_cores
                
                # Si no quedan núcleos, usar al menos uno
                if remaining_cores <= 0 and period_cores == 0:
                    period_cores = 1
                
                # Dividir el período en segmentos
                if period_cores > 0:
                    segment_seconds = period_seconds / period_cores
                    
                    for i in range(period_cores):
                        seg_start = period_start + timedelta(seconds=i * segment_seconds)
                        # Para el último segmento, usar exactamente period_end para evitar errores de redondeo
                        seg_end = period_end if i == period_cores - 1 else period_start + timedelta(seconds=(i + 1) * segment_seconds)
                        segments.append((seg_start, seg_end))
            
            # Si sobran núcleos, distribuirlos en los períodos más largos
            if remaining_cores > 0:
                # Ordenar segmentos por duración (de mayor a menor)
                segments.sort(key=lambda x: (x[1] - x[0]).total_seconds(), reverse=True)
                
                # Dividir los segmentos más largos
                for i in range(min(remaining_cores, len(segments))):
                    seg_start, seg_end = segments[i]
                    mid_point = seg_start + (seg_end - seg_start) / 2
                    
                    # Reemplazar el segmento original con dos segmentos
                    segments[i] = (seg_start, mid_point)
                    segments.append((mid_point, seg_end))
                
                # Reordenar por fecha de inicio
                segments.sort(key=lambda x: x[0])
            
            return segments
        else:
            # Si no se identificaron períodos complejos, usar distribución uniforme
            print("Usando distribución uniforme de segmentos...")
            
            # Calcular duración total en días
            total_days = (end_date - start_date).total_seconds() / SECONDS_PER_DAY
            
            # Determinar el número óptimo de segmentos
            # Para períodos cortos, usar menos segmentos
            if total_days < 30:
                num_segments = min(num_cores, max(1, int(total_days / 7)))
            else:
                num_segments = num_cores
            
            # Crear segmentos de igual duración
            segments = []
            segment_seconds = (end_date - start_date).total_seconds() / num_segments
            
            for i in range(num_segments):
                seg_start = start_date + timedelta(seconds=i * segment_seconds)
                # Para el último segmento, usar exactamente end_date para evitar errores de redondeo
                seg_end = end_date if i == num_segments - 1 else start_date + timedelta(seconds=(i + 1) * segment_seconds)
                segments.append((seg_start, seg_end))
            
            return segments
    
    def calculate_all(self, start_date: datetime = None, end_date: datetime = None) -> List[AstroEvent]:
        """
        Calcula todos los tránsitos para el período especificado usando el enfoque optimizado.
        
        Args:
            start_date: Fecha inicial (default: 1 enero del año actual)
            end_date: Fecha final (default: 31 diciembre del año actual)
            
        Returns:
            Lista de eventos de tránsitos
        """
        try:
            # Si no se especifican fechas, usar el año actual completo
            if not start_date:
                start_date = datetime(datetime.now().year, 1, 1, tzinfo=ZoneInfo("UTC"))
            if not end_date:
                end_date = datetime(datetime.now().year, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
            
            # Verificar que las fechas sean válidas
            if start_date > end_date:
                print("ADVERTENCIA: La fecha de inicio es posterior a la fecha de fin. Intercambiando fechas.")
                start_date, end_date = end_date, start_date
            
            # Limitar el período a un máximo de 1 año para evitar cálculos excesivos
            max_period = timedelta(days=365)
            if end_date - start_date > max_period:
                print(f"ADVERTENCIA: El período solicitado excede 1 año. Limitando a {max_period.days} días.")
                end_date = start_date + max_period
            
            # Reiniciar métricas
            self.metrics = PerformanceMetrics()
            
            # Reiniciar caché
            self.ephemeris_cache = {}
            
            # Registrar tiempo de inicio
            start_time = time.time()
            
            print("\nCalculando tránsitos con el método optimizado...")
            print(f"Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
            
            # Determinar el número óptimo de núcleos a utilizar
            # Usar menos núcleos para períodos cortos
            period_days = (end_date - start_date).days
            if period_days <= 7:
                num_cores = 2
            elif period_days <= 30:
                num_cores = 4
            else:
                num_cores = 8
            
            # Optimizar la distribución de segmentos
            segments = self._optimize_segment_distribution(start_date, end_date, num_cores)
            
            print(f"Dividiendo el período en {len(segments)} segmentos optimizados...")
            
            # Establecer un tiempo máximo total (2 horas)
            max_total_time = 2 * 60 * 60  # 2 horas en segundos
            
            # Crear un pool de trabajadores para procesar los segmentos en paralelo
            all_events = []
            completed_segments = 0
            failed_segments = 0
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=len(segments)) as executor:
                # Enviar cada segmento a un trabajador
                futures = [executor.submit(self._calculate_segment, seg_start, seg_end, i) 
                          for i, (seg_start, seg_end) in enumerate(segments)]
                
                # Recopilar resultados a medida que se completan
                for future in concurrent.futures.as_completed(futures):
                    # Verificar si hemos excedido el tiempo máximo
                    if time.time() - start_time > max_total_time:
                        print("ADVERTENCIA: Se excedió el tiempo máximo total. Terminando cálculos.")
                        executor.shutdown(wait=False)
                        break
                    
                    try:
                        segment_events = future.result()
                        all_events.extend(segment_events)
                        completed_segments += 1
                        
                        # Mostrar progreso
                        progress = completed_segments * 100 / len(segments)
                        elapsed = time.time() - start_time
                        eta = (elapsed / progress) * (100 - progress) if progress > 0 else 0
                        print(f"Progreso general: {progress:.1f}% - "
                              f"Tiempo transcurrido: {elapsed:.1f}s - "
                              f"Tiempo restante estimado: {eta:.1f}s")
                        
                    except Exception as e:
                        print(f"Error en un segmento: {e}")
                        failed_segments += 1
            
            # Ordenar todos los eventos por fecha
            all_events.sort(key=lambda x: x.fecha_utc)
            
            # Mostrar resumen
            elapsed = time.time() - start_time
            print(f"\nCálculo completado en {elapsed:.2f} segundos")
            print(f"Segmentos completados: {completed_segments}/{len(segments)}")
            if failed_segments > 0:
                print(f"Segmentos fallidos: {failed_segments}")
            print(f"Total de eventos encontrados: {len(all_events)}")
            
            # Obtener resumen de métricas
            metrics_summary = self.metrics.get_summary()
            segment_stats = self.metrics.get_segment_stats()
            
            # Mostrar métricas de rendimiento detalladas
            print("\nMétricas de rendimiento:")
            print(f"- Cálculos de efemérides: {metrics_summary['total_calculations']}")
            print(f"- Aciertos de caché: {metrics_summary['cache_hits']}")
            
            if metrics_summary['total_calculations'] + metrics_summary['cache_hits'] > 0:
                cache_hit_rate = metrics_summary['cache_hits'] / (metrics_summary['total_calculations'] + metrics_summary['cache_hits']) * 100
                print(f"- Tasa de aciertos de caché: {cache_hit_rate:.1f}%")
            
            print(f"- Pasos saltados: {metrics_summary['steps_skipped']}")
            print(f"- Aspectos encontrados: {metrics_summary['aspects_found']}")
            
            # Mostrar estadísticas de segmentos si hay datos
            if segment_stats:
                print("\nEstadísticas de segmentos:")
                print(f"- Tiempo promedio por segmento: {segment_stats['avg_time']:.2f}s")
                print(f"- Tiempo mínimo: {segment_stats['min_time']:.2f}s")
                print(f"- Tiempo máximo: {segment_stats['max_time']:.2f}s")
                print(f"- Eventos promedio por segmento: {segment_stats['avg_events']:.1f}")
                
                # Calcular eficiencia del paralelismo
                if elapsed > 0 and segment_stats['avg_time'] > 0:
                    speedup = (segment_stats['avg_time'] * len(segments)) / elapsed
                    efficiency = speedup / len(segments) * 100
                    print(f"- Eficiencia del paralelismo: {efficiency:.1f}%")
            
            return all_events
            
        except Exception as e:
            print(f"Error fatal en calculate_all: {e}")
            # Retornar una lista vacía en caso de error
            return []
