"""
Módulo para detectar conjunciones entre lunas llenas y el sol natal.

Este módulo analiza las lunas llenas del año y determina cuáles forman una conjunción
con el sol natal, considerando un orbe configurable (por defecto 8°).

Ejemplo de uso:
    generate_sun_fullmoon_conjunctions_report(
        natal_file='carta_natal_buenos_aires.json',
        events_file='eventos_astronomicos_2025_BuenosAires.csv',
        max_orb=8.0
    )

El módulo:
1. Lee la posición del sol natal del archivo JSON
2. Lee todas las lunas llenas del archivo CSV
3. Convierte las posiciones a grados absolutos (0-360°)
4. Calcula el orbe entre cada luna llena y el sol natal
5. Genera un reporte CSV con las conjunciones encontradas

Para el año 2025, con sol natal en Capricornio 05°16'45" (275.28°):
- Luna llena del 05/01 en Cáncer 15°29' (105.48°)
  -> Orbe: 169.8° (no es conjunción, es oposición)
"""
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from src.core import config
from src.utils.time_utils import julian_day

def generate_sun_fullmoon_conjunctions_report(
    natal_file: str,
    events_file: str,
    person_name: str,
    max_orb: float = 8.0,
    eclipse_calculator = None
) -> str:
    """
    Genera un reporte de conjunciones entre lunas llenas y el sol natal.
    
    Args:
        natal_file: Ruta al archivo JSON con la carta natal
        events_file: Ruta al archivo CSV con los eventos astronómicos
        output_file: Ruta donde guardar el archivo de salida
        max_orb: Orbe máximo permitido en grados (default: 8°)
    """
    # Extraer el año del nombre del archivo usando expresión regular
    year_match = re.search(r'_(\d{4})(?:_|\.)', events_file)
    if not year_match:
        raise ValueError(f"No se pudo extraer el año del archivo: {events_file}")
    year = int(year_match.group(1))
    
    # Cargar posición del sol natal
    with open(natal_file, 'r') as f:
        natal_data = json.load(f)
        sun_sign = natal_data['points']['Sun']['sign']
        sun_pos = _parsear_posicion(natal_data['points']['Sun']['position'])
        sun_abs = _convertir_a_grados_absolutos(sun_sign, sun_pos, desde_ingles=True)
    
    # Cargar datos de lunas llenas
    full_moons = []
    with open(events_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['tipo_evento'] == 'Luna Llena':
                # Extraer solo el grado numérico de la posición
                grado = float(row['grado'].split('°')[0])
                fecha_utc = datetime.strptime(row['fecha_utc'], '%Y-%m-%d')
                jd = julian_day(fecha_utc)
                
                # Verificar si es eclipse
                eclipse_info = None
                if eclipse_calculator:
                    eclipse_info = eclipse_calculator.is_eclipse(jd)
                
                full_moons.append({
                    'fecha': row['fecha_local'],
                    'hora': row['hora_local'],
                    'signo': row['signo'],
                    'grado': grado,
                    'eclipse': eclipse_info
                })
    
    # Buscar conjunciones
    conjunctions = []
    for moon in full_moons:
        moon_abs = _convertir_a_grados_absolutos(moon['signo'], moon['grado'])
        orb = _calcular_orbe(sun_abs, moon_abs)
        
        if orb <= max_orb:
            conjunctions.append({
                'fecha': moon['fecha'],
                'hora': moon['hora'],
                'signo': moon['signo'],
                'grado': moon['grado'],
                'orbe': orb,
                'eclipse': moon.get('eclipse')  # Usar .get() para manejar casos donde no existe
            })
    
    # Separar conjunciones normales y eclipses
    normal_conjunctions = []
    eclipse_conjunctions = []
    
    for moon in conjunctions:
        if moon.get('eclipse'):  # Usar .get() para manejar casos donde no existe
            eclipse_conjunctions.append(moon)
        else:
            normal_conjunctions.append(moon)
    
    # Generar reporte de lunas llenas normales
    output_file = config.get_report_filename('sunlunallena', person_name)
    _write_conjunctions_report(output_file, normal_conjunctions, False, year)
    
    # Generar reporte de eclipses
    if eclipse_conjunctions:
        eclipse_file = config.get_eclipse_report_filename('lunar', 'sun', person_name)
        _write_conjunctions_report(eclipse_file, eclipse_conjunctions, True, year)
    
    return output_file

def _write_conjunctions_report(filename: str, conjunctions: List[Dict], is_eclipse: bool, year: int):
    """Escribe el reporte de conjunciones en un archivo CSV."""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Fecha', 'Hora', 'Posición', 'Descripción', 'Orbe'])
        
        if not conjunctions:
            msg = 'No hay conjunción sol natal con eclipse lunar' if is_eclipse else 'No hay conjunción sol natal con luna llena'
            writer.writerow(['', '', '', f'{msg} durante el año {year}', ''])
        else:
            for conj in conjunctions:
                if is_eclipse:
                    tipo_eclipse = conj['eclipse'][1]  # Total, Parcial, Penumbral
                    desc = (f"El dia {conj['fecha']} y hora {conj['hora']} el Eclipse Lunar {tipo_eclipse} y el sol natal estan en conjunción "
                           f"en el signo {conj['signo']} y grado {conj['grado']:.2f}")
                else:
                    desc = (f"El dia {conj['fecha']} y hora {conj['hora']} la luna llena y el sol natal estan en conjunción "
                           f"en el signo {conj['signo']} y grado {conj['grado']:.2f}")
                
                writer.writerow([
                    conj['fecha'],
                    conj['hora'],
                    f"{conj['signo']} {conj['grado']:.2f}°",
                    desc,
                    f"{conj['orbe']:.2f}°"
                ])
    
    return filename

def _convertir_a_grados_absolutos(signo: str, grado: float, desde_ingles: bool = False) -> float:
    """
    Convierte una posición zodiacal (signo y grado) a grados absolutos (0-360).
    
    Args:
        signo: Nombre del signo zodiacal
        grado: Grado dentro del signo
        desde_ingles: True si el signo está en inglés y hay que traducirlo a español
    """
    # Mapeo de signos a su posición base (0-330)
    SIGNOS_BASE = {
        # Inglés
        'Aries': 0, 'Taurus': 30, 'Gemini': 60, 'Cancer': 90,
        'Leo': 120, 'Virgo': 150, 'Libra': 180, 'Scorpio': 210,
        'Sagittarius': 240, 'Capricorn': 270, 'Aquarius': 300, 'Pisces': 330,
        # Español
        'Aries': 0, 'Tauro': 30, 'Géminis': 60, 'Cáncer': 90,
        'Leo': 120, 'Virgo': 150, 'Libra': 180, 'Escorpio': 210,
        'Sagitario': 240, 'Capricornio': 270, 'Acuario': 300, 'Piscis': 330
    }
    
    return SIGNOS_BASE[signo] + grado

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

def _calcular_orbe(pos1: float, pos2: float) -> float:
    """
    Calcula el orbe más corto entre dos posiciones zodiacales.
    Considera el cruce por 0°/360°.
    
    Por ejemplo:
    - Sol natal en Capricornio 5° (275°) y Luna llena en Capricornio 2° (272°)
      -> Diferencia directa: |275° - 272°| = 3° (es conjunción)
    - Sol natal en Capricornio 5° (275°) y Luna llena en Cáncer 15° (105°)
      -> Diferencia directa: |275° - 105°| = 170° (no es conjunción, es oposición)
    - Sol natal en Aries 2° (2°) y Luna llena en Piscis 28° (358°)
      -> Diferencia aparente: |2° - 358°| = 356°
      -> Diferencia real: 360° - 356° = 4° (es conjunción)
    """
    # Calcular diferencia directa
    diff = abs(pos1 - pos2)
    
    # Si la diferencia es mayor a 180°, hay un camino más corto
    if diff > 180:
        diff = 360 - diff
    
    return diff
