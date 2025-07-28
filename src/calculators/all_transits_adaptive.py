"""
Módulo unificado para calcular tránsitos planetarios usando immanuel.charts.Transits.
Versión adaptativa que ajusta el intervalo de tiempo según la proximidad a aspectos.
"""
import json
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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
settings.exact_orb = 0.0001  # Aspecto exacto dentro de 0.0001° (aumentada precisión)

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

class AdaptiveTransitsCalculator:
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de tránsitos.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
        """
        self.natal_data = natal_data
        
        # Guardar datos natales
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

    def _distance_to_aspect(self, planet_lon, natal_lon, aspect_type):
        """
        Calcula la distancia angular al próximo aspecto exacto.
        """
        if aspect_type == calc.CONJUNCTION:
            aspect_lon = natal_lon
        elif aspect_type == calc.OPPOSITION:
            aspect_lon = (natal_lon + 180) % 360
        elif aspect_type == calc.SQUARE:
            # Para cuadraturas, hay dos posibles puntos
            sq1 = (natal_lon + 90) % 360
            sq2 = (natal_lon + 270) % 360
            
            # Calcular distancia a cada punto de cuadratura
            dist1 = min(abs(planet_lon - sq1), 360 - abs(planet_lon - sq1))
            dist2 = min(abs(planet_lon - sq2), 360 - abs(planet_lon - sq2))
            
            # Retornar la distancia más corta
            return min(dist1, dist2)
        
        # Calcular la distancia más corta en el círculo
        return min(abs(planet_lon - aspect_lon), 360 - abs(planet_lon - aspect_lon))

    def check_aspect(self, planet_data: dict, planet_id: int, natal_obj_id: int, 
                    natal_obj, current: datetime, transits_found: list, 
                    last_transit: dict) -> bool:
        """
        Verifica si hay un aspecto entre un planeta y un punto natal.
        """
        # Usar posición natal directamente
        natal_planet = {
            'index': natal_obj_id,
            'lon': self.natal_positions[natal_obj_id]['longitude'],
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
                key = f"{planet_id}-{natal_obj_id}-{aspect_data['aspect']}-{movement}"
                
                # Calcular diferencia orbital
                diferencia = abs(aspect_data['difference'])
                
                # Guardar el tránsito si es exacto o más preciso que el anterior
                if diferencia <= settings.exact_orb or (
                    key in last_transit and 
                    diferencia < last_transit[key]['diferencia'] and
                    aspect_data['movement'] == calc.EXACT
                ):
                    transit = {
                        "fecha": current,
                        "planeta": planet_id,
                        "aspecto": ASPECT_NAMES[aspect_data['aspect']],
                        "natal": natal_obj_id,
                        "posicion": planet_data['lon'],
                        "natal_pos": self.natal_positions[natal_obj_id]['longitude'],
                        "diferencia": diferencia,
                        "movimiento": calc.DIRECT if planet_data['speed'] > 0 else calc.RETROGRADE,
                        "estado": aspect_data['movement']
                    }
                    
                    # Actualizar o agregar el tránsito
                    if key in last_transit:
                        if diferencia < last_transit[key]['diferencia']:
                            for i, t in enumerate(transits_found):
                                if t == last_transit[key]:
                                    transits_found[i] = transit
                                    last_transit[key] = transit
                                    break
                    else:
                        transits_found.append(transit)
                        last_transit[key] = transit
                
                return True
        
        return False

    def _verify_near_aspect(self, time_point: datetime, transits_found: list, last_transit: dict):
        """
        Verifica con resolución de 1 minuto alrededor de un punto donde se detectó un aspecto cercano.
        
        Args:
            time_point: Punto central del período a verificar
            transits_found: Lista de tránsitos encontrados
            last_transit: Diccionario de últimos tránsitos por clave
        """
        # Verificar 30 minutos antes y después del punto de interés
        start = time_point - timedelta(minutes=30)
        end = time_point + timedelta(minutes=30)
        current = start
        
        while current <= end:
            # Procesar cada planeta transitante
            for planet_id in PLANETS_TO_CHECK:
                # Obtener posición del planeta transitante
                j2000 = datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
                days_since_j2000 = (current - j2000).total_seconds() / 86400.0
                jd = 2451545.0 + days_since_j2000
                planet_data = ephemeris.planet(planet_id, jd)
                
                # Calcular aspectos con cada planeta natal
                for natal_obj_id in self.natal_positions:
                    # Verificar aspecto usando posición natal fija
                    self.check_aspect(planet_data, planet_id, natal_obj_id, None, 
                                   current, transits_found, last_transit)
            
            # Avanzar 1 minuto
            current += timedelta(minutes=1)

    def calculate_all(self, start_date: datetime = None, end_date: datetime = None) -> list:
        """
        Calcula todos los tránsitos usando incrementos adaptativos para mayor eficiencia.
        
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

        transits_found = []
        last_transit = {}
        
        # Mostrar progreso inicial
        print("\nCalculando tránsitos con algoritmo adaptativo...")
        print("Esto puede tomar varios minutos...")
        
        # Variables para seguimiento de progreso
        total_time = (end_date - start_date).total_seconds()
        last_reported_progress = -1
        start_time = time.time()
        
        # Iniciar con incremento de 12 horas
        increment = timedelta(hours=12)
        current = start_date
        
        # Enfoque simplificado: una sola pasada con verificación adaptativa
        while current <= end_date:
            # Variable para rastrear el aspecto más cercano
            min_distance = float('inf')
            closest_planet_id = None
            closest_natal_id = None
            
            # Procesar cada planeta transitante
            for planet_id in PLANETS_TO_CHECK:
                # Obtener posición del planeta transitante
                j2000 = datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
                days_since_j2000 = (current - j2000).total_seconds() / 86400.0
                jd = 2451545.0 + days_since_j2000
                planet_data = ephemeris.planet(planet_id, jd)
                
                # Calcular aspectos con cada planeta natal
                for natal_obj_id in self.natal_positions:
                    # Verificar aspecto usando posición natal fija
                    aspect_found = self.check_aspect(planet_data, planet_id, natal_obj_id, None, 
                                   current, transits_found, last_transit)
                    
                    # Calcular distancia al próximo aspecto para cada tipo
                    for aspect_type in [calc.CONJUNCTION, calc.OPPOSITION, calc.SQUARE]:
                        distance = self._distance_to_aspect(
                            planet_data['lon'],
                            self.natal_positions[natal_obj_id]['longitude'],
                            aspect_type
                        )
                        
                        # Actualizar la distancia mínima
                        if distance < min_distance:
                            min_distance = distance
                            closest_planet_id = planet_id
                            closest_natal_id = natal_obj_id
            
            # Mostrar progreso
            progress = int((current - start_date).total_seconds() * 100 / total_time)
            if progress > last_reported_progress:
                elapsed = time.time() - start_time
                eta = (elapsed / (progress + 0.1)) * (100 - progress) if progress > 0 else 0
                
                print(f"Progreso: {progress}% ({current.strftime('%Y-%m-%d %H:%M')}) - "
                      f"Incremento actual: {increment} - "
                      f"Distancia mínima: {min_distance:.4f}° - "
                      f"Tiempo transcurrido: {elapsed:.1f}s - "
                      f"Tiempo restante estimado: {eta:.1f}s")
                last_reported_progress = progress
            
            # Determinar si estamos cerca de un aspecto importante
            is_mercury_aspect = closest_planet_id == chart.MERCURY
            is_venus_aspect = closest_planet_id == chart.VENUS
            is_sun_aspect = closest_planet_id == chart.SUN
            
            # Ajustar incremento basado en la proximidad al aspecto más cercano
            if min_distance <= 0.05:  # Muy cerca de un aspecto exacto
                increment = timedelta(minutes=1)
                # Verificar con resolución fina si estamos muy cerca
                self._verify_near_aspect(current, transits_found, last_transit)
            elif min_distance < 0.5:
                increment = timedelta(minutes=5)
                # Para Mercurio, usar incrementos más pequeños
                if is_mercury_aspect:
                    increment = timedelta(minutes=1)
                    self._verify_near_aspect(current, transits_found, last_transit)
            elif min_distance < 2.0:
                increment = timedelta(minutes=30)
                # Para planetas rápidos, usar incrementos más pequeños
                if is_mercury_aspect or is_venus_aspect:
                    increment = timedelta(minutes=10)
            elif min_distance < 5.0:
                increment = timedelta(hours=2)
                # Para planetas rápidos, usar incrementos más pequeños
                if is_mercury_aspect or is_venus_aspect:
                    increment = timedelta(minutes=30)
            else:
                increment = timedelta(hours=6)
            
            # Avanzar el tiempo usando el incremento adaptativo
            current += increment
            
            # Asegurar que no nos saltemos días completos
            # Si el incremento nos lleva a un nuevo día, ajustar para que sea el inicio del día
            next_day = (current.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
            if current > next_day and current - increment < next_day:
                current = next_day
        
        # Ordenar por fecha y diferencia
        transits_found.sort(key=lambda x: (x['fecha'], x['diferencia']))
        
        # Convertir a objetos AstroEvent
        events = []
        for t in transits_found:
            # Crear descripción del evento
            descripcion = (f"{PLANET_NAMES[t['planeta']]} {t['aspecto']} "
                         f"{PLANET_NAMES[t['natal']]} Natal")
            
            # Crear objeto AstroEvent
            event = AstroEvent(
                fecha_utc=t['fecha'],
                tipo_evento=EventType.ASPECTO,
                descripcion=descripcion,
                planeta1=PLANET_NAMES[t['planeta']],
                planeta2=PLANET_NAMES[t['natal']],
                longitud1=t['posicion'],
                longitud2=t['natal_pos'],
                tipo_aspecto=t['aspecto'],
                orbe=t['diferencia'],
                es_aplicativo=(t['estado'] == calc.APPLICATIVE),
                metadata={
                    'movimiento': MOVEMENT_NAMES[t['movimiento']],
                    'estado': ASPECT_STATE[t['estado']]
                }
            )
            events.append(event)
        
        return events
