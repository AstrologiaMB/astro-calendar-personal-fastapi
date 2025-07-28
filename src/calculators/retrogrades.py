from datetime import datetime, timedelta
from typing import List, Dict, Optional
import swisseph as swe
from ..core.constants import EventType, AstronomicalConstants
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import calculate_planet_position, format_position

class RetrogradeCalculator:
    def __init__(self, timezone_str: str = "UTC"):
        """
        Inicializa el calculador de retrogradaciones.
        
        Args:
            timezone_str: La zona horaria a usar para los eventos generados.
        """
        self.timezone_str = timezone_str
        self.processed_events = set()  # Para evitar duplicados

    def _calculate_speed(self, jd: float, planet_id: int) -> float:
        """Calcula la velocidad del planeta usando dos posiciones cercanas"""
        pos1 = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH)[0]
        pos2 = swe.calc_ut(jd + 1/24, planet_id, swe.FLG_SWIEPH)[0]  # 1 hora después
        
        # Manejar el cruce del punto 0°
        diff = pos2[0] - pos1[0]
        if abs(diff) > 180:
            if diff > 0:
                diff = diff - 360
            else:
                diff = diff + 360
                
        return diff * 24

    def _calculate_planet_position(self, date: datetime, planet_id: int) -> Dict:
        """Calcula posición y velocidad de un planeta"""
        jd = julian_day(date)
        result = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH)[0]
        speed = self._calculate_speed(jd, planet_id)
        
        return {
            'date': date,
            'longitude': result[0],
            'speed': speed,
            'position_str': format_position(result[0])
        }

    def _find_station_point(self, start_date: datetime, end_date: datetime, 
                           planet_name: str, is_retrograde_station: bool) -> Optional[Dict]:
        """Encuentra el punto exacto de estación de un planeta"""
        planet_id = AstronomicalConstants.PLANETS[planet_name][0]
        interval = AstronomicalConstants.RETROGRADE_SEARCH_INTERVALS[planet_name] / 4
        
        # Primera fase: búsqueda gruesa
        current_date = start_date
        best_date = None
        min_speed = float('inf')
        best_pos = None
        
        while current_date <= end_date:
            pos = self._calculate_planet_position(current_date, planet_id)
            speed = abs(pos['speed'])
            
            if speed < min_speed:
                min_speed = speed
                best_date = current_date
                best_pos = pos
            
            current_date += interval
        
        if not best_date:
            return None

        # Segunda fase: refinamiento con intervalos más pequeños
        refined_start = best_date - interval
        refined_end = best_date + interval
        interval = interval / 6  # Intervalo más fino
        
        current_date = refined_start
        min_speed = float('inf')
        
        while current_date <= refined_end:
            pos = self._calculate_planet_position(current_date, planet_id)
            speed = abs(pos['speed'])
            
            if speed < min_speed:
                min_speed = speed
                best_date = current_date
                best_pos = pos
            
            current_date += interval

        # Tercera fase: refinamiento final
        if best_date:
            final_start = best_date - timedelta(minutes=30)
            final_end = best_date + timedelta(minutes=30)
            interval = timedelta(seconds=30)
            
            current_date = final_start
            while current_date <= final_end:
                pos = self._calculate_planet_position(current_date, planet_id)
                speed = abs(pos['speed'])
                
                if speed < min_speed:
                    min_speed = speed
                    best_pos = pos
                
                current_date += interval
            
        return best_pos

    def calculate_retrogrades(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """Calcula períodos retrógrados de los planetas"""
        events = []

        for planet_name, (planet_id, _) in AstronomicalConstants.PLANETS.items():
            if planet_name in ['Sol', 'Luna']:  # Estos no retrogradan
                continue

            interval = AstronomicalConstants.RETROGRADE_SEARCH_INTERVALS[planet_name]
            current_date = start_date
            was_retrograde = None
            retro_start = None

            # Para Mercurio, usamos un intervalo más pequeño
            if planet_name == 'Mercurio':
                interval = timedelta(hours=4)

            while current_date < end_date:
                pos = self._calculate_planet_position(current_date, planet_id)
                is_retrograde = pos['speed'] < 0

                if was_retrograde is not None and is_retrograde != was_retrograde:
                    # Verificar tiempo mínimo entre estaciones para Mercurio
                    min_time = timedelta(days=30 if planet_name == 'Mercurio' else 60)
                    
                    if retro_start is None or (current_date - retro_start) >= min_time:
                        station = self._find_station_point(
                            current_date - interval,
                            current_date + interval,
                            planet_name,
                            is_retrograde
                        )

                        if station:
                            event_type = EventType.RETROGRADO_INICIO if is_retrograde else EventType.RETROGRADO_FIN
                            action = "inicia" if is_retrograde else "termina"

                            # Crear identificador único para el evento
                            event_id = f"{planet_name}_{event_type.value}_{station['date'].strftime('%Y-%m')}"
                            
                            if event_id not in self.processed_events:
                                events.append(AstroEvent(
                                    fecha_utc=station['date'],
                                    tipo_evento=event_type,
                                    descripcion=f"{planet_name} {action} retrogradación en {station['position_str']}",
                                    timezone_str=self.timezone_str # Pasar la zona horaria
                                ))
                                self.processed_events.add(event_id)
                                retro_start = station['date']

                was_retrograde = is_retrograde
                current_date += interval

        return sorted(events, key=lambda x: x.fecha_utc)
