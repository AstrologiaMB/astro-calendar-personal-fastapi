"""
Módulo para calcular tránsitos planetarios usando un enfoque astronómico.
Esta implementación utiliza los períodos orbitales conocidos de los planetas para estimar
cuándo ocurrirán los aspectos, y luego verifica la efemérides solo en esas fechas estimadas.
Este enfoque es significativamente más eficiente que verificar en intervalos regulares.
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
settings.default_orb = 2.0  # Orbe estándar de 2° (alineado con all_transits_parallel)
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

class AstronomicalTransitsCalculator:
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de tránsitos astronómico.
        
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
    
    def estimate_transit_dates(self, planet_id, natal_position, aspect_angle, year, start_date=None, end_date=None):
        """
        Estima las fechas en que un planeta transitará por una posición específica.
        
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
        
        # Para cuadraturas, hay dos posiciones posibles (90° y 270°)
        target_positions = [target_position]
        if aspect_angle == 90:
            target_positions.append((natal_position - 90) % 360)
        
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
        window_base_size = 10  # Aumentado de 7 a 10 días para mejor cobertura
        
        # Factor de ajuste basado en el período orbital
        window_factor = min(1.0, 30 / period)  # Factor de ajuste basado en el período
        
        # Ajuste adicional para cuadraturas (más difíciles de detectar)
        aspect_factor = 1.5 if aspect_angle == 90 else 1.0
        
        # Ajuste para planetas lentos (Júpiter, Saturno, etc.)
        planet_speed_factor = 1.0
        if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
            planet_speed_factor = 1.5  # 50% más de muestreo para planetas lentos
        
        # Calcular tamaño final de la ventana
        window_size = int(window_base_size / window_factor * aspect_factor * planet_speed_factor)
        
        # Limitar el tamaño máximo de la ventana
        window_size = min(window_size, 30)  # Aumentado de 15 a 30 para mejor cobertura
        
        # Generar offsets para la ventana de estimación con mayor densidad
        # Reducir el paso para tener más puntos de muestreo
        step_size = max(1, window_size // 8)  # Más denso que el original (window_size // 4)
        offsets = list(range(-window_size, window_size + 1, step_size))
        if 0 not in offsets:
            offsets.append(0)
        offsets.sort()
        
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
                    # Añadir fechas adicionales alrededor de la estimación para mayor precisión
                    for offset in offsets:
                        check_date = current_date + timedelta(days=offset)
                        if start_date <= check_date <= end_date:
                            estimated_dates.append((check_date, target_pos))
                    
                    # Verificar si hay un cambio de dirección (estacionamiento) cerca
                    # Esto es especialmente importante para planetas que pueden volverse retrógrados
                    if abs(initial_speed) < 0.5 and planet_id in [chart.MERCURY, chart.VENUS, chart.MARS, chart.JUPITER, chart.SATURN]:
                        # Añadir puntos adicionales alrededor de posibles estacionamientos
                        for extra_offset in range(-15, 16, 3):  # Ventana más amplia alrededor de estacionamientos
                            check_date = current_date + timedelta(days=extra_offset)
                            if start_date <= check_date <= end_date:
                                estimated_dates.append((check_date, target_pos))
                
                # Avanzar al siguiente ciclo
                current_date += timedelta(days=period)
        
        return estimated_dates
    
    def get_dynamic_orb(self, planet_id, natal_id, aspect_type):
        """
        Calcula un orbe dinámico basado en la combinación de planetas y el tipo de aspecto.
        
        Args:
            planet_id: ID del planeta transitante
            natal_id: ID del planeta o punto natal
            aspect_type: Tipo de aspecto
            
        Returns:
            Orbe dinámico en grados
        """
        # Orbe base según el tipo de aspecto
        base_orb = settings.default_orb  # Usar el valor configurado (2.0°)
        
        # Ajustar según el tipo de aspecto
        if aspect_type == calc.CONJUNCTION:
            base_orb *= 1.1  # 10% más de orbe para conjunciones
        elif aspect_type == calc.OPPOSITION:
            base_orb *= 1.1  # 10% más de orbe para oposiciones
        elif aspect_type == calc.SQUARE:
            # Aumentar ligeramente el orbe para cuadraturas
            # Especialmente para planetas rápidos que pueden pasar rápidamente
            if planet_id in [chart.MERCURY, chart.VENUS]:
                base_orb *= 1.1  # 10% más de orbe para cuadraturas de planetas rápidos
            else:
                base_orb *= 1.05  # 5% más para otras cuadraturas
        
        # Ajustar según la velocidad del planeta transitante
        # Planetas más lentos reciben orbes mayores
        planet_factor = 1.0
        if planet_id == chart.SUN or planet_id == chart.MOON:
            planet_factor = 1.2  # Luminarias reciben orbes mayores
        elif planet_id in [chart.MERCURY, chart.VENUS]:
            planet_factor = 1.0  # Planetas rápidos reciben orbes estándar
        elif planet_id in [chart.MARS, chart.JUPITER]:
            planet_factor = 1.1  # Planetas medios reciben orbes ligeramente mayores
        elif planet_id in [chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
            planet_factor = 1.2  # Planetas lentos reciben orbes mayores
        
        # Ajustar según el planeta natal
        # Luminarias natales reciben orbes mayores
        natal_factor = 1.0
        if natal_id == chart.SUN or natal_id == chart.MOON:
            natal_factor = 1.2
        
        # Combinaciones especiales
        # Sol-Luna y Luna-Sol reciben orbes mayores
        if (planet_id == chart.SUN and natal_id == chart.MOON) or (planet_id == chart.MOON and natal_id == chart.SUN):
            return base_orb * 1.5  # 50% más de orbe para aspectos Sol-Luna
        
        # Mercurio recibe orbes mayores debido a su movimiento rápido
        if planet_id == chart.MERCURY or natal_id == chart.MERCURY:
            return base_orb * 1.2  # 20% más de orbe para aspectos con Mercurio
        
        # Calcular orbe final
        return base_orb * planet_factor * natal_factor
    
    def check_aspect_at_date(self, planet_id, date, target_position, natal_id=None, aspect_type=None):
        """
        Verifica si un planeta forma un aspecto en una fecha específica.
        
        Args:
            planet_id: ID del planeta transitante
            date: Fecha a verificar
            target_position: Posición objetivo en grados
            natal_id: ID del planeta natal (opcional, para orbes dinámicos)
            aspect_type: Tipo de aspecto (opcional, para orbes dinámicos)
            
        Returns:
            Tupla (es_aspecto, fecha_exacta, posición, velocidad, orbe)
        """
        jd = self.datetime_to_jd(date)
        planet_data = ephemeris.planet(planet_id, jd)
        position = planet_data['lon']
        speed = planet_data['speed']
        
        # Calcular la diferencia angular
        diff = self.normalize_angle_diff(target_position, position)
        orb = abs(diff)
        
        # Determinar el orbe máximo permitido
        max_orb = settings.default_orb
        if natal_id is not None and aspect_type is not None:
            max_orb = self.get_dynamic_orb(planet_id, natal_id, aspect_type)
        
        # Verificar si está dentro del orbe permitido
        if orb <= max_orb:
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
                prev_date = date - timedelta(days=1)
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
            
            return True, date, position, speed, orb, movement, aspect_state
        
        return False, None, position, speed, orb, None, None
    
    def refine_aspect_date(self, planet_id, date, target_position, max_iterations=10):
        """
        Refina la fecha exacta de un aspecto mediante búsqueda binaria.
        
        Args:
            planet_id: ID del planeta transitante
            date: Fecha aproximada
            target_position: Posición objetivo en grados
            max_iterations: Número máximo de iteraciones
            
        Returns:
            Tupla (fecha_exacta, posición, velocidad, orbe, movimiento, estado)
        """
        jd = self.datetime_to_jd(date)
        planet_data = ephemeris.planet(planet_id, jd)
        position = planet_data['lon']
        speed = planet_data['speed']
        
        # Calcular la diferencia angular
        diff = self.normalize_angle_diff(target_position, position)
        
        # Si la diferencia es muy pequeña, no es necesario refinar
        if abs(diff) <= settings.exact_orb:
            # Determinar el movimiento
            if abs(speed) <= 0.0001:  # Casi estacionario
                movement = calc.STATIONARY
            else:
                movement = calc.DIRECT if speed > 0 else calc.RETROGRADE
            
            # Determinar el estado del aspecto
            aspect_state = calc.EXACT
            
            return date, position, speed, abs(diff), movement, aspect_state
        
        # Estimar cuánto tiempo tomará llegar a la posición exacta
        days_to_exact = diff / (speed if speed != 0 else 0.1)  # Evitar división por cero
        
        # Limitar a un rango razonable
        days_to_exact = max(-10, min(10, days_to_exact))
        
        # Fecha estimada del aspecto exacto
        exact_date = date + timedelta(days=days_to_exact)
        
        # Verificar la nueva fecha
        jd_exact = self.datetime_to_jd(exact_date)
        exact_data = ephemeris.planet(planet_id, jd_exact)
        exact_position = exact_data['lon']
        exact_speed = exact_data['speed']
        
        # Calcular la nueva diferencia
        exact_diff = self.normalize_angle_diff(target_position, exact_position)
        
        # Si la nueva diferencia es menor, usar la nueva fecha
        if abs(exact_diff) < abs(diff):
            # Refinar recursivamente si es necesario
            if abs(exact_diff) > settings.exact_orb and max_iterations > 0:
                return self.refine_aspect_date(planet_id, exact_date, target_position, max_iterations - 1)
            
            # Determinar el movimiento
            if abs(exact_speed) <= 0.0001:  # Casi estacionario
                movement = calc.STATIONARY
            else:
                movement = calc.DIRECT if exact_speed > 0 else calc.RETROGRADE
            
            # Determinar el estado del aspecto
            if abs(exact_diff) <= settings.exact_orb:
                aspect_state = calc.EXACT
            else:
                # Determinar si el aspecto es aplicativo o separativo
                is_applying = False
                
                # Si el planeta se mueve directo
                if exact_speed > 0:
                    # Calcular la dirección más corta hacia el objetivo
                    direction_to_target = self.normalize_angle_diff(target_position, exact_position)
                    is_applying = (direction_to_target > 0)
                else:
                    # Si el planeta se mueve retrógrado
                    direction_to_target = self.normalize_angle_diff(target_position, exact_position)
                    is_applying = (direction_to_target < 0)
                
                aspect_state = calc.APPLICATIVE if is_applying else calc.SEPARATIVE
            
            return exact_date, exact_position, exact_speed, abs(exact_diff), movement, aspect_state
        
        # Si la nueva diferencia es mayor, mantener la fecha original
        # Determinar el movimiento
        if abs(speed) <= 0.0001:  # Casi estacionario
            movement = calc.STATIONARY
        else:
            movement = calc.DIRECT if speed > 0 else calc.RETROGRADE
        
        # Determinar el estado del aspecto
        if abs(diff) <= settings.exact_orb:
            aspect_state = calc.EXACT
        else:
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
            
            aspect_state = calc.APPLICATIVE if is_applying else calc.SEPARATIVE
        
        return date, position, speed, abs(diff), movement, aspect_state
    
    def find_transits_for_planet(self, planet_id, year, start_date=None, end_date=None):
        """
        Encuentra todos los tránsitos de un planeta para un año específico.
        
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
        
        # Para cada planeta/punto natal
        for natal_id, natal_position in self.natal_positions.items():
            # Para cada tipo de aspecto
            for aspect_type, aspect_angle in ASPECT_ANGLES.items():
                # Estimar fechas de tránsito
                estimated_dates = self.estimate_transit_dates(
                    planet_id, natal_position, aspect_angle, year, start_date, end_date
                )
                
                # Calcular la posición objetivo para este aspecto
                target_position = (natal_position + aspect_angle) % 360
                
                # Añadir fechas adicionales para aspectos específicos que son difíciles de detectar
                extra_dates = []
                
                # Determinar el intervalo de muestreo basado en características astronómicas
                base_interval = timedelta(hours=12)  # Intervalo base de 12 horas
                
                # Calcular la velocidad relativa entre el planeta transitante y el planeta natal
                # Para planetas natales, la velocidad es 0 (posición fija)
                jd_start = self.datetime_to_jd(start_date)
                planet_data = ephemeris.planet(planet_id, jd_start)
                planet_speed = abs(planet_data['speed'])  # Valor absoluto de la velocidad
                
                # Ajustar el intervalo según características astronómicas
                
                # 1. Ajuste por tipo de aspecto (las cuadraturas son más difíciles de detectar)
                aspect_factor = 2.0 if aspect_type == calc.SQUARE else 1.0
                
                # 2. Ajuste por velocidad del planeta (planetas más lentos o cerca de estacionamiento)
                # Velocidad típica de un planeta en movimiento directo (grados/día)
                typical_speed = AVERAGE_SPEED.get(planet_id, 1.0)
                
                # Si la velocidad es menor al 20% de la típica, es posible que esté cerca de un estacionamiento
                speed_ratio = planet_speed / typical_speed if typical_speed > 0 else 1.0
                
                # Factor de velocidad: más muestreo para planetas lentos o cerca de estacionamiento
                if speed_ratio < 0.2:  # Muy lento o cerca de estacionamiento
                    speed_factor = 6.0  # Muestreo muy denso
                elif speed_ratio < 0.5:  # Lento
                    speed_factor = 3.0  # Muestreo denso
                else:
                    speed_factor = 1.0  # Muestreo normal
                
                # 3. Ajuste por combinación de planetas
                # Combinaciones que involucran planetas lentos necesitan más muestreo
                combo_factor = 1.0
                if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                    combo_factor = 2.0  # Doble densidad para planetas lentos
                
                # Calcular el factor de ajuste final
                adjustment_factor = aspect_factor * speed_factor * combo_factor
                
                # Calcular el intervalo final en horas (más pequeño = más denso)
                # Limitar a un mínimo de 1 hora y un máximo de 24 horas
                interval_hours = max(1.0, min(24.0, 12.0 / adjustment_factor))
                sampling_interval = timedelta(hours=interval_hours)
                
                # Para aspectos Sol-Luna, usar muestreo cada 12 horas
                if (planet_id == chart.SUN and natal_id == chart.MOON) or (planet_id == chart.MOON and natal_id == chart.SUN):
                    current = start_date
                    while current <= end_date:
                        extra_dates.append((current, target_position))
                        current += base_interval
                
                # Para aspectos con Mercurio, usar muestreo más denso
                elif planet_id == chart.MERCURY or natal_id == chart.MERCURY:
                    # Calcular intervalo basado en el tipo de aspecto
                    mercury_interval = timedelta(hours=4)  # Reducir de 12 a 4 horas
                    
                    # Para cuadraturas, usar intervalo aún más pequeño
                    if aspect_type == calc.SQUARE:
                        mercury_interval = timedelta(hours=2)  # Más denso para cuadraturas
                        
                    current = start_date
                    while current <= end_date:
                        extra_dates.append((current, target_position))
                        current += mercury_interval
                
                # Para aspectos con Venus, usar muestreo más denso que el diario
                elif planet_id == chart.VENUS or natal_id == chart.VENUS:
                    # Calcular intervalo basado en el tipo de aspecto
                    venus_interval = timedelta(hours=6)  # Reducir de 24 a 6 horas
                    
                    # Para cuadraturas, usar intervalo aún más pequeño
                    if aspect_type == calc.SQUARE:
                        venus_interval = timedelta(hours=3)  # Más denso para cuadraturas
                        
                    current = start_date
                    while current <= end_date:
                        extra_dates.append((current, target_position))
                        current += venus_interval
                
                # Para aspectos con planetas rápidos (Luna, Sol), usar muestreo diario
                elif planet_id in [chart.MOON, chart.SUN] or natal_id in [chart.MOON, chart.SUN]:
                    current = start_date
                    while current <= end_date:
                        extra_dates.append((current, target_position))
                        current += timedelta(days=1)
                
                # Para todos los demás aspectos, usar el intervalo ajustado dinámicamente
                else:
                    current = start_date
                    while current <= end_date:
                        extra_dates.append((current, target_position))
                        
                        # Recálculo adaptativo de velocidad
                        # Determinar la frecuencia de recálculo basada en el planeta y su velocidad
                        recalc_days = 30  # Valor predeterminado (30 días)
                        
                        # Para planetas lentos, recalcular con mayor frecuencia
                        if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                            recalc_days = 7  # Cada 7 días para planetas lentos
                        
                        # Para planetas rápidos, recalcular con mayor frecuencia
                        elif planet_id in [chart.MERCURY, chart.VENUS]:
                            recalc_days = 3  # Cada 3 días para planetas rápidos
                        
                        # Recalcular si ha pasado el número de días correspondiente
                        days_since_start = (current - start_date).days
                        if days_since_start % recalc_days == 0 and days_since_start > 0:
                            # Obtener la velocidad actual del planeta
                            jd_current = self.datetime_to_jd(current)
                            current_data = ephemeris.planet(planet_id, jd_current)
                            current_speed = abs(current_data['speed'])
                            
                            # Recalcular el factor de velocidad
                            speed_ratio = current_speed / typical_speed if typical_speed > 0 else 1.0
                            
                            # Ajustar el factor de velocidad basado en la velocidad actual
                            if speed_ratio < 0.1:  # Extremadamente lento o casi estacionario
                                speed_factor = 10.0  # Muestreo extremadamente denso
                            elif speed_ratio < 0.2:  # Muy lento o cerca de estacionamiento
                                speed_factor = 6.0  # Muestreo muy denso
                            elif speed_ratio < 0.5:  # Lento
                                speed_factor = 3.0  # Muestreo denso
                            else:
                                speed_factor = 1.0  # Muestreo normal
                            
                            # Recalcular el intervalo
                            adjustment_factor = aspect_factor * speed_factor * combo_factor
                            interval_hours = max(1.0, min(24.0, 12.0 / adjustment_factor))
                            sampling_interval = timedelta(hours=interval_hours)
                        
                        current += sampling_interval
                
                # Añadir muestreo adicional para períodos de cambio de dirección
                # Detectar posibles estacionamientos (cambios de dirección) durante el período
                check_dates = []
                
                # Determinar el intervalo de verificación basado en el planeta
                if planet_id in [chart.MERCURY, chart.VENUS]:
                    check_interval = timedelta(days=5)  # Verificar cada 5 días para planetas rápidos
                elif planet_id in [chart.MARS, chart.JUPITER]:
                    check_interval = timedelta(days=7)  # Verificar cada 7 días para planetas medios
                else:
                    check_interval = timedelta(days=15)  # Verificar cada 15 días para planetas lentos
                
                check_date = start_date
                
                while check_date <= end_date:
                    check_dates.append(check_date)
                    check_date += check_interval
                
                # Añadir la fecha final si no está incluida
                if check_dates[-1] < end_date:
                    check_dates.append(end_date)
                
                # Verificar cambios de dirección
                prev_direction = None
                
                for i, check_date in enumerate(check_dates):
                    if i > 0:
                        jd = self.datetime_to_jd(check_date)
                        planet_data = ephemeris.planet(planet_id, jd)
                        current_speed = planet_data['speed']
                        current_direction = 1 if current_speed > 0 else -1 if current_speed < 0 else 0
                        
                        if prev_direction is not None and current_direction != prev_direction:
                            # Posible cambio de dirección detectado
                            # Añadir muestreo denso alrededor de esta fecha
                            station_start = check_dates[i-1]
                            station_end = check_date
                            
                            # Determinar el intervalo de muestreo para el período de estacionamiento
                            # basado en el planeta y el tipo de aspecto
                            if planet_id in [chart.MERCURY, chart.VENUS]:
                                # Para planetas rápidos, usar intervalo muy pequeño
                                dense_interval = timedelta(minutes=30)  # 30 minutos
                            elif planet_id in [chart.MARS, chart.JUPITER]:
                                # Para planetas medios, usar intervalo pequeño
                                dense_interval = timedelta(hours=1)  # 1 hora
                            else:
                                # Para planetas lentos, usar intervalo moderado
                                dense_interval = timedelta(hours=2)  # 2 horas
                            
                            # Para cuadraturas, reducir el intervalo a la mitad
                            if aspect_type == calc.SQUARE:
                                dense_interval = timedelta(seconds=dense_interval.total_seconds() / 2)
                            
                            # Añadir muestreo denso alrededor del período de estacionamiento
                            current = station_start
                            while current <= station_end:
                                extra_dates.append((current, target_position))
                                current += dense_interval
                        
                        prev_direction = current_direction
                
                # Combinar las fechas estimadas con las fechas adicionales
                all_dates = estimated_dates + extra_dates
                
                # Verificar cada fecha estimada
                for date, target_position in all_dates:
                    is_aspect, exact_date, position, speed, orb, movement, aspect_state = self.check_aspect_at_date(
                        planet_id, date, target_position, natal_id, aspect_type
                    )
                    
                    if is_aspect:
                        # Refinar la fecha exacta
                        exact_date, exact_position, exact_speed, exact_orb, exact_movement, exact_state = self.refine_aspect_date(
                            planet_id, exact_date, target_position
                        )
                        
                        # Añadir el tránsito a la lista
                        transits.append((
                            exact_date,
                            planet_id,
                            aspect_type,
                            natal_id,
                            exact_movement,
                            exact_state,
                            exact_orb,
                            exact_position
                        ))
        
        return transits
    
    def convert_to_astro_events(self, transit_dates):
        """Convierte los datos de tránsitos a objetos AstroEvent."""
        events = []
        
        for date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, planet_position in transit_dates:
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
            
            # Crear descripción del evento en el mismo formato que all_transits_parallel.py
            descripcion = f"{planet_name} por tránsito esta en {aspect_name} a tu {natal_name} Natal"
            
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
            
            # Crear objeto AstroEvent
            event = AstroEvent(
                fecha_utc=date,
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
                }
            )
            events.append(event)
        
        return events
    
    def filter_duplicate_transits(self, transit_dates):
        """
        Filtra tránsitos duplicados, manteniendo solo el más exacto para cada combinación única.
        También considera la proximidad temporal para identificar duplicados.
        
        Args:
            transit_dates: Lista de tuplas (fecha, planeta_id, aspecto, natal_id, movimiento, estado, orbe, posicion)
            
        Returns:
            Lista filtrada de tránsitos sin duplicados
        """
        # Paso 1: Filtrar aspectos a puntos que no son planetas
        valid_transits = []
        for transit in transit_dates:
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position = transit
            
            # Ignorar aspectos a puntos que no son planetas (como MC, IC, etc.)
            # Solo si natal_id no es un número (los IDs de planetas son números)
            if not isinstance(natal_id, int) and natal_id not in ['ASC', 'MC']:
                continue
                
            valid_transits.append(transit)
        
        # Paso 2: Agrupar por combinación planeta-aspecto-natal y mes
        # Esto permite identificar duplicados que ocurren en el mismo mes
        transit_groups = {}
        
        for transit in valid_transits:
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position = transit
            
            # Clave única para cada combinación planeta-aspecto-natal y mes
            month_key = (date.year, date.month)
            
            # Para planetas lentos, usar una clave más específica que incluya la semana
            # Esto evita que se filtren aspectos legítimos que ocurren en el mismo mes
            if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                # Calcular el número de semana dentro del mes (1-5)
                week_of_month = (date.day - 1) // 7 + 1
                month_key = (date.year, date.month, week_of_month)
            
            key = (planet_id, natal_id, aspect_type, month_key)
            
            # Si ya existe un tránsito para esta combinación, verificar si este es más exacto
            if key in transit_groups:
                prev_transit = transit_groups[key]
                prev_orb = prev_transit[6]
                prev_movement = prev_transit[4]
                
                # Si este tránsito es más exacto (orbe menor), reemplazar el anterior
                if orb < prev_orb:
                    transit_groups[key] = transit
                # Si los orbes son similares pero este tiene un movimiento diferente, mantener ambos
                # Esto es importante para capturar aspectos cerca de cambios de dirección
                elif abs(orb - prev_orb) < 0.5 and movement != prev_movement:
                    # Crear una clave alternativa para mantener ambos tránsitos
                    alt_key = (planet_id, natal_id, aspect_type, month_key, movement)
                    transit_groups[alt_key] = transit
            else:
                # Si no existe un tránsito previo para esta combinación
                transit_groups[key] = transit
        
        # Paso 3: Filtrar duplicados temporales cercanos
        # Agrupar tránsitos que ocurren en fechas muy cercanas
        temporal_groups = {}
        
        # Ordenar por fecha para procesar cronológicamente
        sorted_transits = sorted(transit_groups.values(), key=lambda x: x[0])
        
        for transit in sorted_transits:
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position = transit
            
            # Clave base sin considerar la fecha
            base_key = (planet_id, natal_id, aspect_type)
            
            # Verificar si ya existe un tránsito similar en una fecha cercana
            found_temporal_match = False
            
            for existing_key in list(temporal_groups.keys()):
                existing_transit = temporal_groups[existing_key]
                existing_date = existing_transit[0]
                existing_planet_id = existing_transit[1]
                existing_aspect_type = existing_transit[2]
                existing_natal_id = existing_transit[3]
                existing_movement = existing_transit[4]
                
                # Si es la misma combinación planeta-aspecto-natal
                if (existing_planet_id == planet_id and 
                    existing_natal_id == natal_id and 
                    existing_aspect_type == aspect_type):
                    
                    # Determinar el umbral de días basado en la velocidad del planeta
                    # Planetas más lentos pueden tener aspectos legítimos más cercanos entre sí
                    day_threshold = 3.0  # Valor predeterminado (3 días)
                    
                    # Reducir el umbral para planetas lentos
                    if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                        day_threshold = 1.5  # Reducir a 1.5 días para planetas lentos
                    
                    # Reducir aún más si los movimientos son diferentes (directo vs retrógrado)
                    if movement != existing_movement:
                        day_threshold = 1.0  # Reducir a 1 día si los movimientos son diferentes
                    
                    # Verificar si las fechas están dentro del umbral
                    date_diff = abs((date - existing_date).total_seconds()) / 86400.0  # Diferencia en días
                    
                    if date_diff <= day_threshold:
                        found_temporal_match = True
                        
                        # Si los movimientos son diferentes, mantener ambos
                        if movement != existing_movement:
                            # Crear una clave alternativa para mantener ambos tránsitos
                            alt_key = (base_key, date.strftime('%Y-%m-%d'), movement)
                            temporal_groups[alt_key] = transit
                            found_temporal_match = False  # Seguir procesando
                            break
                        
                        # Mantener el que tenga menor orbe
                        existing_orb = existing_transit[6]
                        if orb < existing_orb:
                            temporal_groups[existing_key] = transit
                        
                        break
            
            # Si no se encontró un duplicado temporal, agregar este tránsito
            if not found_temporal_match:
                # Generar una clave única que incluya la fecha
                unique_key = (base_key, date.strftime('%Y-%m-%d'))
                temporal_groups[unique_key] = transit
        
        # Recopilar todos los tránsitos filtrados
        filtered_transits = list(temporal_groups.values())
        
        # Ordenar por fecha
        filtered_transits.sort(key=lambda x: x[0])
        
        return filtered_transits
    
    def calculate_all(self, start_date: datetime = None, end_date: datetime = None, planets_to_check=None) -> list:
        """
        Calcula todos los tránsitos para el período especificado usando el enfoque astronómico.
        
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
        
        # Si no se especifican planetas, usar todos excepto Luna (que requiere un enfoque diferente)
        if not planets_to_check:
            planets_to_check = [
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
        
        year = start_date.year
        
        # Iniciar el cálculo
        start_time = time.time()
        print("\nCalculando tránsitos con método astronómico...")
        
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
        print(f"\nCálculo astronómico completado en {elapsed:.2f} segundos")
        print(f"Total de eventos encontrados: {len(all_events)}")
        
        return all_events
