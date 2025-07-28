"""
Calculador de eclipses de alta precisión utilizando exclusivamente Swiss Ephemeris
para determinar con exactitud los tiempos y características de eclipses solares y lunares.
"""
import swisseph as swe
from datetime import datetime
import math
import pytz
import ephem
from typing import List, Tuple, Optional, Dict

from ..core.constants import EventType
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import calculate_planet_position

class PreciseEclipseCalculator:
    def __init__(self, observer, timezone_str="UTC"):
        """
        Inicializa el calculador de eclipses de alta precisión.
        
        Args:
            observer: Objeto observer de PyEphem (usado solo para obtener coordenadas)
            timezone_str: Zona horaria para conversión a hora local
        """
        self.observer = observer
        self.timezone_str = timezone_str
        # Extraer coordenadas del observador para cálculos de Swiss Ephemeris
        self.latitude = float(self.observer.lat) * 180/math.pi
        self.longitude = float(self.observer.lon) * 180/math.pi
        self.elevation = float(self.observer.elevation)
        
        # Inicializar Swiss Ephemeris
        swe.set_ephe_path()  # Usar el path por defecto
        
    def calculate_eclipses(self, start_date: datetime, end_date: datetime, only_visible_solar: bool = False) -> List[AstroEvent]:
        """
        Calcula todos los eclipses solares y lunares en el período especificado
        utilizando las funciones especializadas de Swiss Ephemeris.
        
        Args:
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período
            only_visible_solar: Si es True, solo retorna eclipses solares visibles desde la ubicación del observador
            
        Returns:
            Lista de eventos AstroEvent representando los eclipses
        """
        events = []
        
        # Calcular eclipses lunares
        lunar_eclipses = self._calculate_lunar_eclipses(start_date, end_date)
        events.extend(lunar_eclipses)
        
        # Calcular eclipses solares
        solar_eclipses = self._calculate_solar_eclipses(start_date, end_date, only_visible_solar)
        events.extend(solar_eclipses)
        
        # Ordenar eventos por fecha
        events.sort(key=lambda x: x.fecha_utc)
        
        return events
    
    def _calculate_lunar_eclipses(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """
        Calcula eclipses lunares usando swe.lun_eclipse_when().
        """
        events = []
        
        # Convertir fechas a días julianos
        jd_start = julian_day(start_date)
        jd_end = julian_day(end_date)
        
        # Configurar flags para Swiss Ephemeris
        flags = swe.FLG_SWIEPH
        
        # Buscar eclipses lunares en el período
        jd = jd_start
        while jd < jd_end:
            # Buscar próximo eclipse lunar
            # La función lun_eclipse_when devuelve un entero y una lista de tiempos
            # El entero es un código de error (0 = OK)
            # La lista contiene los tiempos de las diferentes fases del eclipse
            eclipse_type = 0  # 0 = cualquier tipo de eclipse
            backwards = False  # Buscar hacia adelante en el tiempo
            ret_code, tret = swe.lun_eclipse_when(jd, flags, eclipse_type, backwards)
            
            if ret_code == 0:  # Si se encontró un eclipse
                eclipse_time = tret[0]  # Tiempo del máximo del eclipse
                if eclipse_time >= jd_end:
                    break
                
            # tret[0] contiene el tiempo juliano del máximo del eclipse
            # tret[3] contiene la magnitud del eclipse (umbral)
            # tret[4] contiene la magnitud del eclipse (penumbral)
            
            # Convertir tiempo juliano a datetime
            eclipse_time = swe.jdut1_to_utc(tret[0])
            dt = datetime(eclipse_time[0], eclipse_time[1], eclipse_time[2], 
                         eclipse_time[3], eclipse_time[4], int(eclipse_time[5]))
            dt = pytz.utc.localize(dt)
            
            # Determinar tipo de eclipse basado en magnitud
            eclipse_type = self._get_lunar_eclipse_type(tret[3])
            
            if eclipse_type:
                # Calcular posición lunar en el momento exacto
                moon_pos = calculate_planet_position(tret[0], swe.MOON)
                sign_num = int(moon_pos['longitude'] / 30)
                degree = moon_pos['longitude'] % 30
                sign = self._get_sign_name(sign_num)
                
                # Calcular distancia al nodo
                node_distance = self._calculate_node_distance(tret[0])
                
                # Calcular elevación y azimut
                # Necesitamos usar PyEphem para esto ya que Swiss Ephemeris no lo calcula directamente
                self.observer.date = dt.strftime('%Y/%m/%d %H:%M:%S')
                import ephem
                moon = ephem.Moon()
                moon.compute(self.observer)
                elevation = float(moon.alt) * 180/math.pi
                azimuth = float(moon.az) * 180/math.pi
                
                events.append(AstroEvent(
                    fecha_utc=dt,
                    tipo_evento=EventType.ECLIPSE_LUNAR,
                    descripcion=f"Eclipse Lunar {eclipse_type} en {sign} {AstroEvent.format_degree(degree)} (distancia al nodo: {node_distance:.1f}°)",
                    elevacion=elevation,
                    azimut=azimuth,
                    longitud1=moon_pos['longitude'],
                    signo=sign,
                    grado=degree,
                    visibilidad_local="Visible",  # Los eclipses lunares son generalmente visibles desde un hemisferio completo
                    timezone_str=self.timezone_str  # Usar la zona horaria del usuario
                ))
            
            # Avanzar al día siguiente del eclipse encontrado
            jd = tret[0] + 1
        
        return events
        
    def _calculate_solar_eclipses(self, start_date: datetime, end_date: datetime, only_visible: bool = False) -> List[AstroEvent]:
        """
        Calcula eclipses solares usando lunas nuevas y criterios geométricos.
        
        Args:
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período
            only_visible: Si es True, solo retorna eclipses visibles desde la ubicación del observador
            
        Returns:
            Lista de eventos AstroEvent representando los eclipses solares
        """
        events = []
        
        # Usar fechas de lunas nuevas para verificar eclipses
        date = ephem.Date(start_date)
        
        # Verificar eclipses solares en lunas nuevas
        while date < ephem.Date(end_date):
            next_new = ephem.next_new_moon(date)
            if next_new >= ephem.Date(end_date):
                break

            dt = ephem.Date(next_new).datetime()
            dt = pytz.utc.localize(dt)
            
            # Calcular parámetros del eclipse
            jd = julian_day(dt)
            
            # Obtener posiciones
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
            sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
            node_pos = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH)
            
            # Extraer longitud y latitud lunar
            moon_lon = moon_pos[0][0]  # Longitud lunar
            moon_lat = abs(moon_pos[0][1])  # Latitud lunar absoluta
            sun_lon = sun_pos[0][0]  # Longitud solar
            node_lon = node_pos[0][0]  # Longitud del nodo
            
            # Calcular distancia al nodo más cercano
            dist_to_north = abs(moon_lon - node_lon)
            dist_to_south = abs(moon_lon - (node_lon + 180))
            
            # Ajustar distancias mayores a 180°
            if dist_to_north > 180:
                dist_to_north = 360 - dist_to_north
            if dist_to_south > 180:
                dist_to_south = 360 - dist_to_south
            
            # Determinar la distancia al nodo más cercano
            if dist_to_north <= dist_to_south:
                node_distance = dist_to_north
                signed_distance = node_distance
            else:
                node_distance = dist_to_south
                signed_distance = -node_distance
            
            # Determinar tipo de eclipse según criterios geométricos
            eclipse_type = self._get_solar_eclipse_type_geometric(node_distance, moon_lat)
            
            if eclipse_type:
                # Calcular posición solar para el signo y grado
                sun_pos_dict = calculate_planet_position(jd, swe.SUN)
                sign_num = int(sun_pos_dict['longitude'] / 30)
                degree = sun_pos_dict['longitude'] % 30
                sign = self._get_sign_name(sign_num)
                
                # Calcular elevación y azimut
                self.observer.date = dt.strftime('%Y/%m/%d %H:%M:%S')
                sun = ephem.Sun()
                sun.compute(self.observer)
                elevation = float(sun.alt) * 180/math.pi
                azimuth = float(sun.az) * 180/math.pi
                
                # Determinar visibilidad local
                # Para simplificar, consideramos que un eclipse es visible localmente si el sol está sobre el horizonte
                if elevation > 0:
                    visibilidad = "Parcial"  # Por defecto, consideramos todos los eclipses visibles como parciales
                else:
                    visibilidad = "No visible localmente"
                
                # Si only_visible es True, solo incluir eclipses visibles localmente
                if only_visible and visibilidad == "No visible localmente":
                    pass  # No añadir este eclipse a la lista
                else:
                    # Crear descripción
                    descripcion = f"Eclipse Solar {eclipse_type} en {sign} {AstroEvent.format_degree(degree)} (distancia al nodo: {signed_distance:.1f}°)"
                    if visibilidad == "No visible localmente":
                        descripcion += f" - No visible desde {self.observer.name}"
                    
                    # Crear evento de eclipse solar
                    events.append(AstroEvent(
                        fecha_utc=dt,
                        tipo_evento=EventType.ECLIPSE_SOLAR,
                        descripcion=descripcion,
                        elevacion=elevation,
                        azimut=azimuth,
                        longitud1=sun_pos_dict['longitude'],
                        signo=sign,
                        grado=degree,
                        visibilidad_local=visibilidad,
                        timezone_str=self.timezone_str  # Usar la zona horaria del usuario
                    ))
            
            # Avanzar al día siguiente
            date = next_new + 1
        
        return events
        
    def _get_solar_eclipse_type_geometric(self, node_distance: float, moon_lat: float) -> Optional[str]:
        """
        Determina el tipo de eclipse solar según criterios geométricos.
        
        Args:
            node_distance: Distancia al nodo lunar más cercano en grados
            moon_lat: Latitud lunar absoluta en grados
            
        Returns:
            Tipo de eclipse o None si no hay eclipse
        """
        if node_distance > 18.5:
            return None
            
        if moon_lat > 1.5:
            return None
            
        if node_distance <= 10:
            if moon_lat <= 0.5:
                return "Total"
            elif moon_lat <= 0.9:
                return "Anular"
            elif moon_lat <= 1.2:
                return "Parcial"
        elif node_distance <= 18.5:
            return "Parcial"
            
        return None
        
    def _get_lunar_eclipse_type(self, magnitude: float) -> Optional[str]:
        """
        Determina el tipo de eclipse lunar basado en la magnitud.
        La magnitud es la fracción del diámetro lunar cubierta por la umbra.
        """
        if magnitude <= 0:
            return None
        elif magnitude >= 1.0:
            return "Total"
        elif magnitude >= 0.01:
            return "Parcial"
        else:
            return "Penumbral"

    def _get_solar_eclipse_type(self, eclipse_flags: int) -> Optional[str]:
        """
        Determina el tipo de eclipse solar basado en los flags de Swiss Ephemeris.
        """
        if eclipse_flags & swe.ECL_TOTAL:
            return "Total"
        elif eclipse_flags & swe.ECL_ANNULAR:
            return "Anular"
        elif eclipse_flags & swe.ECL_PARTIAL:
            return "Parcial"
        elif eclipse_flags & swe.ECL_ANNULAR_TOTAL:
            return "Anular-Total"
        else:
            return None

    def _calculate_node_distance(self, jd: float) -> float:
        """
        Calcula la distancia al nodo lunar más cercano.
        """
        # Obtener posiciones
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0]
        node_pos = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH)[0]
        
        # Calcular distancia al nodo más cercano
        moon_lon = moon_pos[0]
        node_lon = node_pos[0]
        
        dist_to_north = abs(moon_lon - node_lon)
        dist_to_south = abs(moon_lon - (node_lon + 180))
        
        # Ajustar distancias mayores a 180°
        if dist_to_north > 180:
            dist_to_north = 360 - dist_to_north
        if dist_to_south > 180:
            dist_to_south = 360 - dist_to_south
        
        # Determinar la distancia al nodo más cercano
        if dist_to_north <= dist_to_south:
            return dist_to_north
        else:
            return -dist_to_south  # Valor negativo para indicar nodo sur
            
    def _get_sign_name(self, sign_num: int) -> str:
        """
        Obtiene el nombre del signo zodiacal.
        """
        from ..core.constants import AstronomicalConstants
        return AstronomicalConstants.SIGNS[sign_num]
