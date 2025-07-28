"""
Módulo para calcular tránsitos planetarios usando un enfoque astronómico avanzado (v3.0).
Esta implementación extiende la versión 2.0 con mejoras específicas para la detección
y preservación de eventos estacionarios.
"""
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.core import config
from src.core.base_event import AstroEvent
from src.core.constants import EventType, AstronomicalConstants
import immanuel.charts as charts
from immanuel.const import chart, calc
from immanuel.setup import settings
from immanuel.reports import aspect
from immanuel.tools import ephemeris, date
import numpy as np

# Configuración de immanuel para aspectos
settings.aspects = [calc.CONJUNCTION, calc.OPPOSITION, calc.SQUARE]
settings.default_orb = 3.0  # Aumentado a 3° para capturar más aspectos (especialmente conjunciones)
settings.exact_orb = 0.001  # Tolerancia para aspecto exacto

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

# Períodos orbitales aproximados en días
ORBITAL_PERIODS = {
    chart.SUN: 365.25,  # Movimiento aparente del Sol visto desde la Tierra
    chart.MOON: 27.32,  # Período sideral
    chart.MERCURY: 87.97,
    chart.VENUS: 224.7,
    chart.MARS: 686.98,
    chart.JUPITER: 4332.59,
    chart.SATURN: 10759.22,
    chart.URANUS: 30688.5,
    chart.NEPTUNE: 60182,
    chart.PLUTO: 90560
}

# Velocidad media de movimiento en grados por día
AVERAGE_SPEED = {planet: 360 / period for planet, period in ORBITAL_PERIODS.items()}

# Mapeo de aspectos
ASPECT_ANGLES = {
    calc.CONJUNCTION: 0,
    calc.OPPOSITION: 180,
    calc.SQUARE: 90
}

ASPECT_NAMES = {
    calc.CONJUNCTION: "Conjunción",
    calc.OPPOSITION: "Oposición",
    calc.SQUARE: "Cuadratura"
}

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

