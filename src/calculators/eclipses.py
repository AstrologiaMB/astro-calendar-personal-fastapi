import swisseph as swe
from datetime import datetime
import math
import ephem
import pytz
from typing import List, Tuple, Optional, Dict
from ..core.constants import EventType
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import calculate_planet_position

class EclipseCalculator:
    def __init__(self, observer, timezone_str="UTC", natal_houses: Optional[Dict] = None):
        self.observer = observer
        self.timezone_str = timezone_str
        self.natal_houses = natal_houses

    def calculate_eclipses(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        events = []
        
        # Usar fechas de lunas llenas y nuevas para verificar eclipses
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
            node_distance, eclipse_type = self._get_node_distance_and_type(jd, True)
            
            if eclipse_type:
                self.observer.date = next_new
                sun = ephem.Sun()
                sun.compute(self.observer)
                
                sun_pos = calculate_planet_position(jd, swe.SUN)
                sign_num = int(sun_pos['longitude'] / 30)
                degree = sun_pos['longitude'] % 30
                sign = self._get_sign_name(sign_num)
                
                # Determinar casa natal si se proporcionaron las casas
                casa_natal = None
                if self.natal_houses:
                    casa_natal = determinar_casa_natal(sign, degree, self.natal_houses)
                
                # Crear descripción con casa natal si está disponible
                descripcion = f"Eclipse Solar {eclipse_type} en {sign} {AstroEvent.format_degree(degree)}"
                if casa_natal:
                    descripcion += f" en Casa {casa_natal}"
                descripcion += f" (distancia al nodo: {node_distance:.1f}°)"
                
                events.append(AstroEvent(
                    fecha_utc=dt,
                    tipo_evento=EventType.ECLIPSE_SOLAR,
                    descripcion=descripcion,
                    elevacion=float(sun.alt) * 180/math.pi,
                    azimut=float(sun.az) * 180/math.pi,
                    longitud1=sun_pos['longitude'],
                    signo=sign,
                    grado=degree,
                    casa_natal=casa_natal,
                    timezone_str=self.timezone_str
                ))
            
            date = next_new + 1
        
        # Verificar eclipses lunares en lunas llenas
        date = ephem.Date(start_date)
        while date < ephem.Date(end_date):
            next_full = ephem.next_full_moon(date)
            if next_full >= ephem.Date(end_date):
                break

            dt = ephem.Date(next_full).datetime()
            dt = pytz.utc.localize(dt)
            
            # Calcular parámetros del eclipse
            jd = julian_day(dt)
            node_distance, eclipse_type = self._get_node_distance_and_type(jd, False)
            
            if eclipse_type:
                self.observer.date = next_full
                moon = ephem.Moon()
                moon.compute(self.observer)
                
                moon_pos = calculate_planet_position(jd, swe.MOON)
                sign_num = int(moon_pos['longitude'] / 30)
                degree = moon_pos['longitude'] % 30
                sign = self._get_sign_name(sign_num)
                
                # Determinar casa natal si se proporcionaron las casas
                casa_natal = None
                if self.natal_houses:
                    casa_natal = determinar_casa_natal(sign, degree, self.natal_houses)
                
                # Crear descripción con casa natal si está disponible
                descripcion = f"Eclipse Lunar {eclipse_type} en {sign} {AstroEvent.format_degree(degree)}"
                if casa_natal:
                    descripcion += f" en Casa {casa_natal}"
                descripcion += f" (distancia al nodo: {node_distance:.1f}°)"
                
                events.append(AstroEvent(
                    fecha_utc=dt,
                    tipo_evento=EventType.ECLIPSE_LUNAR,
                    descripcion=descripcion,
                    elevacion=float(moon.alt) * 180/math.pi,
                    azimut=float(moon.az) * 180/math.pi,
                    longitud1=moon_pos['longitude'],
                    signo=sign,
                    grado=degree,
                    casa_natal=casa_natal,
                    timezone_str=self.timezone_str
                ))
            
            date = next_full + 1
        
        return events

    def is_eclipse(self, jd: float) -> Optional[Tuple[str, str]]:
        """
        Determina si hay un eclipse en la fecha dada.
        
        Args:
            jd: Fecha juliana a verificar
            
        Returns:
            None si no hay eclipse, o una tupla (tipo, descripción) si hay eclipse
            tipo: 'ECLIPSE_SOLAR' o 'ECLIPSE_LUNAR'
            descripción: 'Total', 'Anular', 'Parcial' o 'Penumbral'
        """
        # Obtener posiciones
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0]
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0]
        
        # Calcular elongación para determinar si es luna nueva o llena
        elong = abs(moon_pos[0] - sun_pos[0])
        if elong > 180:
            elong = 360 - elong
            
        is_solar = elong < 10  # Luna nueva
        
        # Obtener distancia nodal y tipo
        node_distance, eclipse_type = self._get_node_distance_and_type(jd, is_solar)
        
        if eclipse_type:
            tipo = 'ECLIPSE_SOLAR' if is_solar else 'ECLIPSE_LUNAR'
            return (tipo, eclipse_type)
            
        return None

    def _get_node_distance_and_type(self, jd: float, is_solar: bool) -> Tuple[float, Optional[str]]:
        """Calcula la distancia al nodo lunar y determina el tipo de eclipse"""
        # Obtener posiciones
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0]
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0]
        node_pos = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH)[0]
        
        # Cálculos básicos
        moon_lon = moon_pos[0]
        moon_lat = abs(moon_pos[1])  # Latitud lunar absoluta
        sun_lon = sun_pos[0]
        node_lon = node_pos[0]
        
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
        
        # Determinar tipo de eclipse según criterios
        if is_solar:
            return self._get_solar_eclipse_type(node_distance, moon_lat, signed_distance)
        else:
            return self._get_lunar_eclipse_type(node_distance, moon_lat, sun_lon, moon_lon, signed_distance)

    def _get_solar_eclipse_type(self, node_distance: float, moon_lat: float, signed_distance: float) -> Tuple[float, Optional[str]]:
        """Determina el tipo de eclipse solar"""
        if node_distance > 18.5:
            return signed_distance, None
            
        if moon_lat > 1.5:
            return signed_distance, None
            
        if node_distance <= 10:
            if moon_lat <= 0.5:
                return signed_distance, "Total"
            elif moon_lat <= 0.9:
                return signed_distance, "Anular"
            elif moon_lat <= 1.2:
                return signed_distance, "Parcial"
        elif node_distance <= 18.5:
            return signed_distance, "Parcial"
            
        return signed_distance, None

    def _get_lunar_eclipse_type(self, node_distance: float, moon_lat: float, sun_lon: float, 
                              moon_lon: float, signed_distance: float) -> Tuple[float, Optional[str]]:
        """Determina el tipo de eclipse lunar"""
        if node_distance > 12.5:
            return signed_distance, None
            
        if moon_lat > 1.0:
            return signed_distance, None
            
        elong = abs(moon_lon - (sun_lon + 180))
        if elong > 180:
            elong = 360 - elong
            
        # Ajustado según Astroseek
        if node_distance <= 4.0:  # Aumentado de 3.8 a 4.0
            if moon_lat <= 0.5:
                return signed_distance, "Total"
            elif moon_lat <= 0.7:
                return signed_distance, "Parcial"
        elif node_distance <= 6:
            if moon_lat <= 0.85:
                return signed_distance, "Parcial"
        elif node_distance <= 12.5:
            if moon_lat <= 1.0 and elong >= 175:
                return signed_distance, "Penumbral"
                
        return signed_distance, None

    def _get_sign_name(self, sign_num: int) -> str:
        """Obtiene el nombre del signo zodiacal"""
        from ..core.constants import AstronomicalConstants
        return AstronomicalConstants.SIGNS[sign_num]


