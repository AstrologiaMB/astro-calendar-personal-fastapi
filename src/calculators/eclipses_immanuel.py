"""
Calculador de eclipses utilizando la biblioteca Immanuel.
Proporciona cálculos de alta precisión para eclipses solares y lunares
utilizando directamente las funciones especializadas de Swiss Ephemeris.
"""
import swisseph as swe
from datetime import datetime
import math
import pytz
import ephem
from typing import List, Optional

from immanuel.tools import find
from immanuel.const import chart

from ..core.constants import EventType
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import calculate_planet_position

class ImmanuelEclipseCalculator:
    def __init__(self, observer, timezone_str="UTC"):
        """
        Inicializa el calculador de eclipses basado en Immanuel.
        
        Args:
            observer: Objeto observer de PyEphem (usado para calcular elevación y azimut)
            timezone_str: Zona horaria para conversión a hora local
        """
        self.observer = observer
        self.timezone_str = timezone_str
        # Extraer coordenadas del observador para cálculos de visibilidad
        self.latitude = float(self.observer.lat) * 180/math.pi
        self.longitude = float(self.observer.lon) * 180/math.pi
        self.elevation = float(self.observer.elevation)
        
        # Inicializar Swiss Ephemeris
        swe.set_ephe_path()  # Usar el path por defecto
        
    def calculate_eclipses(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """
        Calcula todos los eclipses solares y lunares en el período especificado
        utilizando las funciones especializadas de Immanuel/Swiss Ephemeris.
        
        Args:
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período
            
        Returns:
            Lista de eventos AstroEvent representando los eclipses
        """
        events = []
        
        # Calcular eclipses solares
        solar_eclipses = self._calculate_solar_eclipses(start_date, end_date)
        events.extend(solar_eclipses)
        
        # Calcular eclipses lunares
        lunar_eclipses = self._calculate_lunar_eclipses(start_date, end_date)
        events.extend(lunar_eclipses)
        
        # Ordenar eventos por fecha
        events.sort(key=lambda x: x.fecha_utc)
        
        return events
    
    def _calculate_solar_eclipses(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """
        Calcula eclipses solares usando la función next_solar_eclipse de Immanuel.
        """
        events = []
        
        # Convertir fechas a días julianos
        jd_start = julian_day(start_date)
        jd_end = julian_day(end_date)
        
        # Encontrar eclipses solares en el período
        jd = jd_start
        while jd < jd_end:
            # Buscar próximo eclipse solar
            eclipse_type, eclipse_jd = find.next_solar_eclipse(jd)
            
            if eclipse_jd >= jd_end:
                break
                
            # Convertir a datetime
            dt_tuple = swe.jdut1_to_utc(eclipse_jd)
            dt = datetime(dt_tuple[0], dt_tuple[1], dt_tuple[2], 
                         dt_tuple[3], dt_tuple[4], int(dt_tuple[5]))
            # Asegurarnos de que está en UTC
            dt = pytz.utc.localize(dt)
            
            # Calcular posición solar
            sun_pos = calculate_planet_position(eclipse_jd, swe.SUN)
            sign_num = int(sun_pos['longitude'] / 30)
            degree = sun_pos['longitude'] % 30
            sign = self._get_sign_name(sign_num)
            
            # Calcular elevación y azimut
            self.observer.date = dt.strftime('%Y/%m/%d %H:%M:%S')
            sun = ephem.Sun()
            sun.compute(self.observer)
            elevation = float(sun.alt) * 180/math.pi
            azimuth = float(sun.az) * 180/math.pi
            
            # Determinar visibilidad local
            if elevation > 0:
                visibilidad = "Visible localmente"
            else:
                visibilidad = "No visible localmente"
            
            # Mapear tipo de eclipse
            eclipse_type_str = self._map_eclipse_type(eclipse_type)
            
            # Crear evento
            events.append(AstroEvent(
                fecha_utc=dt,
                tipo_evento=EventType.ECLIPSE_SOLAR,
                descripcion=f"Eclipse Solar {eclipse_type_str} en {sign} {AstroEvent.format_degree(degree)} ({visibilidad})",
                elevacion=elevation,
                azimut=azimuth,
                longitud1=sun_pos['longitude'],
                signo=sign,
                grado=degree,
                visibilidad_local=visibilidad,
                timezone_str=self.timezone_str  # Usar la zona horaria del usuario
            ))
            
            # Avanzar al día siguiente
            jd = eclipse_jd + 1
        
        return events
        
    def _calculate_lunar_eclipses(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """
        Calcula eclipses lunares usando la función next_lunar_eclipse de Immanuel.
        """
        events = []
        
        # Convertir fechas a días julianos
        jd_start = julian_day(start_date)
        jd_end = julian_day(end_date)
        
        # Encontrar eclipses lunares en el período
        jd = jd_start
        while jd < jd_end:
            # Buscar próximo eclipse lunar
            eclipse_type, eclipse_jd = find.next_lunar_eclipse(jd)
            
            if eclipse_jd >= jd_end:
                break
                
            # Convertir a datetime
            dt_tuple = swe.jdut1_to_utc(eclipse_jd)
            dt = datetime(dt_tuple[0], dt_tuple[1], dt_tuple[2], 
                         dt_tuple[3], dt_tuple[4], int(dt_tuple[5]))
            # Asegurarnos de que está en UTC
            dt = pytz.utc.localize(dt)
            
            # Calcular posición lunar
            moon_pos = calculate_planet_position(eclipse_jd, swe.MOON)
            sign_num = int(moon_pos['longitude'] / 30)
            degree = moon_pos['longitude'] % 30
            sign = self._get_sign_name(sign_num)
            
            # Calcular elevación y azimut
            self.observer.date = dt.strftime('%Y/%m/%d %H:%M:%S')
            moon = ephem.Moon()
            moon.compute(self.observer)
            elevation = float(moon.alt) * 180/math.pi
            azimuth = float(moon.az) * 180/math.pi
            
            # Determinar visibilidad local
            if elevation > 0:
                visibilidad = "Visible localmente"
            else:
                visibilidad = "No visible localmente"
            
            # Mapear tipo de eclipse
            eclipse_type_str = self._map_eclipse_type(eclipse_type)
            
            # Crear evento
            events.append(AstroEvent(
                fecha_utc=dt,
                tipo_evento=EventType.ECLIPSE_LUNAR,
                descripcion=f"Eclipse Lunar {eclipse_type_str} en {sign} {AstroEvent.format_degree(degree)} ({visibilidad})",
                elevacion=elevation,
                azimut=azimuth,
                longitud1=moon_pos['longitude'],
                signo=sign,
                grado=degree,
                visibilidad_local=visibilidad,
                timezone_str=self.timezone_str  # Usar la zona horaria del usuario
            ))
            
            # Avanzar al día siguiente
            jd = eclipse_jd + 1
        
        return events
    
    def _map_eclipse_type(self, eclipse_type: int) -> str:
        """
        Mapea el tipo de eclipse de Immanuel a una cadena descriptiva.
        """
        if eclipse_type == chart.TOTAL:
            return "Total"
        elif eclipse_type == chart.ANNULAR:
            return "Anular"
        elif eclipse_type == chart.PARTIAL:
            return "Parcial"
        elif eclipse_type == chart.ANNULAR_TOTAL:
            return "Anular-Total"
        elif eclipse_type == chart.PENUMBRAL:
            return "Penumbral"
        else:
            return "Desconocido"
            
    def _get_sign_name(self, sign_num: int) -> str:
        """
        Obtiene el nombre del signo zodiacal.
        """
        from ..core.constants import AstronomicalConstants
        return AstronomicalConstants.SIGNS[sign_num]
