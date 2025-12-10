import ephem
from datetime import datetime
import pytz
import math
from typing import List, Optional, Dict
from ..core.constants import EventType, AstronomicalConstants
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import calculate_planet_position
import swisseph as swe

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
    # Convertir posición de la luna a grados absolutos (ya viene en español)
    pos_luna = _convertir_a_grados_absolutos(signo, grado)
    
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
            if pos_luna >= inicio or pos_luna < fin:
                return casa_actual[0]
        # Caso normal
        elif inicio <= pos_luna < fin:
            return casa_actual[0]
    
    # Si no se encontró (no debería ocurrir)
    raise ValueError(f"No se pudo determinar la casa para {signo} {grado}°")

class LunarPhaseCalculator:
    def __init__(self, observer, timezone_str="UTC", natal_houses: Optional[Dict] = None):
        self.observer = observer
        self.timezone_str = timezone_str
        self.natal_houses = natal_houses

    def calculate_phases(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        events = []
        
        # Calcular lunas llenas
        date = ephem.Date(start_date)
        while date < ephem.Date(end_date):
            next_full = ephem.next_full_moon(date)
            if next_full >= ephem.Date(end_date):
                break

            self.observer.date = next_full
            moon = ephem.Moon()
            moon.compute(self.observer)

            dt = ephem.Date(next_full).datetime()
            dt = pytz.utc.localize(dt)

            # Calcular posición exacta para el signo y grado
            jd = julian_day(dt)
            moon_pos = calculate_planet_position(jd, swe.MOON)
            sign_num = int(moon_pos['longitude'] / 30)
            degree = moon_pos['longitude'] % 30
            signo_nombre = AstronomicalConstants.SIGNS[sign_num]

            # Calcular casa natal si tenemos los datos
            casa_natal = None
            descripcion = f"Luna llena en {signo_nombre} {AstroEvent.format_degree(degree)}"
            if self.natal_houses:
                try:
                    casa_natal = determinar_casa_natal(signo_nombre, degree, self.natal_houses)
                    descripcion = f"Luna llena en {signo_nombre} {AstroEvent.format_degree(degree)} en Casa {casa_natal}"
                except Exception as e:
                    print(f"Error calculando casa natal para Luna Llena: {e}")

            events.append(AstroEvent(
                fecha_utc=dt,
                tipo_evento=EventType.LUNA_LLENA,
                descripcion=descripcion,
                elevacion=float(moon.alt) * 180/math.pi,
                azimut=float(moon.az) * 180/math.pi,
                longitud1=moon_pos['longitude'],  # Agregar longitud para el CSV
                signo=signo_nombre,  # Agregar signo para el CSV
                grado=degree,  # Agregar grado para el CSV
                casa_natal=casa_natal,  # Agregar casa natal
                timezone_str=self.timezone_str  # Usar la zona horaria del usuario
            ))

            date = next_full + 1

        # Calcular cuartos crecientes
        date = ephem.Date(start_date)
        while date < ephem.Date(end_date):
            next_quarter = ephem.next_first_quarter_moon(date)
            if next_quarter >= ephem.Date(end_date):
                break

            self.observer.date = next_quarter
            moon = ephem.Moon()
            moon.compute(self.observer)

            dt = ephem.Date(next_quarter).datetime()
            dt = pytz.utc.localize(dt)

            # Calcular posición exacta para el signo y grado
            jd = julian_day(dt)
            moon_pos = calculate_planet_position(jd, swe.MOON)
            sign_num = int(moon_pos['longitude'] / 30)
            degree = moon_pos['longitude'] % 30
            signo_nombre = AstronomicalConstants.SIGNS[sign_num]

            # Calcular casa natal si tenemos los datos
            casa_natal = None
            descripcion = f"Cuarto Creciente en {signo_nombre} {AstroEvent.format_degree(degree)}"
            if self.natal_houses:
                try:
                    casa_natal = determinar_casa_natal(signo_nombre, degree, self.natal_houses)
                    descripcion = f"Cuarto Creciente en {signo_nombre} {AstroEvent.format_degree(degree)} en Casa {casa_natal}"
                except Exception as e:
                    print(f"Error calculando casa natal para Cuarto Creciente: {e}")

            events.append(AstroEvent(
                fecha_utc=dt,
                tipo_evento=EventType.CUARTO_CRECIENTE,
                descripcion=descripcion,
                elevacion=float(moon.alt) * 180/math.pi,
                azimut=float(moon.az) * 180/math.pi,
                longitud1=moon_pos['longitude'],
                signo=signo_nombre,
                grado=degree,
                casa_natal=casa_natal,
                timezone_str=self.timezone_str
            ))

            date = next_quarter + 1

        # Calcular cuartos menguantes
        date = ephem.Date(start_date)
        while date < ephem.Date(end_date):
            next_quarter = ephem.next_last_quarter_moon(date)
            if next_quarter >= ephem.Date(end_date):
                break

            self.observer.date = next_quarter
            moon = ephem.Moon()
            moon.compute(self.observer)

            dt = ephem.Date(next_quarter).datetime()
            dt = pytz.utc.localize(dt)

            # Calcular posición exacta para el signo y grado
            jd = julian_day(dt)
            moon_pos = calculate_planet_position(jd, swe.MOON)
            sign_num = int(moon_pos['longitude'] / 30)
            degree = moon_pos['longitude'] % 30
            signo_nombre = AstronomicalConstants.SIGNS[sign_num]

            # Calcular casa natal si tenemos los datos
            casa_natal = None
            descripcion = f"Cuarto Menguante en {signo_nombre} {AstroEvent.format_degree(degree)}"
            if self.natal_houses:
                try:
                    casa_natal = determinar_casa_natal(signo_nombre, degree, self.natal_houses)
                    descripcion = f"Cuarto Menguante en {signo_nombre} {AstroEvent.format_degree(degree)} en Casa {casa_natal}"
                except Exception as e:
                    print(f"Error calculando casa natal para Cuarto Menguante: {e}")

            events.append(AstroEvent(
                fecha_utc=dt,
                tipo_evento=EventType.CUARTO_MENGUANTE,
                descripcion=descripcion,
                elevacion=float(moon.alt) * 180/math.pi,
                azimut=float(moon.az) * 180/math.pi,
                longitud1=moon_pos['longitude'],
                signo=signo_nombre,
                grado=degree,
                casa_natal=casa_natal,
                timezone_str=self.timezone_str
            ))

            date = next_quarter + 1

        # Calcular lunas nuevas
        date = ephem.Date(start_date)
        while date < ephem.Date(end_date):
            next_new = ephem.next_new_moon(date)
            if next_new >= ephem.Date(end_date):
                break

            self.observer.date = next_new
            sun = ephem.Sun()
            sun.compute(self.observer)

            dt = ephem.Date(next_new).datetime()
            dt = pytz.utc.localize(dt)

            # Calcular posición exacta para el signo y grado
            jd = julian_day(dt)
            sun_pos = calculate_planet_position(jd, swe.SUN)
            sign_num = int(sun_pos['longitude'] / 30)
            degree = sun_pos['longitude'] % 30
            signo_nombre = AstronomicalConstants.SIGNS[sign_num]

            # Calcular casa natal si tenemos los datos
            casa_natal = None
            descripcion = f"Luna nueva en {signo_nombre} {AstroEvent.format_degree(degree)}"
            if self.natal_houses:
                try:
                    casa_natal = determinar_casa_natal(signo_nombre, degree, self.natal_houses)
                    descripcion = f"Luna nueva en {signo_nombre} {AstroEvent.format_degree(degree)} en Casa {casa_natal}"
                except Exception as e:
                    print(f"Error calculando casa natal para Luna Nueva: {e}")

            events.append(AstroEvent(
                fecha_utc=dt,
                tipo_evento=EventType.LUNA_NUEVA,
                descripcion=descripcion,
                elevacion=float(sun.alt) * 180/math.pi,
                azimut=float(sun.az) * 180/math.pi,
                longitud1=sun_pos['longitude'],  # Agregar longitud para el CSV
                signo=signo_nombre,  # Agregar signo para el CSV
                grado=degree,  # Agregar grado para el CSV
                casa_natal=casa_natal,  # Agregar casa natal
                timezone_str=self.timezone_str  # Usar la zona horaria del usuario
            ))

            date = next_new + 1

        return events
