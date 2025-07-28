"""
Módulo unificado para calcular tránsitos planetarios usando immanuel.charts.Transits.
Versión paralela que divide el período en segmentos procesados simultáneamente.
"""
import json
import time
import concurrent.futures
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

class ParallelTransitsCalculator:
    def __init__(self, natal_data: dict, timezone_str: str = "UTC"):
        """
        Inicializa el calculador de tránsitos paralelo.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
            timezone_str: La zona horaria a usar para los eventos generados.
        """
        self.natal_data = natal_data
        self.timezone_str = timezone_str # Guardar la zona horaria
        
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

    def _create_time_segments(self, start_date: datetime, end_date: datetime, num_segments: int = 12):
        """
        Divide el período de tiempo en segmentos para procesamiento paralelo.
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            num_segments: Número de segmentos a crear
            
        Returns:
            Lista de tuplas (fecha_inicio, fecha_fin) para cada segmento
        """
        total_seconds = (end_date - start_date).total_seconds()
        segment_seconds = total_seconds / num_segments
        
        segments = []
        for i in range(num_segments):
            seg_start = start_date + timedelta(seconds=i * segment_seconds)
            # Para el último segmento, usar exactamente end_date para evitar errores de redondeo
            seg_end = end_date if i == num_segments - 1 else start_date + timedelta(seconds=(i + 1) * segment_seconds)
            segments.append((seg_start, seg_end))
            
        return segments

    def _calculate_segment(self, start_date: datetime, end_date: datetime, segment_id: int = 0):
        """
        Calcula los tránsitos para un segmento de tiempo específico.
        
        Args:
            start_date: Fecha inicial del segmento
            end_date: Fecha final del segmento
            segment_id: Identificador del segmento (para seguimiento)
            
        Returns:
            Lista de eventos de tránsitos para este segmento
        """
        transits_found = []
        last_transit = {}
        
        # Variables para seguimiento de progreso
        total_minutes = int((end_date - start_date).total_seconds() / 60)
        last_reported_progress = -1
        segment_start_time = time.time()
        
        # Búsqueda minuto a minuto
        current = start_date
        minute_count = 0
        
        while current <= end_date:
            # Calcular y mostrar progreso cada 5%
            minute_count += 1
            progress = int(minute_count * 100 / total_minutes)
            if progress > last_reported_progress and progress % 5 == 0:
                elapsed = time.time() - segment_start_time
                eta = (elapsed / (progress + 0.1)) * (100 - progress) if progress > 0 else 0
                print(f"Segmento {segment_id}: {progress}% ({current.strftime('%Y-%m-%d %H:%M')}) - "
                      f"Tiempo transcurrido: {elapsed:.1f}s - "
                      f"Tiempo restante estimado: {eta:.1f}s")
                last_reported_progress = progress
                
            # Procesar cada planeta transitante
            for planet_id in PLANETS_TO_CHECK:
                # Obtener posición del planeta transitante
                # Calcular JD desde J2000 (2000-01-01 12:00 UTC)
                j2000 = datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
                days_since_j2000 = (current - j2000).total_seconds() / 86400.0
                jd = 2451545.0 + days_since_j2000  # JD para J2000 es 2451545.0
                planet_data = ephemeris.planet(planet_id, jd)
                
                # Calcular aspectos con cada planeta natal
                for natal_obj_id in self.natal_positions:
                    # Verificar aspecto usando posición natal fija
                    self.check_aspect(planet_data, planet_id, natal_obj_id, None, 
                                   current, transits_found, last_transit)
            
            # Avanzar 1 minuto
            current += timedelta(minutes=1)
        
        # Ordenar por fecha y diferencia
        transits_found.sort(key=lambda x: (x['fecha'], x['diferencia']))
        
        # Convertir a objetos AstroEvent
        events = []
        for t in transits_found:
            # Crear descripción del evento
            descripcion = (f"{PLANET_NAMES[t['planeta']]} por tránsito, esta en {t['aspecto']} "
                         f"a tu {PLANET_NAMES[t['natal']]} Natal")
            
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
                },
                timezone_str=self.timezone_str # Pasar la zona horaria
            )
            events.append(event)
        
        print(f"Segmento {segment_id} completado: {len(events)} eventos encontrados")
        return events

    def calculate_all(self, start_date: datetime = None, end_date: datetime = None) -> list:
        """
        Calcula todos los tránsitos para el período especificado usando procesamiento paralelo.
        
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

        # Determinar el número óptimo de segmentos basado en los núcleos disponibles
        # Para M1, usamos 8 segmentos (uno por núcleo)
        num_segments = 8
        
        # Mostrar progreso inicial
        print("\nCalculando tránsitos con procesamiento paralelo...")
        print(f"Dividiendo el período en {num_segments} segmentos...")
        
        # Dividir el período en segmentos
        segments = self._create_time_segments(start_date, end_date, num_segments)
        
        # Registrar tiempo de inicio
        start_time = time.time()
        
        # Crear un pool de trabajadores para procesar los segmentos en paralelo
        all_events = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_segments) as executor:
            # Enviar cada segmento a un trabajador
            futures = [executor.submit(self._calculate_segment, seg_start, seg_end, i) 
                      for i, (seg_start, seg_end) in enumerate(segments)]
            
            # Recopilar resultados a medida que se completan
            for future in concurrent.futures.as_completed(futures):
                try:
                    segment_events = future.result()
                    all_events.extend(segment_events)
                except Exception as e:
                    print(f"Error en un segmento: {e}")
        
        # Ordenar todos los eventos por fecha
        all_events.sort(key=lambda x: x.fecha_utc)
        
        # Mostrar resumen
        elapsed = time.time() - start_time
        print(f"\nCálculo completado en {elapsed:.2f} segundos")
        print(f"Total de eventos encontrados: {len(all_events)}")
        
        return all_events