class AstronomicalTransitsCalculatorV3:
    """
    Versión 3.0 del calculador de tránsitos astronómico.
    Extiende la versión 2.0 con mejoras específicas para la detección
    y preservación de eventos estacionarios.
    """
    
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de tránsitos astronómico v3.0.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
        """
        self.natal_data = natal_data
        
        # Obtener la zona horaria del usuario desde los datos natales
        self.user_timezone = ZoneInfo("UTC")  # Default a UTC
        if 'location' in natal_data and 'timezone' in natal_data['location']:
            try:
                self.user_timezone = ZoneInfo(natal_data['location']['timezone'])
            except Exception:
                # Si hay un error al obtener la zona horaria, usar UTC
                print(f"Error al obtener zona horaria {natal_data['location']['timezone']}, usando UTC")
        
        # Crear diccionario de posiciones natales (planetas)
        self.natal_positions = {}
        for planet_name, data in natal_data['points'].items():
            if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                             'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                self.natal_positions[getattr(chart, planet_name.upper())] = data['longitude']
        
        # Agregar ángulos natales (ASC, MC, DESC, IC) si están disponibles
        if 'angles' in natal_data:
            if 'ASC' in natal_data['angles'] and 'longitude' in natal_data['angles']['ASC']:
                self.natal_positions['ASC'] = natal_data['angles']['ASC']['longitude']
                self.natal_positions['DESC'] = (natal_data['angles']['ASC']['longitude'] + 180) % 360
            if 'MC' in natal_data['angles'] and 'longitude' in natal_data['angles']['MC']:
                self.natal_positions['MC'] = natal_data['angles']['MC']['longitude']
                self.natal_positions['IC'] = (natal_data['angles']['MC']['longitude'] + 180) % 360
    
    @staticmethod
    def datetime_to_jd(dt: datetime) -> float:
        """Convierte un objeto datetime a fecha juliana."""
        return date.to_jd(dt)
    
    def normalize_angle_diff(self, angle1, angle2):
        """
        Normaliza la diferencia entre dos ángulos al rango [-180, 180].
        Esto asegura que siempre se use el camino más corto entre dos ángulos.
        """
        # Asegurar que ambos ángulos estén en el rango [0, 360)
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        # Calcular la diferencia directa
        diff = (a1 - a2) % 360
        
        # Ajustar para obtener el camino más corto
        if diff > 180:
            diff -= 360
            
        return diff
    
    def get_planet_speed_category(self, planet_id, date):
        """
        Determina la categoría de velocidad de un planeta en una fecha específica.
        
        Args:
            planet_id: ID del planeta
            date: Fecha a verificar
            
        Returns:
            Categoría de velocidad: 'very_fast', 'fast', 'medium', 'slow', 'very_slow'
        """
        jd = self.datetime_to_jd(date)
        planet_data = ephemeris.planet(planet_id, jd)
        speed = abs(planet_data['speed'])
        
        # Velocidades típicas (grados/día)
        if speed > 1.0:
            return 'very_fast'  # Mercurio, Luna
        elif speed > 0.5:
            return 'fast'       # Venus
        elif speed > 0.1:
            return 'medium'     # Marte, Sol
        elif speed > 0.02:
            return 'slow'       # Júpiter, Saturno
        else:
            return 'very_slow'  # Urano, Neptuno, Plutón
    
    def find_exact_aspect_time(self, planet_id, natal_position, aspect_angle, start_jd, end_jd, max_iterations=20):
        """
        Implementa búsqueda binaria para encontrar el momento exacto de un aspecto.
        
        Args:
            planet_id: ID del planeta transitante
            natal_position: Posición natal en grados
            aspect_angle: Ángulo del aspecto (0 para conjunción, 180 para oposición, etc.)
            start_jd: Fecha juliana de inicio para la búsqueda
            end_jd: Fecha juliana de fin para la búsqueda
            max_iterations: Número máximo de iteraciones para convergencia
            
        Returns:
            Fecha juliana del aspecto exacto, o None si no se encuentra
        """
        # Calcular la posición objetivo
        target_position = (natal_position + aspect_angle) % 360
        
        # Iteraciones para convergencia
        for iteration in range(max_iterations):
            # Obtener posiciones en ambos extremos
            data1 = ephemeris.planet(planet_id, start_jd)
            data2 = ephemeris.planet(planet_id, end_jd)
            
            # Calcular diferencias angulares
            diff1 = self.normalize_angle_diff(target_position, data1['lon'])
            diff2 = self.normalize_angle_diff(target_position, data2['lon'])
            
            # Si las diferencias son muy pequeñas, ya encontramos el punto
            if abs(diff1) <= settings.exact_orb:
                return start_jd
            if abs(diff2) <= settings.exact_orb:
                return end_jd
            
            # Si las diferencias tienen signos opuestos, hay un cruce en el intervalo
            if diff1 * diff2 <= 0:
                # Punto medio (búsqueda binaria)
                mid_jd = (start_jd + end_jd) / 2
                
                # Si el intervalo es muy pequeño, hemos convergido
                if abs(end_jd - start_jd) < 0.0001:  # ~8.6 segundos
                    return mid_jd
                
                # Obtener posición en el punto medio
                mid_data = ephemeris.planet(planet_id, mid_jd)
                mid_diff = self.normalize_angle_diff(target_position, mid_data['lon'])
                
                # Actualizar intervalo para siguiente iteración
                if diff1 * mid_diff <= 0:
                    end_jd = mid_jd
                else:
                    start_jd = mid_jd
            else:
                # No hay aspecto exacto en este intervalo
                return None
        
        # Si no convergió, devolver None
        return None
    
    def get_adaptive_sampling_interval(self, planet_id, aspect_type, date, last_speed=None):
        """
        Determina el intervalo óptimo de muestreo basado en características astronómicas.
        
        Args:
            planet_id: ID del planeta transitante
            aspect_type: Tipo de aspecto
            date: Fecha actual
            last_speed: Velocidad anterior del planeta (opcional)
            
        Returns:
            Intervalo de tiempo (timedelta) para el muestreo
        """
        # Obtener datos actuales del planeta
        jd = self.datetime_to_jd(date)
        planet_data = ephemeris.planet(planet_id, jd)
        current_speed = abs(planet_data['speed'])
        
        # Velocidad típica para este planeta
        typical_speed = AVERAGE_SPEED.get(planet_id, 1.0)
        
        # Factor base según el planeta (horas)
        if planet_id == chart.MOON:
            base_hours = 1  # Luna: cada 1 hora (más denso debido a su rápido movimiento)
        elif planet_id == chart.MERCURY:
            base_hours = 4  # Mercurio: cada 4 horas
        elif planet_id == chart.VENUS:
            base_hours = 6  # Venus: cada 6 horas
        elif planet_id in [chart.MARS, chart.JUPITER]:
            base_hours = 12  # Marte/Júpiter: cada 12 horas
        else:
            base_hours = 24  # Planetas lentos: cada 24 horas
        
        # Ajuste por tipo de aspecto - Más agresivo para cuadraturas, conjunciones y oposiciones
        if aspect_type == calc.SQUARE:
            if planet_id in [chart.MERCURY, chart.VENUS]:
                aspect_factor = 0.25  # 4x más denso para Mercurio y Venus
            elif planet_id in [chart.MARS, chart.JUPITER]:
                aspect_factor = 0.33  # 3x más denso para Marte y Júpiter
            else:
                aspect_factor = 0.5  # 2x más denso para otros
        elif aspect_type == calc.CONJUNCTION:
            if planet_id in [chart.MERCURY, chart.VENUS, chart.MARS]:
                aspect_factor = 0.5  # 2x más denso para conjunciones de planetas rápidos y medios
            else:
                aspect_factor = 0.75  # 1.33x más denso para conjunciones de otros planetas
        elif aspect_type == calc.OPPOSITION:
            if planet_id in [chart.MERCURY, chart.VENUS, chart.MARS]:
                aspect_factor = 0.5  # 2x más denso para oposiciones de planetas rápidos y medios
            else:
                aspect_factor = 0.75  # 1.33x más denso para oposiciones de otros planetas
        else:
            aspect_factor = 1.0
        
        # Ajuste por velocidad actual
        # Más lento = muestreo más denso
        speed_ratio = current_speed / typical_speed if typical_speed > 0 else 1.0
        
        if speed_ratio < 0.1:  # Muy lento (cerca de estacionamiento)
            speed_factor = 0.1  # 10x más denso
        elif speed_ratio < 0.3:
            speed_factor = 0.3  # 3x más denso
        elif speed_ratio < 0.7:
            speed_factor = 0.7  # Ligeramente más denso
        else:
            speed_factor = 1.0
        
        # Ajuste adicional si hay cambio significativo de velocidad
        acceleration_factor = 1.0
        if last_speed is not None:
            speed_change = abs(current_speed - last_speed) / typical_speed
            if speed_change > 0.05:  # Cambio significativo
                acceleration_factor = 0.5  # 2x más denso
        
        # Calcular horas finales
        hours = max(1, base_hours * aspect_factor * speed_factor * acceleration_factor)
        
        return timedelta(hours=hours)
    
    def get_universal_dynamic_orb(self, planet_id, natal_id, aspect_type):
        """
        Calcula un orbe dinámico basado en principios astronómicos universales.
        
        Args:
            planet_id: ID del planeta transitante
            natal_id: ID del planeta o punto natal
            aspect_type: Tipo de aspecto
            
        Returns:
            Orbe dinámico en grados
        """
        # Orbe base según configuración
        base_orb = settings.default_orb  # Normalmente 2.0°
        
        # 1. Ajuste por tipo de aspecto
        if aspect_type == calc.CONJUNCTION:
            aspect_factor = 1.2  # 20% más para conjunciones
        elif aspect_type == calc.OPPOSITION:
            aspect_factor = 1.5  # 50% más para oposiciones (aumentado de 1.2)
        elif aspect_type == calc.SQUARE:
            # Aumentar significativamente para cuadraturas de planetas lentos
            if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                aspect_factor = 2.0  # 100% más (4° base) para planetas lentos
            elif planet_id in [chart.MERCURY, chart.VENUS]:
                aspect_factor = 1.5  # 50% más para planetas rápidos
            else:
                aspect_factor = 1.3  # 30% más para otros
        else:
            aspect_factor = 1.0
        
        # 2. Ajuste por planeta transitante
        transit_factor = 1.0
        if planet_id == chart.MERCURY:
            transit_factor = 1.3  # 30% más para Mercurio
        elif planet_id == chart.VENUS:
            transit_factor = 1.2  # 20% más para Venus
        elif planet_id in [chart.MARS, chart.JUPITER]:
            transit_factor = 1.1  # 10% más para Marte/Júpiter
        
        # 3. Ajuste por planeta natal
        natal_factor = 1.0
        if isinstance(natal_id, int):  # Es un planeta (no un ángulo)
            if natal_id in [chart.SUN, chart.MOON]:
                natal_factor = 1.2  # 20% más para luminarias natales
            elif natal_id in [chart.MERCURY, chart.VENUS]:
                natal_factor = 1.1  # 10% más para planetas personales
        else:  # Es un ángulo (ASC, MC, etc.)
            if natal_id in ['ASC', 'DESC']:
                natal_factor = 1.2  # 20% más para aspectos al Ascendente/Descendente
            elif natal_id in ['MC', 'IC']:
                natal_factor = 1.15  # 15% más para aspectos al MC/IC
        
        # 4. Ajuste por combinaciones específicas
        combo_factor = 1.0
        
        # Combinaciones de planetas rápidos con lentos (difíciles de detectar)
        if planet_id in [chart.MERCURY, chart.VENUS] and \
           isinstance(natal_id, int) and natal_id in [chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
            combo_factor = 1.5  # 50% más (aumentado de 1.2)
        
        # Combinaciones de planetas medios con personales
        elif planet_id in [chart.MARS, chart.JUPITER] and \
             isinstance(natal_id, int) and natal_id in [chart.MERCURY, chart.VENUS, chart.MARS]:
            combo_factor = 1.3  # 30% más (aumentado de 1.15)
            
        # Combinaciones específicas que son difíciles de detectar
        # Júpiter cuadratura Urano/Plutón (mencionados como faltantes)
        elif planet_id == chart.JUPITER and \
             isinstance(natal_id, int) and natal_id in [chart.URANUS, chart.PLUTO] and \
             aspect_type == calc.SQUARE:
            combo_factor = 1.8  # 80% más
            
        # Marte cuadratura Neptuno/Venus/Mercurio (mencionados como faltantes)
        elif planet_id == chart.MARS and \
             isinstance(natal_id, int) and natal_id in [chart.NEPTUNE, chart.VENUS, chart.MERCURY] and \
             aspect_type == calc.SQUARE:
            combo_factor = 1.8  # 80% más
            
        # Venus cuadratura Urano/Plutón/Marte/Luna/Neptuno/Saturno (mencionados como faltantes)
        elif planet_id == chart.VENUS and \
             isinstance(natal_id, int) and natal_id in [chart.URANUS, chart.PLUTO, chart.MARS, chart.MOON, chart.NEPTUNE, chart.SATURN] and \
             aspect_type == calc.SQUARE:
            combo_factor = 1.8  # 80% más
        
        # Calcular orbe final
        return base_orb * aspect_factor * transit_factor * natal_factor * combo_factor
    
    def is_challenging_combination(self, planet_id, natal_id, aspect_type):
        """
        Determina si una combinación es potencialmente difícil de detectar
        basado en principios astronómicos generales.
        
        Args:
            planet_id: ID del planeta transitante
            natal_id: ID del planeta o punto natal
            aspect_type: Tipo de aspecto
            
        Returns:
            Boolean indicando si la combinación necesita verificación adicional
        """
        # Cualquier aspecto con la Luna (transitante o natal) necesita verificación adicional
        if planet_id == chart.MOON or (isinstance(natal_id, int) and natal_id == chart.MOON):
            return True
            
        # Cualquier aspecto con Saturno (transitante o natal) necesita verificación adicional
        if planet_id == chart.SATURN or (isinstance(natal_id, int) and natal_id == chart.SATURN):
            return True
            
        # Cualquier aspecto principal con el Sol natal necesita verificación adicional
        if isinstance(natal_id, int) and natal_id == chart.SUN and aspect_type in [calc.CONJUNCTION, calc.OPPOSITION, calc.SQUARE]:
            return True
            
        # Verificar cuadraturas
        if aspect_type == calc.SQUARE:
            # 1. Planetas rápidos en tránsito (pueden pasar rápidamente por el aspecto)
            if planet_id in [chart.MERCURY, chart.VENUS]:
                return True
            
            # 2. Planetas lentos en tránsito con aspectos a planetas personales
            if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO] and \
               isinstance(natal_id, int) and natal_id in [chart.SUN, chart.MOON, chart.MERCURY, chart.VENUS, chart.MARS]:
                return True
            
            # 3. Planetas medios (Marte, Júpiter) en tránsito
            if planet_id in [chart.MARS, chart.JUPITER]:
                return True
            
            # 4. Cualquier cuadratura a luminarias (Sol, Luna)
            if isinstance(natal_id, int) and natal_id in [chart.SUN, chart.MOON]:
                return True
                
            # 5. Cualquier cuadratura a Neptuno
            if isinstance(natal_id, int) and natal_id == chart.NEPTUNE:
                return True
        
        # Verificar conjunciones
        elif aspect_type == calc.CONJUNCTION:
            # 1. Conjunciones de Venus con cualquier planeta
            if planet_id == chart.VENUS:
                return True
                
            # 2. Conjunciones de Marte con planetas exteriores
            if planet_id == chart.MARS and \
               isinstance(natal_id, int) and natal_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                return True
                
            # 3. Conjunciones de planetas rápidos
            if planet_id in [chart.MERCURY, chart.VENUS, chart.MARS] and \
               isinstance(natal_id, int) and natal_id in [chart.MERCURY, chart.VENUS, chart.MARS]:
                return True
                
            # 4. Conjunciones con luminarias
            if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO] and \
               isinstance(natal_id, int) and natal_id in [chart.SUN, chart.MOON]:
                return True
                
            # 5. Cualquier conjunción con Neptuno
            if planet_id == chart.NEPTUNE or (isinstance(natal_id, int) and natal_id == chart.NEPTUNE):
                return True
                
            # 6. Mercurio con cualquier planeta exterior
            if planet_id == chart.MERCURY and \
               isinstance(natal_id, int) and natal_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                return True
        
        # Verificar oposiciones
        elif aspect_type == calc.OPPOSITION:
            # 1. Oposiciones de planetas rápidos (pueden pasar rápidamente por el aspecto)
            if planet_id in [chart.MERCURY, chart.VENUS]:
                return True
                
            # 2. Oposiciones con luminarias (Sol, Luna)
            if isinstance(natal_id, int) and natal_id in [chart.SUN, chart.MOON]:
                return True
                
            # 3. Oposiciones de planetas lentos a planetas personales
            if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO] and \
               isinstance(natal_id, int) and natal_id in [chart.MERCURY, chart.VENUS, chart.MARS]:
                return True
                
            # 4. Marte en oposición a cualquier planeta
            if planet_id == chart.MARS:
                return True
                
            # 5. Cualquier oposición a Júpiter
            if isinstance(natal_id, int) and natal_id == chart.JUPITER:
                return True
        
        return False
    
    def detect_direction_changes(self, planet_id, start_date, end_date):
        """
        Detecta cambios de dirección (estacionamientos) de un planeta.
        
        Args:
            planet_id: ID del planeta
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de fechas (datetime) donde ocurren cambios de dirección
        """
        direction_changes = []
        
        # La Luna siempre se mueve en dirección directa, nunca retrógrada
        if planet_id == chart.MOON:
            return []
        
        # Determinar intervalo de verificación según el planeta
        if planet_id in [chart.MERCURY, chart.VENUS]:
            check_interval = timedelta(days=3)  # Cada 3 días para planetas rápidos
        elif planet_id in [chart.MARS, chart.JUPITER]:
            check_interval = timedelta(days=5)  # Cada 5 días para planetas medios
        else:
            check_interval = timedelta(days=10)  # Cada 10 días para planetas lentos
        
        # Verificar cambios de dirección
        current = start_date
        prev_speed = None
        
        while current <= end_date:
            jd = self.datetime_to_jd(current)
            planet_data = ephemeris.planet(planet_id, jd)
            current_speed = planet_data['speed']
            
            # Si tenemos velocidad previa, verificar cambio de signo
            if prev_speed is not None:
                if (prev_speed > 0 and current_speed <= 0) or (prev_speed <= 0 and current_speed > 0):
                    # Cambio de dirección detectado
                    # Refinar para encontrar el momento exacto
                    change_date = self.refine_direction_change(
                        planet_id, 
                        current - check_interval, 
                        current
                    )
                    if change_date:
                        direction_changes.append(change_date)
            
            prev_speed = current_speed
            current += check_interval
        
        return direction_changes
    
    def refine_direction_change(self, planet_id, start_date, end_date, max_iterations=10):
        """
        Refina el momento exacto de un cambio de dirección mediante búsqueda binaria.
        
        Args:
            planet_id: ID del planeta
            start_date: Fecha de inicio (antes del cambio)
            end_date: Fecha de fin (después del cambio)
            max_iterations: Número máximo de iteraciones
            
        Returns:
            Fecha (datetime) del cambio de dirección
        """
        start_jd = self.datetime_to_jd(start_date)
        end_jd = self.datetime_to_jd(end_date)
        
        # Obtener velocidades iniciales
        start_data = ephemeris.planet(planet_id, start_jd)
        end_data = ephemeris.planet(planet_id, end_jd)
        
        start_speed = start_data['speed']
        end_speed = end_data['speed']
        
        # Verificar que hay un cambio de dirección
        if (start_speed > 0 and end_speed > 0) or (start_speed < 0 and end_speed < 0):
            # No hay cambio de dirección
            return None
        
        # Buscar el punto donde la velocidad es cercana a cero
        for _ in range(max_iterations):
            # Punto medio
            mid_jd = (start_jd + end_jd) / 2
            mid_data = ephemeris.planet(planet_id, mid_jd)
            mid_speed = mid_data['speed']
            
            # Si la velocidad es muy cercana a cero, hemos encontrado el estacionamiento
            if abs(mid_speed) < 0.0001:
                dt = date.to_datetime(mid_jd)
                return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(self.user_timezone)
            
            # Actualizar intervalo de búsqueda
            if (start_speed > 0 and mid_speed < 0) or (start_speed < 0 and mid_speed > 0):
                end_jd = mid_jd
                end_speed = mid_speed
            else:
                start_jd = mid_jd
                start_speed = mid_speed
            
            # Si el intervalo es muy pequeño, hemos convergido
            if abs(end_jd - start_jd) < 0.01:  # ~15 minutos
                dt = date.to_datetime(mid_jd)
                return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(self.user_timezone)
        
        # Si no convergió, devolver el punto medio
        dt = date.to_datetime((start_jd + end_jd) / 2)
        return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(self.user_timezone)
    
    def add_critical_period_sampling(self, planet_id, direction_changes, all_dates, target_position):
        """
        Añade muestreo ultra-denso alrededor de períodos críticos.
        
        Args:
            planet_id: ID del planeta
            direction_changes: Lista de fechas de cambios de dirección
            all_dates: Lista actual de fechas de muestreo
            target_position: Posición objetivo
            
        Returns:
            Lista ampliada de fechas de muestreo
        """
        extra_dates = []
        
        # Para cada cambio de dirección
        for change_date in direction_changes:
            # Determinar ventana alrededor del cambio
            if planet_id == chart.MOON:
                window = timedelta(days=2)  # ±2 días para la Luna
                interval = timedelta(minutes=15)  # Cada 15 minutos (más denso)
            elif planet_id in [chart.MERCURY, chart.VENUS]:
                window = timedelta(days=5)  # ±5 días para planetas rápidos
                interval = timedelta(minutes=30)  # Cada 30 minutos
            elif planet_id in [chart.MARS, chart.JUPITER]:
                window = timedelta(days=7)  # ±7 días para planetas medios
                interval = timedelta(hours=1)  # Cada hora
            else:
                window = timedelta(days=10)  # ±10 días para planetas lentos
                interval = timedelta(hours=2)  # Cada 2 horas
            
            # Añadir fechas en la ventana
            current = change_date - window
            end = change_date + window
            
            while current <= end:
                extra_dates.append((current, target_position))
                current += interval
        
        # Combinar con fechas existentes
        all_dates.extend(extra_dates)
        
        return all_dates
    
    def check_aspect_at_date(self, planet_id, check_date, target_position, natal_id=None, aspect_type=None):
        """
        Verifica si un planeta forma un aspecto en una fecha específica.
        Versión mejorada que utiliza orbes dinámicos universales.
        
        Args:
            planet_id: ID del planeta transitante
            check_date: Fecha a verificar
            target_position: Posición objetivo en grados
            natal_id: ID del planeta natal (opcional, para orbes dinámicos)
            aspect_type: Tipo de aspecto (opcional, para orbes dinámicos)
            
        Returns:
            Tupla (es_aspecto, fecha_exacta, posición, velocidad, orbe, movimiento, estado)
        """
        jd = self.datetime_to_jd(check_date)
        planet_data = ephemeris.planet(planet_id, jd)
        position = planet_data['lon']
        speed = planet_data['speed']
        
        # Calcular la diferencia angular
        diff = self.normalize_angle_diff(target_position, position)
        orb = abs(diff)
        
        # Determinar el orbe máximo permitido
        max_orb = settings.default_orb
        if natal_id is not None and aspect_type is not None:
            max_orb = self.get_universal_dynamic_orb(planet_id, natal_id, aspect_type)
        
        # Verificar si está dentro del orbe permitido
        if orb <= max_orb:
            # Si está cerca, usar búsqueda binaria para encontrar el momento exacto
            if orb > settings.exact_orb:
                # Buscar el momento exacto en un intervalo de ±1 día
                exact_jd = self.find_exact_aspect_time(
                    planet_id, 
                    (target_position - aspect_type) % 360,  # Posición natal
                    aspect_type,
                    jd - 1,  # 1 día antes
                    jd + 1   # 1 día después
                )
                
                if exact_jd:
                    # Actualizar a la fecha exacta
                    exact_date = date.to_datetime(exact_jd)
                    # Convertir a la zona horaria del usuario - asegurar que se aplica correctamente
                    if exact_date.tzinfo is None:
                        exact_date = exact_date.replace(tzinfo=ZoneInfo("UTC"))
                    # Aplicar la zona horaria del usuario
                    exact_date = exact_date.astimezone(self.user_timezone)
                    
                    # Obtener datos exactos del planeta
                    exact_data = ephemeris.planet(planet_id, exact_jd)
                    position = exact_data['lon']
                    speed = exact_data['speed']
                    orb = abs(self.normalize_angle_diff(target_position, position))
                    check_date = exact_date
            
            # Determinar si el aspecto es aplicativo o separativo
            is_applying = False
            
            # Si el planeta se mueve directo
            if speed > 0:
                # Calcular la dirección más corta hacia el objetivo
                direction_to_target = self.normalize_angle_diff(target_position, position)
                is_applying = (direction_to_target > 0)
            else:
                # Si el planeta se mueve retrógrado
                direction_to_target = self.normalize_angle_diff(target_position, position)
                is_applying = (direction_to_target < 0)
            
            # Si la velocidad es muy baja, considerar estacionario
            if abs(speed) <= 0.0001:
                # Para planetas estacionarios, verificar la tendencia
                # Obtener posición un día antes
                prev_date = check_date - timedelta(days=1)
                prev_jd = self.datetime_to_jd(prev_date)
                prev_data = ephemeris.planet(planet_id, prev_jd)
                prev_position = prev_data['lon']
                
                # Calcular la dirección del movimiento reciente
                recent_direction = self.normalize_angle_diff(position, prev_position)
                
                # Si se está moviendo hacia el aspecto, es aplicativo
                is_applying = (recent_direction > 0 and direction_to_target > 0) or (recent_direction < 0 and direction_to_target < 0)
            
            aspect_state = calc.APPLICATIVE if is_applying else calc.SEPARATIVE
            
            # Si el orbe es muy pequeño, considerar el aspecto exacto
            if orb <= settings.exact_orb:
                aspect_state = calc.EXACT
            
            # Determinar el movimiento
            if abs(speed) <= 0.0001:  # Casi estacionario
                movement = calc.STATIONARY
            else:
                movement = calc.DIRECT if speed > 0 else calc.RETROGRADE
            
            return True, check_date, position, speed, orb, movement, aspect_state
        
        return False, None, position, speed, orb, None, None
    
    def estimate_transit_dates(self, planet_id, natal_position, aspect_angle, year, start_date=None, end_date=None):
        """
        Estima las fechas en que un planeta transitará por una posición específica.
        Versión mejorada con muestreo adaptativo.
        
        Args:
            planet_id: ID del planeta transitante
            natal_position: Posición natal en grados
            aspect_angle: Ángulo del aspecto (0 para conjunción, 180 para oposición, etc.)
            year: Año para el cálculo
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Lista de fechas estimadas
        """
        # Usar la zona horaria del usuario para las fechas por defecto
        if start_date is None:
            start_date = datetime(year, 1, 1, tzinfo=self.user_timezone)
        if end_date is None:
            end_date = datetime(year, 12, 31, 23, 59, tzinfo=self.user_timezone)
        
        # Calcular la posición objetivo
        target_position = (natal_position + aspect_angle) % 360
        
        # Para cuadraturas y oposiciones, hay dos posiciones posibles
        target_positions = [target_position]
        if aspect_angle == 90:
            target_positions.append((natal_position - 90) % 360)
        elif aspect_angle == 180:
            target_positions.append((natal_position - 180) % 360)  # Añadir posición alternativa para oposiciones
        
        # Obtener la posición inicial del planeta
        jd_start = self.datetime_to_jd(start_date)
        planet_data = ephemeris.planet(planet_id, jd_start)
        initial_position = planet_data['lon']
        initial_speed = planet_data['speed']
        
        # Verificar si el planeta está retrógrado al inicio
        is_retrograde_initial = initial_speed < 0
        
        estimated_dates = []
        
        # Calcular el período en días para que el planeta recorra 360°
        period = ORBITAL_PERIODS.get(planet_id, 365.25)  # Usar 365.25 como valor predeterminado
        
        # Calcular cuántos ciclos completos puede hacer el planeta en el período
        days_in_period = (end_date - start_date).total_seconds() / 86400.0
        cycles = max(1, int(days_in_period / period) + 1)
        
        # Ajustar el tamaño de la ventana de estimación basado en:
        # 1. Período orbital (planetas más lentos necesitan ventanas más amplias)
        # 2. Tipo de aspecto (las cuadraturas necesitan más muestreo)
        # 3. Velocidad del planeta (planetas más lentos necesitan más muestreo)
        
        # Factor base para el tamaño de la ventana
        window_base_size = 15  # Aumentado de 10 a 15 días para mejor cobertura
        
        # Factor de ajuste basado en el período orbital
        window_factor = min(1.0, 30 / period)  # Factor de ajuste basado en el período
        
        # Ajuste adicional para cuadraturas (más difíciles de detectar)
        aspect_factor = 2.0 if aspect_angle == 90 else 1.0  # Duplicado para cuadraturas
        
        # Ajuste para planetas lentos (Júpiter, Saturno, etc.)
        planet_speed_factor = 1.0
        if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
            planet_speed_factor = 2.0  # 100% más de muestreo para planetas lentos
        
        # Calcular tamaño final de la ventana
        window_size = int(window_base_size / window_factor * aspect_factor * planet_speed_factor)
        
        # Limitar el tamaño máximo de la ventana
        window_size = min(window_size, 45)  # Aumentado de 30 a 45 para mejor cobertura
        
        # Generar offsets para la ventana de estimación con mayor densidad
        # Reducir el paso para tener más puntos de muestreo
        step_size = max(1, window_size // 16)  # Más denso que el original (window_size // 8)
        offsets = list(range(-window_size, window_size + 1, step_size))
        if 0 not in offsets:
            offsets.append(0)
        offsets.sort()
        
        # Variables para seguimiento de velocidad
        last_speed = None
        last_recalc_date = start_date
        
        # Para cada posición objetivo
        for target_pos in target_positions:
            # Calcular la diferencia angular inicial
            angle_diff = self.normalize_angle_diff(target_pos, initial_position)
            
            # Ajustar el cálculo de días basado en la dirección del movimiento y la velocidad real
            # Usar la velocidad real del planeta en lugar de la velocidad media
            if abs(initial_speed) < 0.0001:  # Si el planeta está casi estacionario
                # Usar la velocidad media como fallback
                days_to_target = abs(angle_diff) / AVERAGE_SPEED[planet_id]
                first_date = start_date + timedelta(days=period / 4)  # Comenzar a 1/4 del período
            elif is_retrograde_initial:
                # Si el planeta está retrógrado, la dirección es opuesta
                days_to_target = abs(angle_diff) / abs(initial_speed)
                # Si el ángulo es positivo, necesitamos ir en dirección negativa (y viceversa)
                first_date = start_date + timedelta(days=days_to_target if angle_diff < 0 else period - days_to_target)
            else:
                # Movimiento directo normal, usar velocidad real
                days_to_target = abs(angle_diff) / abs(initial_speed)
                first_date = start_date + timedelta(days=days_to_target if angle_diff > 0 else period - days_to_target)
            
            # Si la primera fecha está después del final del período, no hay tránsitos
            if first_date > end_date:
                continue
            
            # Ajustar la primera fecha si está antes del inicio
            if first_date < start_date:
                first_date = start_date + timedelta(days=period - (days_to_target % period))
            
            # Generar fechas estimadas para cada ciclo
            current_date = first_date
            for _ in range(cycles):
                if current_date <= end_date:
                    # Obtener intervalo adaptativo
                    sampling_interval = self.get_adaptive_sampling_interval(
                        planet_id, 
                        aspect_angle, 
                        current_date,
                        last_speed
                    )
                    
                    # Añadir fecha actual
                    estimated_dates.append((current_date, target_pos))
                    
                    # Añadir fechas adicionales alrededor de la estimación para mayor precisión
                    for offset in offsets:
                        check_date = current_date + timedelta(days=offset)
                        if start_date <= check_date <= end_date:
                            estimated_dates.append((check_date, target_pos))
                    
                    # Actualizar velocidad cada cierto tiempo
                    days_since_last_recalc = (current_date - last_recalc_date).days
                    recalc_interval = 7  # Valor predeterminado
                    
                    # Ajustar intervalo de recálculo según el planeta
                    if planet_id in [chart.MERCURY, chart.VENUS]:
                        recalc_interval = 3
                    elif planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                        recalc_interval = 10
                    
                    if days_since_last_recalc >= recalc_interval:
                        jd_current = self.datetime_to_jd(current_date)
                        current_data = ephemeris.planet(planet_id, jd_current)
                        last_speed = abs(current_data['speed'])
                        last_recalc_date = current_date
                    
                    # Avanzar al siguiente punto de muestreo
                    current_date += sampling_interval
                else:
                    break
        
        # Para cuadraturas, añadir muestreo adicional para Mercurio
        if aspect_angle == 90 and planet_id == chart.MERCURY:
            extra_dates = []
            current = start_date
            # Para Mercurio, usar muestreo cada 30 minutos
            mercury_interval = timedelta(minutes=30)
            
            while current <= end_date:
                for target_pos in target_positions:
                    extra_dates.append((current, target_pos))
                current += mercury_interval
            
            # Combinar con fechas estimadas
            estimated_dates.extend(extra_dates)
        
        return estimated_dates
        
    def find_transits_for_planet(self, planet_id, year, start_date=None, end_date=None):
        """
        Encuentra todos los tránsitos de un planeta para un año específico.
        Versión mejorada con detección avanzada de cambios de dirección.
        
        Args:
            planet_id: ID del planeta transitante
            year: Año para el cálculo
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            Lista de tránsitos encontrados
        """
        # Usar la zona horaria del usuario para las fechas por defecto
        if start_date is None:
            start_date = datetime(year, 1, 1, tzinfo=self.user_timezone)
        if end_date is None:
            end_date = datetime(year, 12, 31, 23, 59, tzinfo=self.user_timezone)
        
        transits = []
        
        # Detectar cambios de dirección para este planeta
        direction_changes = self.detect_direction_changes(planet_id, start_date, end_date)
        print(f"Detectados {len(direction_changes)} cambios de dirección para {PLANET_NAMES.get(planet_id, planet_id)}")
        
        # Para cada planeta/punto natal
        for natal_id, natal_position in self.natal_positions.items():
            # Para cada tipo de aspecto
            for aspect_type, aspect_angle in ASPECT_ANGLES.items():
                # Verificar si esta es una combinación potencialmente problemática
                needs_extra_verification = self.is_challenging_combination(planet_id, natal_id, aspect_type)
                
                # Estimar fechas de tránsito
                estimated_dates = self.estimate_transit_dates(
                    planet_id, natal_position, aspect_angle, year, start_date, end_date
                )
                
                # Manejar ambas cuadraturas explícitamente
                target_positions = [(natal_position + aspect_angle) % 360]
                if aspect_type == calc.SQUARE:
                    # Asegurar que consideramos ambas cuadraturas (90° y 270°)
                    target_positions = [
                        (natal_position + 90) % 360,  # Cuadratura a 90°
                        (natal_position - 90) % 360   # Cuadratura a 270°
                    ]
                
                # Para cada posición objetivo
                for target_position in target_positions:
                    # Para combinaciones potencialmente problemáticas, añadir verificación adicional
                    if needs_extra_verification:
                        # Determinar la frecuencia de verificación basada en la velocidad del planeta
                        if planet_id == chart.MOON:
                            # Para la Luna, verificar cada 2 horas (mucho más denso)
                            check_interval = timedelta(hours=2)
                        elif planet_id == chart.MERCURY:
                            # Para Mercurio, verificar cada 4 horas (más denso)
                            check_interval = timedelta(hours=4)
                        elif planet_id == chart.VENUS:
                            # Para Venus, verificar cada 8 horas (más denso)
                            check_interval = timedelta(hours=8)
                        elif planet_id in [chart.MARS, chart.JUPITER]:
                            # Para Marte y Júpiter, verificar cada 12 horas (más denso)
                            check_interval = timedelta(hours=12)
                        else:
                            # Para planetas lentos, verificar cada día (más denso)
                            check_interval = timedelta(days=1)
                        
                        # Ajuste adicional para aspectos con la Luna o el Sol
                        if isinstance(natal_id, int) and natal_id in [chart.SUN, chart.MOON]:
                            check_interval = timedelta(hours=max(2, check_interval.total_seconds() / 3600 / 2))
                        
                        # Añadir verificaciones adicionales
                        extra_dates = []
                        current = start_date
                        while current <= end_date:
                            extra_dates.append((current, target_position))
                            current += check_interval
                        
                        # Combinar con fechas estimadas
                        estimated_dates.extend(extra_dates)
                    
                    # Añadir muestreo ultra-denso alrededor de cambios de dirección
                    all_dates = self.add_critical_period_sampling(
                        planet_id, direction_changes, estimated_dates, target_position
                    )
                    
                    # Verificar cada fecha estimada
                    for date, check_position in all_dates:
                        is_aspect, exact_date, position, speed, orb, movement, aspect_state = self.check_aspect_at_date(
                            planet_id, date, target_position, natal_id, aspect_type
                        )
                        
                        if is_aspect:
                            # Añadir el tránsito a la lista, incluyendo la velocidad para filtrado posterior
                            transits.append((
                                exact_date,
                                planet_id,
                                aspect_type,
                                natal_id,
                                movement,
                                aspect_state,
                                orb,
                                position,
                                speed  # Añadir la velocidad para poder filtrar por ella después
                            ))
        
        return transits
        
    def filter_duplicate_transits(self, transit_dates):
        """
        Filtra tránsitos duplicados de manera inteligente.
        Versión 3.0 mejorada que selecciona el momento más exacto para eventos estacionarios.
        
        Args:
            transit_dates: Lista de tuplas (fecha, planeta_id, aspecto, natal_id, movimiento, estado, orbe, posicion, velocidad)
            
        Returns:
            Lista filtrada de tránsitos sin duplicados
        """
        # Paso 1: Filtrar aspectos a puntos que no son planetas o ángulos principales
        valid_transits = []
        for transit in transit_dates:
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position, speed = transit
            
            # Incluir planetas y ángulos principales (ASC, MC)
            if isinstance(natal_id, int) or natal_id in ['ASC', 'MC']:
                valid_transits.append(transit)
        
        # Paso 2: Agrupar eventos estacionarios por día
        # Esto nos permitirá seleccionar solo el evento con la velocidad más cercana a cero
        stationary_groups = {}
        
        # Primero, agrupar todos los eventos estacionarios por planeta, aspecto, natal y fecha
        for transit in valid_transits:
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position, speed = transit
            
            if movement == calc.STATIONARY:
                # Clave para agrupar: (planeta, aspecto, natal, fecha)
                date_key = date.strftime('%Y-%m-%d')  # Solo la fecha, sin hora
                group_key = (planet_id, aspect_type, natal_id, date_key)
                
                if group_key not in stationary_groups:
                    stationary_groups[group_key] = []
                
                stationary_groups[group_key].append(transit)
        
        # Para cada grupo de estacionarios, seleccionar solo el que tiene la velocidad más cercana a cero
        stationary_selected = []
        for group in stationary_groups.values():
            # Ordenar por velocidad absoluta (más cercana a cero primero)
            sorted_group = sorted(group, key=lambda x: abs(x[8]))
            # Seleccionar el evento con la velocidad más cercana a cero
            stationary_selected.append(sorted_group[0])
        
        # Filtrar los eventos estacionarios de la lista original
        non_stationary_transits = [t for t in valid_transits if t[4] != calc.STATIONARY]
        
        # Paso 3: Procesar eventos no estacionarios normalmente
        transit_groups = {}
        
        # Umbrales para aspectos exactos
        exact_threshold_minutes = 10  # Umbral de tiempo para aspectos exactos (10 minutos)
        exact_position_threshold = 0.0167  # 1 minuto de arco
        
        # Ordenar por fecha para procesar cronológicamente
        sorted_transits = sorted(non_stationary_transits, key=lambda x: x[0])
        
        for transit in sorted_transits:
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position, speed = transit
            
            # Clave base
            base_key = (planet_id, natal_id, aspect_type)
            
            # Para aspectos exactos, usar solo fecha; para otros, usar fecha y hora
            if aspect_state == calc.EXACT:
                date_key = date.strftime('%Y-%m-%d')
            else:
                date_key = date.strftime('%Y-%m-%d-%H')
            
            # Determinar umbral de días según velocidad del planeta y tipo de aspecto
            if planet_id in [chart.MERCURY, chart.VENUS]:
                day_threshold = 2.0  # 2 días para planetas rápidos (reducido de 3.0)
            elif planet_id in [chart.MARS, chart.JUPITER]:
                day_threshold = 3.0  # 3 días para planetas medios (reducido de 5.0)
            else:
                day_threshold = 5.0  # 5 días para planetas lentos (reducido de 10.0)
            
            # Ajustar umbral según el tipo de aspecto
            if aspect_type == calc.CONJUNCTION:
                day_threshold *= 1.5  # Aumentar umbral para conjunciones (más permisivo)
            elif aspect_type == calc.OPPOSITION:
                day_threshold *= 1.5  # Aumentar umbral para oposiciones (más permisivo)
            
            # Reducir umbral si los movimientos son diferentes
            if movement == calc.RETROGRADE:
                day_threshold *= 0.5  # Reducir a la mitad para retrógrados
            
            # Umbral de tiempo muy cercano (minutos) para detectar duplicados inmediatos
            minute_threshold = 5  # 5 minutos
            
            # Buscar duplicados temporales
            found_match = False
            
            # Caso especial para aspectos exactos: buscar activamente en el mismo día
            if aspect_state == calc.EXACT:
                # Buscar en el mismo día otros aspectos exactos cercanos
                for key, existing_transit in list(transit_groups.items()):
                    existing_date = existing_transit[0]
                    existing_planet_id = existing_transit[1]
                    existing_natal_id = existing_transit[3]
                    existing_aspect_type = existing_transit[2]
                    existing_movement = existing_transit[4]
                    existing_aspect_state = existing_transit[5]
                    existing_position = existing_transit[7]
                    
                    # Si es la misma combinación planeta-aspecto-planeta y también es exacto
                    if (existing_planet_id == planet_id and 
                        existing_natal_id == natal_id and 
                        existing_aspect_type == aspect_type and
                        existing_aspect_state == calc.EXACT):
                        
                        # Verificar si es el mismo día
                        same_day = (date.year == existing_date.year and 
                                   date.month == existing_date.month and 
                                   date.day == existing_date.day)
                        
                        if same_day:
                            # Verificar proximidad temporal
                            minute_diff = abs((date - existing_date).total_seconds() / 60.0)
                            
                            if minute_diff <= exact_threshold_minutes:
                                # Verificar proximidad posicional
                                position_diff = abs(self.normalize_angle_diff(position, existing_position))
                                
                                if position_diff < exact_position_threshold:
                                    found_match = True
                                    
                                    # Si ambos tienen el mismo orbe, mantener el primero cronológicamente
                                    existing_orb = existing_transit[6]
                                    if orb < existing_orb or (orb == existing_orb and date < existing_date):
                                        transit_groups[key] = transit
                                    
                                    break
            
            # Si no se encontró duplicado en la búsqueda activa para aspectos exactos,
            # continuar con la lógica normal de búsqueda
            if not found_match:
                for key in list(transit_groups.keys()):
                    existing_transit = transit_groups[key]
                    existing_date = existing_transit[0]
                    existing_planet_id, existing_natal_id, existing_aspect_type = existing_transit[1], existing_transit[3], existing_transit[2]
                    existing_movement = existing_transit[4]
                    existing_aspect_state = existing_transit[5]
                    
                    # Si es la misma combinación
                    if (existing_planet_id == planet_id and 
                        existing_natal_id == natal_id and 
                        existing_aspect_type == aspect_type):
                        
                        # Verificar proximidad temporal
                        seconds_diff = abs((date - existing_date).total_seconds())
                        date_diff = seconds_diff / 86400.0  # Diferencia en días
                        minute_diff = seconds_diff / 60.0   # Diferencia en minutos
                        
                        # Si están muy cerca en tiempo (pocos minutos), considerar duplicado inmediato
                        if minute_diff <= minute_threshold:
                            found_match = True
                            
                            # Mantener el de menor orbe
                            existing_orb = existing_transit[6]
                            if orb < existing_orb:
                                transit_groups[key] = transit
                            
                            break
                        # Si están dentro del umbral de días
                        elif date_diff <= day_threshold:
                            found_match = True
                            
                            # Si los movimientos o estados son diferentes, mantener ambos
                            # Esto es importante para capturar aspectos cerca de cambios de dirección
                            if movement != existing_movement or aspect_state != existing_aspect_state:
                                unique_key = base_key + (date_key, movement, aspect_state)
                                transit_groups[unique_key] = transit
                                found_match = False  # Seguir procesando
                                break
                            
                            # Mantener el de menor orbe
                            existing_orb = existing_transit[6]
                            if orb < existing_orb:
                                transit_groups[key] = transit
                            
                            break
            
            # Si no se encontró duplicado, añadir este tránsito
            if not found_match:
                unique_key = base_key + (date_key, movement, aspect_state)
                transit_groups[unique_key] = transit
        
        # Combinar los eventos estacionarios seleccionados con los demás eventos filtrados
        filtered_transits = list(transit_groups.values()) + stationary_selected
        
        # Ordenar por fecha
        filtered_transits.sort(key=lambda x: x[0])
        
        return filtered_transits
        
    def convert_to_astro_events(self, transit_dates):
        """
        Convierte los datos de tránsitos a objetos AstroEvent.
        
        Args:
            transit_dates: Lista de tuplas (fecha, planeta_id, aspecto, natal_id, movimiento, estado, orbe, posicion, velocidad)
            
        Returns:
            Lista de objetos AstroEvent
        """
        events = []
        
        for transit in transit_dates:
            # Desempaquetar los valores de la tupla
            # La velocidad (speed) es el noveno elemento, pero no lo necesitamos para crear el AstroEvent
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, planet_position = transit[:8]
            # Obtener nombres para la descripción
            planet_name = PLANET_NAMES.get(planet_id, str(planet_id))
            
            # Manejar tanto planetas como ángulos natales
            if natal_id in PLANET_NAMES:
                natal_name = PLANET_NAMES[natal_id]
            else:
                natal_name = str(natal_id)  # Para ángulos como 'ASC', 'MC', etc.
                
            aspect_name = ASPECT_NAMES[aspect_type]
            movement_name = MOVEMENT_NAMES[movement]
            aspect_state_name = ASPECT_STATE[aspect_state]
            
            # Crear descripción del evento incluyendo el estado del movimiento del planeta
            descripcion = f"{planet_name} ({movement_name.lower()}) por tránsito esta en {aspect_name} a tu {natal_name} Natal"
            
            # Obtener signo y grado para la posición del planeta
            planet_sign = AstronomicalConstants.get_sign_name(planet_position)
            planet_degree = planet_position % 30
            
            # Obtener signo y grado para la posición natal
            natal_position = self.natal_positions[natal_id]
            natal_sign = AstronomicalConstants.get_sign_name(natal_position)
            natal_degree = natal_position % 30
            
            # Formatear posiciones en formato de grados
            def format_position(degrees):
                whole_degrees = int(degrees)
                minutes_decimal = (degrees - whole_degrees) * 60
                minutes = int(minutes_decimal)
                seconds = int((minutes_decimal - minutes) * 60)
                return f"{whole_degrees}°{minutes}'{seconds}\""
            
            planet_position_str = f"{format_position(planet_degree)} {planet_sign}"
            natal_position_str = f"{format_position(natal_degree)} {natal_sign}"
            
            # Asegurarse de que la fecha esté en UTC antes de pasarla al objeto AstroEvent
            # Si la fecha ya tiene zona horaria (probablemente la del usuario), convertirla a UTC
            if date.tzinfo is not None and date.tzinfo != ZoneInfo("UTC"):
                date_utc = date.astimezone(ZoneInfo("UTC"))
            else:
                # Si no tiene zona horaria o ya está en UTC, usarla directamente
                date_utc = date
                
            # Crear objeto AstroEvent
            event = AstroEvent(
                fecha_utc=date_utc,  # Fecha en UTC
                tipo_evento=EventType.ASPECTO,
                descripcion=descripcion,
                planeta1=planet_name,
                planeta2=natal_name,
                longitud1=planet_position,  # Usar la posición exacta del planeta
                longitud2=natal_position,
                tipo_aspecto=aspect_name,
                orbe=orb,
                es_aplicativo=(aspect_state == calc.APPLICATIVE),
                metadata={
                    'movimiento': movement_name,
                    'estado': aspect_state_name,
                    'posicion1': planet_position_str,
                    'posicion2': natal_position_str
                },
                timezone_str=self.user_timezone.key  # Usar la zona horaria del usuario
            )
            events.append(event)
        
        return events
        
    def calculate_all(self, start_date: datetime = None, end_date: datetime = None, planets_to_check=None) -> list:
        """
        Calcula todos los tránsitos para el período especificado usando el enfoque astronómico mejorado.
        Versión 3.0 con mejoras específicas para la detección y preservación de eventos estacionarios.
        
        Args:
            start_date: Fecha inicial (default: 1 enero del año actual)
            end_date: Fecha final (default: 31 diciembre del año actual)
            planets_to_check: Lista de planetas a verificar (default: todos excepto Luna)
            
        Returns:
            Lista de eventos de tránsitos
        """
        # Si no se especifican fechas, usar el año actual completo con la zona horaria del usuario
        if not start_date:
            start_date = datetime(datetime.now().year, 1, 1, tzinfo=self.user_timezone)
        if not end_date:
            end_date = datetime(datetime.now().year, 12, 31, 23, 59, tzinfo=self.user_timezone)
        
        # Si no se especifican planetas, usar todos EXCEPTO la Luna
        if not planets_to_check:
            planets_to_check = [
                chart.SUN,
                # chart.MOON,  # Excluir la Luna como planeta transitante
                chart.MERCURY,
                chart.VENUS,
                chart.MARS,
                chart.JUPITER,
                chart.SATURN,
                chart.URANUS,
                chart.NEPTUNE,
                chart.PLUTO
            ]
        
        year = start_date.year
        
        # Iniciar el cálculo
        start_time = time.time()
        print("\nCalculando tránsitos con método astronómico v3.0...")
        
        # Para cada planeta, detectar cambios de dirección primero
        direction_changes = {}
        for planet_id in planets_to_check:
            direction_changes[planet_id] = self.detect_direction_changes(planet_id, start_date, end_date)
            print(f"Detectados {len(direction_changes[planet_id])} cambios de dirección para {PLANET_NAMES.get(planet_id, planet_id)}")
        
        # Procesar cada planeta en paralelo
        all_transits = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.find_transits_for_planet, planet, year, start_date, end_date) 
                      for planet in planets_to_check]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    planet_transits = future.result()
                    all_transits.extend(planet_transits)
                    print(f"Encontrados {len(planet_transits)} tránsitos para un planeta")
                except Exception as e:
                    print(f"Error procesando planeta: {e}")
        
        # Ordenar por fecha
        all_transits.sort(key=lambda x: x[0])
        
        # Filtrar por rango de fechas si es necesario
        filtered_transits = [t for t in all_transits if start_date <= t[0] <= end_date]
        
        # Eliminar duplicados, manteniendo solo el más exacto para cada combinación
        filtered_transits = self.filter_duplicate_transits(filtered_transits)
        
        # Convertir a objetos AstroEvent
        all_events = self.convert_to_astro_events(filtered_transits)
        
        # Mostrar resumen
        elapsed = time.time() - start_time
        print(f"\nCálculo astronómico v3.0 completado en {elapsed:.2f} segundos")
        print(f"Total de eventos encontrados: {len(all_events)}")
        
        return all_events
