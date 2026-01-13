from enum import Enum
import swisseph as swe
import ephem
from datetime import timedelta

class EventType(Enum):
    """Enumeración de tipos de eventos"""
    LUNA_LLENA = "Luna Llena"
    LUNA_NUEVA = "Luna Nueva"
    CUARTO_CRECIENTE = "Cuarto Creciente"
    CUARTO_MENGUANTE = "Cuarto Menguante"
    ECLIPSE_SOLAR = "Eclipse Solar"
    ECLIPSE_LUNAR = "Eclipse Lunar"
    INGRESO_SIGNO = "Ingreso a Signo"
    RETROGRADO_INICIO = "Inicio Retrogradación"
    RETROGRADO_FIN = "Fin Retrogradación"
    ASPECTO = "Aspecto"
    LUNA_PROGRESADA = "Luna Progresada"
    PROFECCION = "Profección"
    TRANSITO_CASA_ESTADO = "Tránsito Casa Estado"

class AstronomicalConstants:
    """Constantes astronómicas y mapeos"""
    # Lista simple de signos para compatibilidad con código existente
    SIGNS = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
             "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
    
    # Información detallada de signos para nuevas funcionalidades
    SIGNS_INFO = {
        "Aries": {"start": 0, "element": "Fuego", "quality": "Cardinal"},
        "Tauro": {"start": 30, "element": "Tierra", "quality": "Fijo"},
        "Géminis": {"start": 60, "element": "Aire", "quality": "Mutable"},
        "Cáncer": {"start": 90, "element": "Agua", "quality": "Cardinal"},
        "Leo": {"start": 120, "element": "Fuego", "quality": "Fijo"},
        "Virgo": {"start": 150, "element": "Tierra", "quality": "Mutable"},
        "Libra": {"start": 180, "element": "Aire", "quality": "Cardinal"},
        "Escorpio": {"start": 210, "element": "Agua", "quality": "Fijo"},
        "Sagitario": {"start": 240, "element": "Fuego", "quality": "Mutable"},
        "Capricornio": {"start": 270, "element": "Tierra", "quality": "Cardinal"},
        "Acuario": {"start": 300, "element": "Aire", "quality": "Fijo"},
        "Piscis": {"start": 330, "element": "Agua", "quality": "Mutable"}
    }

    PLANETS = {
        'Sol': (swe.SUN, ephem.Sun()),
        'Luna': (swe.MOON, ephem.Moon()),
        'Mercurio': (swe.MERCURY, ephem.Mercury()),
        'Venus': (swe.VENUS, ephem.Venus()),
        'Marte': (swe.MARS, ephem.Mars()),
        'Júpiter': (swe.JUPITER, ephem.Jupiter()),
        'Saturno': (swe.SATURN, ephem.Saturn()),
        'Urano': (swe.URANUS, ephem.Uranus()),
        'Neptuno': (swe.NEPTUNE, ephem.Neptune()),
        'Plutón': (swe.PLUTO, ephem.Pluto())
    }

    # Información planetaria extendida para aspectos
    # Orbe mínimo para aspectos partiles
    PLANETS_INFO = {
        'Sol': {
            'id': swe.SUN,
            'ephem_obj': ephem.Sun(),
            'mean_speed': 0.985,
            'orb_major': 0.1,  # 0.1 grados para aspectos partiles
            'orb_minor': 0.1,
            'dignity': {'Leo': 'Domicilio'}
        },
        'Luna': {
            'id': swe.MOON,
            'ephem_obj': ephem.Moon(),
            'mean_speed': 13.176,
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Cáncer': 'Domicilio'}
        },
        'Mercurio': {
            'id': swe.MERCURY,
            'ephem_obj': ephem.Mercury(),
            'mean_speed': [-1.4, 2.2],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Géminis': 'Domicilio', 'Virgo': 'Domicilio'}
        },
        'Venus': {
            'id': swe.VENUS,
            'ephem_obj': ephem.Venus(),
            'mean_speed': [-0.6, 1.2],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Tauro': 'Domicilio', 'Libra': 'Domicilio'}
        },
        'Marte': {
            'id': swe.MARS,
            'ephem_obj': ephem.Mars(),
            'mean_speed': [-0.4, 0.8],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Aries': 'Domicilio', 'Escorpio': 'Domicilio'}
        },
        'Júpiter': {
            'id': swe.JUPITER,
            'ephem_obj': ephem.Jupiter(),
            'mean_speed': [-0.1, 0.2],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Sagitario': 'Domicilio', 'Piscis': 'Domicilio'}
        },
        'Saturno': {
            'id': swe.SATURN,
            'ephem_obj': ephem.Saturn(),
            'mean_speed': [-0.05, 0.1],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Capricornio': 'Domicilio', 'Acuario': 'Domicilio'}
        },
        'Urano': {
            'id': swe.URANUS,
            'ephem_obj': ephem.Uranus(),
            'mean_speed': [-0.04, 0.04],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Acuario': 'Regente Moderno'}
        },
        'Neptuno': {
            'id': swe.NEPTUNE,
            'ephem_obj': ephem.Neptune(),
            'mean_speed': [-0.02, 0.02],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Piscis': 'Regente Moderno'}
        },
        'Plutón': {
            'id': swe.PLUTO,
            'ephem_obj': ephem.Pluto(),
            'mean_speed': [-0.01, 0.01],
            'orb_major': 0.1,
            'orb_minor': 0.1,
            'dignity': {'Escorpio': 'Regente Moderno'}
        }
    }

    RETROGRADE_SEARCH_INTERVALS = {
        'Mercurio': timedelta(hours=6),
        'Venus': timedelta(hours=12),
        'Marte': timedelta(days=1),
        'Júpiter': timedelta(days=2),
        'Saturno': timedelta(days=2),
        'Urano': timedelta(days=2),
        'Neptuno': timedelta(days=2),
        'Plutón': timedelta(days=2)
    }

    # Definición de aspectos exactos/partiles
    ASPECTS = {
        'Conjunción': {
            'angle': 0,
            'orb_factor': 1.0,  # Mantiene el orbe de 0.1 grados
            'harmony': 'Neutro'
        },
        'Sextil': {
            'angle': 60,
            'orb_factor': 1.0,
            'harmony': 'Armónico'
        },
        'Cuadratura': {
            'angle': 90,
            'orb_factor': 1.0,
            'harmony': 'Tensión'
        },
        'Trígono': {
            'angle': 120,
            'orb_factor': 1.0,
            'harmony': 'Armónico'
        },
        'Oposición': {
            'angle': 180,
            'orb_factor': 1.0,
            'harmony': 'Tensión'
        },
        # Aspectos detallados (Crecientes/Menguantes) para referencia
        'Sextil Creciente': { 'angle': 60, 'orb_factor': 1.0, 'harmony': 'Armónico' },
        'Cuadratura Creciente': { 'angle': 90, 'orb_factor': 1.0, 'harmony': 'Tensión' },
        'Trígono Creciente': { 'angle': 120, 'orb_factor': 1.0, 'harmony': 'Armónico' },
        'Trígono Menguante': { 'angle': 240, 'orb_factor': 1.0, 'harmony': 'Armónico' },
        'Cuadratura Menguante': { 'angle': 270, 'orb_factor': 1.0, 'harmony': 'Tensión' },
        'Sextil Menguante': { 'angle': 300, 'orb_factor': 1.0, 'harmony': 'Armónico' }
    }

    @classmethod
    def get_sign_name(cls, longitude: float) -> str:
        """Obtiene el nombre del signo para una longitud dada"""
        sign_num = int(longitude / 30) % 12
        return cls.SIGNS[sign_num]

    @classmethod
    def get_planet_id(cls, planet_name: str) -> int:
        """Obtiene el ID de Swiss Ephemeris para un planeta"""
        return cls.PLANETS[planet_name][0]