# Mapeo de nombres de signos inglés-español
SIGN_TRANSLATIONS = {
    # Inglés a Español
    'Aries': 'Aries',
    'Taurus': 'Tauro',
    'Gemini': 'Géminis',
    'Cancer': 'Cáncer',
    'Leo': 'Leo',
    'Virgo': 'Virgo',
    'Libra': 'Libra',
    'Scorpio': 'Escorpio',
    'Sagittarius': 'Sagitario',
    'Capricorn': 'Capricornio',
    'Aquarius': 'Acuario',
    'Pisces': 'Piscis',
    # Español a Inglés
    'Tauro': 'Taurus',
    'Géminis': 'Gemini',
    'Cáncer': 'Cancer',
    'Escorpio': 'Scorpio',
    'Sagitario': 'Sagittarius',
    'Capricornio': 'Capricorn',
    'Acuario': 'Aquarius',
    'Piscis': 'Pisces'
}

# Lista ordenada de signos en español
SIGNOS = [
    'Aries', 'Tauro', 'Géminis', 'Cáncer', 'Leo', 'Virgo',
    'Libra', 'Escorpio', 'Sagitario', 'Capricornio', 'Acuario', 'Piscis'
]

def _convertir_a_grados_absolutos(signo: str, grado: float, desde_ingles: bool = False) -> float:
    """
    Convierte una posición zodiacal (signo y grado) a grados absolutos (0-360).
    
    Args:
        signo: Nombre del signo zodiacal
        grado: Grado dentro del signo
        desde_ingles: True si el signo está en inglés y hay que traducirlo a español
    """
    # Si el signo está en inglés y hay que traducirlo
    if desde_ingles:
        signo = SIGN_TRANSLATIONS.get(signo, signo)
    return SIGNOS.index(signo) * 30 + grado

