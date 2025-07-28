"""
Módulo optimizado para calcular tránsitos planetarios usando un enfoque matemático/analítico.
Esta implementación calcula directamente cuándo ocurrirán los aspectos en lugar de verificar
en intervalos regulares, lo que resulta en un cálculo mucho más eficiente.
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
from immanuel.tools import ephemeris
import numpy as np

# Configuración de immanuel para aspectos - Mantener consistencia con all_transits_parallel.py
settings.aspects = [calc.CONJUNCTION, calc.OPPOSITION, calc.SQUARE]
settings.default_orb = 3.0  # Aumentar el orbe a 3° para capturar más aspectos
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

# Lista de planetas a procesar (excluyendo Mercurio)
PLANETS_TO_CHECK = [
    chart.SUN,
    chart.VENUS,
    chart.MARS,
    chart.JUPITER,
    chart.SATURN,
    chart.URANUS,
    chart.NEPTUNE,
    chart.PLUTO
]

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

# Restricciones de aspectos imposibles
INVALID_ASPECTS = {
    # Nota: Eliminamos las restricciones para permitir todos los aspectos que AstroSeek muestra
}

class OptimizedTransitsCalculator:
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de tránsitos optimizado.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
        """
        self.natal_data = natal_data
        
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
    
    def precompute_target_positions(self):
        """
        Precalcula las posiciones exactas de los planetas en tránsito para formar aspectos con los planetas natales.
        Incluye un rango de orbe para cada aspecto.
        """
        self.target_positions = {}
        for natal_id, natal_lon in self.natal_positions.items():
            # Filtrar aspectos imposibles para este planeta/punto natal
            valid_aspects = {k: v for k, v in ASPECT_ANGLES.items() 
                            if k not in INVALID_ASPECTS.get(natal_id, [])}
            
            self.target_positions[natal_id] = {}
            for aspect, angle in valid_aspects.items():
                # Crear un rango de posiciones objetivo dentro del orbe permitido
                # Aumentamos de 5 a 15 puntos para mayor precisión
                orb_range = np.linspace(-settings.default_orb, settings.default_orb, 15)
                targets = []
                
                # Añadir posición para el aspecto directo
                for orb in orb_range:
                    targets.append(((natal_lon + angle + orb) % 360, orb))
                
                # Si no es conjunción, añadir también para el aspecto inverso
                if angle != 0:
                    for orb in orb_range:
                        targets.append(((natal_lon - angle + orb) % 360, orb))
                
                self.target_positions[natal_id][aspect] = targets
        
        print("Posiciones objetivo precalculadas (incluyendo orbes y excluyendo aspectos imposibles).")
    
    @staticmethod
    def datetime_to_jd(dt: datetime) -> float:
        """Convierte un objeto datetime a fecha juliana."""
        j2000 = datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
        days_since_j2000 = (dt - j2000).total_seconds() / 86400.0
        return 2451545.0 + days_since_j2000
    
    def get_ephemeris_for_year(self, planet_id, year):
        """
        Obtiene la efemérides del planeta para el año completo en intervalos adaptados a su velocidad.
        Planetas rápidos: intervalos más cortos, planetas lentos: intervalos más largos.
        """
        start_date = datetime(year, 1, 1, tzinfo=ZoneInfo("UTC"))
        end_date = datetime(year, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
        
        # Determinar intervalo base según el planeta
        if planet_id in [chart.MOON, chart.MERCURY]:
            interval_base = timedelta(hours=1)  # Luna y Mercurio: cada 1 hora
        elif planet_id == chart.VENUS:
            interval_base = timedelta(hours=2)  # Venus: cada 2 horas
        elif planet_id == chart.SUN:
            interval_base = timedelta(hours=4)  # Sol: cada 4 horas
        elif planet_id in [chart.MARS, chart.JUPITER]:
            interval_base = timedelta(hours=6)  # Planetas medios: cada 6 horas
        else:
            interval_base = timedelta(hours=12)  # Planetas lentos: cada 12 horas
        
        current = start_date
        ephemeris_data = []
        
        # Recopilamos todas las posiciones objetivo para este planeta
        all_target_positions = []
        for natal_id, aspects in self.target_positions.items():
            for aspect_type, targets in aspects.items():
                for target_degree, _ in targets:
                    all_target_positions.append(target_degree)
        
        while current <= end_date:
            jd = self.datetime_to_jd(current)
            planet_data = ephemeris.planet(planet_id, jd)
            position = planet_data['lon']
            ephemeris_data.append((current, position, planet_data['speed']))
            
            # Determinar el intervalo dinámicamente
            # Si estamos cerca de una posición objetivo, reducir el intervalo
            min_distance = float('inf')
            for target in all_target_positions:
                # Normalizar la distancia angular
                distance = abs((target - position + 180) % 360 - 180)
                min_distance = min(min_distance, distance)
            
            # Reducir el intervalo si estamos cerca de una posición objetivo
            if min_distance <= settings.default_orb * 3.0:  # Margen adicional ampliado
                if min_distance <= settings.default_orb:
                    interval = interval_base / 6  # Reducir a un sexto si muy cerca
                elif min_distance <= settings.default_orb * 2.0:
                    interval = interval_base / 3  # Reducir a un tercio si moderadamente cerca
                else:
                    interval = interval_base / 2  # Reducir a la mitad
            else:
                interval = interval_base
            
            current += interval
        
        print(f"Efemérides calculadas para {PLANET_NAMES.get(planet_id, planet_id)}: {len(ephemeris_data)} puntos")
        return ephemeris_data
    
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
    
    def find_exact_crossing(self, t1, t2, pos1, pos2, speed1, speed2, target_degree):
        """
        Encuentra el momento exacto en que un planeta cruza un grado específico
        utilizando búsqueda binaria con interpolación.
        
        Args:
            t1, t2: Tiempos de los puntos conocidos
            pos1, pos2: Posiciones en los puntos conocidos
            speed1, speed2: Velocidades en los puntos conocidos
            target_degree: Grado objetivo
            
        Returns:
            Tupla (tiempo_exacto, posición_exacta, velocidad_exacta, orbe)
        """
        # Normalizar posiciones y diferencias para manejar el cruce 0°/360°
        pos1_norm = pos1 % 360
        pos2_norm = pos2 % 360
        target_norm = target_degree % 360
        
        # Calcular diferencias normalizadas
        diff1 = self.normalize_angle_diff(target_norm, pos1_norm)
        diff2 = self.normalize_angle_diff(target_norm, pos2_norm)
        
        # Si no hay cruce ni puntos dentro del orbe, retornar None
        if diff1 * diff2 > 0 and abs(diff1) > settings.default_orb and abs(diff2) > settings.default_orb:
            # Verificar si hay un cruce de 0°/360° entre los puntos
            if abs(pos1_norm - pos2_norm) > 180:
                # Hay un cruce de 0°/360° entre los puntos, verificar si el objetivo está en ese rango
                if (pos1_norm > pos2_norm and (target_norm >= pos2_norm or target_norm <= pos1_norm)) or \
                   (pos2_norm > pos1_norm and (target_norm >= pos1_norm or target_norm <= pos2_norm)):
                    # El objetivo está en el rango del cruce, continuar con la interpolación
                    pass
                else:
                    return None
            else:
                return None
        
        # Convertir tiempos a segundos desde t1 para la interpolación
        t1_sec = 0
        t2_sec = (t2 - t1).total_seconds()
        
        # Función para calcular la diferencia al grado objetivo en un tiempo dado
        def diff_at_time(t_sec):
            # Interpolar posición
            fraction = t_sec / t2_sec
            
            # Manejar el cruce de 0°/360°
            if abs(pos1_norm - pos2_norm) > 180:
                # Ajustar para el cruce de 0°/360°
                if pos1_norm > pos2_norm:
                    pos2_adjusted = pos2_norm + 360
                else:
                    pos1_adjusted = pos1_norm + 360
                    
                # Interpolar con los valores ajustados
                if pos1_norm > pos2_norm:
                    pos = (pos1_norm + fraction * (pos2_adjusted - pos1_norm)) % 360
                else:
                    pos = (pos1_adjusted + fraction * (pos2_norm - pos1_adjusted)) % 360
            else:
                # Interpolación normal
                pos = (pos1_norm + fraction * (pos2_norm - pos1_norm)) % 360
            
            # Calcular diferencia normalizada
            return self.normalize_angle_diff(target_norm, pos)
        
        # Búsqueda binaria para encontrar el cruce exacto
        left = t1_sec
        right = t2_sec
        
        # Buscar el punto donde la diferencia es cercana a cero
        for _ in range(30):  # Aumentamos a 30 iteraciones para mayor precisión
            mid = (left + right) / 2
            diff_mid = diff_at_time(mid)
            
            if abs(diff_mid) < 1e-6:  # Precisión suficiente
                break
                
            if diff_mid * diff_at_time(left) < 0:
                right = mid
            else:
                left = mid
        
        # Calcular tiempo exacto
        exact_time = t1 + timedelta(seconds=mid)
        
        # Interpolar posición y velocidad en el tiempo exacto
        fraction = mid / t2_sec
        
        # Manejar el cruce de 0°/360° para la interpolación final
        if abs(pos1_norm - pos2_norm) > 180:
            # Ajustar para el cruce de 0°/360°
            if pos1_norm > pos2_norm:
                pos2_adjusted = pos2_norm + 360
                exact_pos = (pos1_norm + fraction * (pos2_adjusted - pos1_norm)) % 360
            else:
                pos1_adjusted = pos1_norm + 360
                exact_pos = (pos1_adjusted + fraction * (pos2_norm - pos1_adjusted)) % 360
        else:
            # Interpolación normal
            exact_pos = (pos1_norm + fraction * (pos2_norm - pos1_norm)) % 360
            
        exact_speed = speed1 + fraction * (speed2 - speed1)
        
        # Calcular orbe exacto
        exact_orb = abs(self.normalize_angle_diff(target_degree, exact_pos))
        
        return exact_time, exact_pos, exact_speed, exact_orb
    
    def interpolate_exact_time(self, ephemeris_data, target_degree, target_orb):
        """
        Interpola la hora exacta en que un planeta alcanza un grado específico.
        Utiliza interpolación cúbica y búsqueda binaria para mayor precisión.
        Detecta múltiples cruces debido a movimiento retrógrado.
        """
        crossing_events = []
        
        # Necesitamos al menos 2 puntos para la interpolación
        if len(ephemeris_data) < 2:
            return crossing_events
        
        # Buscar cruces entre cada par de puntos consecutivos
        for i in range(len(ephemeris_data) - 1):
            t1, pos1, speed1 = ephemeris_data[i]
            t2, pos2, speed2 = ephemeris_data[i + 1]
            
            # Normalizar posiciones y diferencias para manejar el cruce 0°/360°
            pos1_norm = pos1 % 360
            pos2_norm = pos2 % 360
            target_norm = target_degree % 360
            
            # Calcular diferencias normalizadas
            diff1 = self.normalize_angle_diff(target_norm, pos1_norm)
            diff2 = self.normalize_angle_diff(target_norm, pos2_norm)
            
            # Verificar si el planeta cruza la posición objetivo o está dentro del orbe
            if (diff1 * diff2 <= 0) or (abs(diff1) <= settings.default_orb and abs(diff2) <= settings.default_orb):
                # Encontrar el cruce exacto
                result = self.find_exact_crossing(t1, t2, pos1, pos2, speed1, speed2, target_degree)
                
                if result is None:
                    # Si no hay cruce exacto pero ambos puntos están dentro del orbe,
                    # usar el punto con menor orbe
                    if abs(diff1) <= settings.default_orb and abs(diff2) <= settings.default_orb:
                        if abs(diff1) <= abs(diff2):
                            exact_time = t1
                            exact_pos = pos1
                            exact_speed = speed1
                            exact_orb = abs(diff1)
                        else:
                            exact_time = t2
                            exact_pos = pos2
                            exact_speed = speed2
                            exact_orb = abs(diff2)
                    else:
                        continue  # No hay cruce ni puntos dentro del orbe
                else:
                    exact_time, exact_pos, exact_speed, exact_orb = result
                
                # Determinar si el aspecto es aplicativo o separativo
                # Un aspecto es aplicativo si la distancia está disminuyendo
                is_applying = False
                
                # Si el planeta se mueve directo
                if exact_speed > 0:
                    # Calcular la dirección más corta hacia el objetivo
                    direction_to_target = self.normalize_angle_diff(target_degree, exact_pos)
                    is_applying = (direction_to_target > 0)
                else:
                    # Si el planeta se mueve retrógrado
                    direction_to_target = self.normalize_angle_diff(target_degree, exact_pos)
                    is_applying = (direction_to_target < 0)
                
                aspect_state = calc.APPLICATIVE if is_applying else calc.SEPARATIVE
                
                # Si el orbe es muy pequeño, considerar el aspecto exacto
                if exact_orb <= settings.exact_orb:
                    aspect_state = calc.EXACT
                
                # Determinar el movimiento
                if abs(exact_speed) <= 0.0001:  # Casi estacionario
                    movement = calc.STATIONARY
                else:
                    movement = calc.DIRECT if exact_speed > 0 else calc.RETROGRADE
                
                # Añadir el evento de cruce
                crossing_events.append((
                    exact_time, 
                    movement,
                    aspect_state,
                    exact_orb + abs(target_orb),  # Orbe total: orbe del punto objetivo + orbe de interpolación
                    exact_pos  # Posición exacta interpolada
                ))
        
        return crossing_events
    
    def find_transit_dates(self, planet_id, year):
        """
        Encuentra las fechas en las que un planeta transitante alcanza posiciones objetivo.
        """
        ephemeris_data = self.get_ephemeris_for_year(planet_id, year)
        transit_dates = []
        
        # Identificar combinaciones críticas que necesitan atención especial
        critical_combinations = [
            (chart.SUN, chart.MOON, calc.SQUARE),      # Sol cuadratura Luna
            (chart.VENUS, chart.VENUS, calc.SQUARE),   # Venus cuadratura Venus
            (chart.VENUS, chart.MERCURY, calc.SQUARE), # Venus cuadratura Mercurio
            (chart.MERCURY, chart.MARS, calc.SQUARE)   # Mercurio cuadratura Marte
        ]
        
        for natal_id, aspects in self.target_positions.items():
            for aspect_type, targets in aspects.items():
                # Verificar si esta es una combinación crítica
                is_critical = any((planet_id == p1 and natal_id == p2 and aspect_type == a) or 
                                 (planet_id == p2 and natal_id == p1 and aspect_type == a) 
                                 for p1, p2, a in critical_combinations)
                
                # Para combinaciones críticas, usar un orbe ligeramente mayor
                effective_orb = settings.default_orb * 1.1 if is_critical else settings.default_orb
                
                for target_degree, target_orb in targets:
                    crossings = self.interpolate_exact_time(ephemeris_data, target_degree, target_orb)
                    
                    for exact_time, movement, aspect_state, orb, planet_position in crossings:
                        # Solo incluir aspectos dentro del orbe permitido
                        if orb <= effective_orb:
                            transit_dates.append((
                                exact_time,
                                planet_id,
                                aspect_type,
                                natal_id,
                                movement,
                                aspect_state,
                                orb,
                                planet_position  # Posición exacta del planeta en el momento del tránsito
                            ))
        
        return transit_dates
    
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
        Utiliza criterios matemáticos y astronómicos sin ajustes manuales.
        
        Args:
            transit_dates: Lista de tuplas (fecha, planeta_id, aspecto, natal_id, movimiento, estado, orbe, posicion)
            
        Returns:
            Lista filtrada de tránsitos sin duplicados
        """
        # Diccionario para agrupar tránsitos por combinación planeta-aspecto-natal
        transit_groups = {}
        
        for transit in transit_dates:
            date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position = transit
            
            # Ignorar aspectos a puntos que no son planetas (como MC, IC, etc.)
            # Solo si natal_id no es un número (los IDs de planetas son números)
            if not isinstance(natal_id, int):
                continue
            
            # Clave única para cada combinación planeta-aspecto-natal
            key = (planet_id, natal_id, aspect_type)
            
            # Si ya existe un tránsito para esta combinación, verificar si este es más exacto
            if key in transit_groups:
                prev_transit = transit_groups[key]
                prev_orb = prev_transit[6]
                
                # Si este tránsito es más exacto (orbe menor), reemplazar el anterior
                if orb < prev_orb:
                    transit_groups[key] = transit
            else:
                # Si no existe un tránsito previo para esta combinación
                transit_groups[key] = transit
        
        # Recopilar todos los tránsitos filtrados
        filtered_transits = list(transit_groups.values())
        
        # Ordenar por fecha
        filtered_transits.sort(key=lambda x: x[0])
        
        return filtered_transits
    
    def calculate_all(self, start_date: datetime = None, end_date: datetime = None) -> list:
        """
        Calcula todos los tránsitos para el período especificado usando el enfoque optimizado.
        
        Args:
            start_date: Fecha inicial (default: 1 enero del año actual)
            end_date: Fecha final (default: 31 diciembre del año actual)
            
        Returns:
            Lista de eventos de tránsitos
        """
        # Si no se especifican fechas, usar el año actual completo
        if not start_date:
            start_date = datetime(datetime.now().year, 1, 1, tzinfo=ZoneInfo("UTC"))
        if not end_date:
            end_date = datetime(datetime.now().year, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))
        
        year = start_date.year
        
        # Precalcular posiciones objetivo
        start_time = time.time()
        print("\nCalculando tránsitos con método optimizado...")
        self.precompute_target_positions()
        
        # Procesar cada planeta en paralelo
        all_transits = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.find_transit_dates, planet, year) for planet in PLANETS_TO_CHECK]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    planet_transits = future.result()
                    all_transits.extend(planet_transits)
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
        print(f"\nCálculo optimizado completado en {elapsed:.2f} segundos")
        print(f"Total de eventos encontrados: {len(all_events)}")
        
        return all_events