def _parsear_posicion(posicion: str) -> float:
    """
    Convierte una posición en formato '27°45\'16"' a grados decimales.
    """
    # Eliminar caracteres especiales
    partes = posicion.replace('°', ' ').replace('\'', ' ').replace('"', ' ').split()
    grados = float(partes[0])
    minutos = float(partes[1]) if len(partes) > 1 else 0
    segundos = float(partes[2]) if len(partes) > 2 else 0
    return grados + minutos/60 + segundos/3600

def determinar_casa_natal(signo: str, grado: float, casas: dict) -> int:
    """
    Determina en qué casa natal cae una posición zodiacal.
    
    Args:
        signo: Nombre del signo zodiacal (en español)
        grado: Grado dentro del signo
        casas: Diccionario con los datos de las casas natales
        
    Returns:
        Número de la casa natal (1-12)
    """
    # Convertir posición del eclipse a grados absolutos (ya viene en español)
    pos_eclipse = _convertir_a_grados_absolutos(signo, grado)
    
    # Convertir posiciones de las casas a grados absolutos
    casas_abs = {}
    for num, datos in casas.items():
        pos_abs = _convertir_a_grados_absolutos(
            datos['sign'],
            _parsear_posicion(datos['position']),
            desde_ingles=True  # Las casas vienen en inglés del JSON
        )
        casas_abs[int(num)] = pos_abs
    
    # Mantener el orden original de las casas (1-12)
    casas_ordenadas = [(i, casas_abs[i]) for i in range(1, 13)]
    
    # Para cada casa, determinar si el punto está entre su inicio y el inicio de la siguiente
    for i in range(len(casas_ordenadas)):
        casa_actual = casas_ordenadas[i]
        casa_siguiente = casas_ordenadas[(i + 1) % 12]
        
        inicio = casa_actual[1]
        fin = casa_siguiente[1]
        
        # Si la casa cruza 0°
        if fin < inicio:
            # Si la posición está después del inicio o antes del fin
            if pos_eclipse >= inicio or pos_eclipse < fin:
                return casa_actual[0]
        # Caso normal
        elif inicio <= pos_eclipse < fin:
            return casa_actual[0]
    
    # Si no se encontró (no debería ocurrir)
    raise ValueError(f"No se pudo determinar la casa para {signo} {grado}°")
