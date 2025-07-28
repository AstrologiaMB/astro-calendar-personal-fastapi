"""
Módulo para detectar conjunciones entre lunas nuevas y el Sol natal.

Este módulo analiza las lunas nuevas del año y determina cuáles forman una conjunción
con el Sol natal, considerando un orbe configurable (por defecto 8°).

Ejemplo de uso:
    generate_sun_newmoon_conjunctions_report(
        natal_file='carta_natal_buenos_aires.json',
        events_file='eventos_astronomicos_2025_BuenosAires.csv',
        max_orb=8.0
    )

El módulo:
1. Lee la posición del Sol natal del archivo JSON
2. Lee todas las lunas nuevas del archivo CSV
3. Convierte las posiciones a grados absolutos (0-360°)
4. Calcula el orbe entre cada luna nueva y el Sol natal
5. Genera un reporte CSV con las conjunciones encontradas

Para el año 2025, con Sol natal en Capricornio 5°16'45" (275.28°):
- Luna nueva del 29/12 en Capricornio 7°39' (277.65°)
  -> Orbe: 2.37° (dentro del límite de 8°)
"""
import json
import csv
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from src.core import config
from src.utils.time_utils import julian_day

def generate_sun_newmoon_conjunctions_report(
    natal_file: str,
    events_file: str,
    person_name: str,
    max_orb: float = 8.0,
    eclipse_calculator = None
) -> str:
    """
    Genera un reporte de conjunciones entre lunas nuevas y el Sol natal.
    
    Args:
        natal_file: Ruta al archivo JSON con la carta natal
        events_file: Ruta al archivo CSV con los eventos astronómicos
        output_file: Ruta donde guardar el archivo de salida
        max_orb: Orbe máximo permitido en grados (default: 8°)
    """
    # Cargar posición del Sol natal
    with open(natal_file, 'r') as f:
        natal_data = json.load(f)
        sun_sign = natal_data['points']['Sun']['sign']
        sun_pos = _parsear_posicion(natal_data['points']['Sun']['position'])
        sun_abs = _convertir_a_grados_absolutos(sun_sign, sun_pos, desde_ingles=True)
    
    # Cargar datos de lunas nuevas
    new_moons = []
    with open(events_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['tipo_evento'] == 'Luna Nueva':
                # Extraer solo el grado numérico de la posición
                grado = float(row['grado'].split('°')[0])
                fecha_utc = datetime.strptime(row['fecha_utc'], '%Y-%m-%d')
                jd = julian_day(fecha_utc)
                
                # Verificar si es eclipse
                eclipse_info = None
                if eclipse_calculator:
                    eclipse_info = eclipse_calculator.is_eclipse(jd)
                
                new_moons.append({
                    'fecha': row['fecha_local'],
                    'hora': row['hora_local'],
                    'signo': row['signo'],
                    'grado': grado,
                    'eclipse': eclipse_info
                })
    
    # Buscar conjunciones
    conjunctions = []
    for moon in new_moons:
        moon_abs = _convertir_a_grados_absolutos(moon['signo'], moon['grado'])
        orb = _calcular_orbe(sun_abs, moon_abs)
        
        if orb <= max_orb:
            conjunctions.append({
                'fecha': moon['fecha'],
                'hora': moon['hora'],
                'signo': moon['signo'],
                'grado': moon['grado'],
                'orbe': orb,
                'eclipse': moon['eclipse']
            })
    
    # Separar conjunciones normales y eclipses
    normal_conjunctions = []
    eclipse_conjunctions = []
    
    for moon in conjunctions:
        if moon['eclipse']:
            eclipse_conjunctions.append(moon)
        else:
            normal_conjunctions.append(moon)
    
    # Generar reporte de lunas nuevas normales
    output_file = config.get_report_filename('sollunanueva', person_name)
    _write_conjunctions_report(output_file, normal_conjunctions, False)
    
    # Generar reporte de eclipses
    if eclipse_conjunctions:
        eclipse_file = config.get_eclipse_report_filename('solar', 'sun', person_name)
        _write_conjunctions_report(eclipse_file, eclipse_conjunctions, True)
    
    return output_file

def _write_conjunctions_report(filename: str, conjunctions: List[Dict], is_eclipse: bool):
    """Escribe el reporte de conjunciones en un archivo CSV."""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Fecha', 'Hora', 'Posición', 'Descripción', 'Orbe'])
        
        if not conjunctions:
            msg = 'No hay conjunción Sol natal con eclipse solar' if is_eclipse else 'No hay conjunción Sol natal con luna nueva'
            writer.writerow(['', '', '', f'{msg} durante el año 2025', ''])
        else:
            for conj in conjunctions:
                if is_eclipse:
                    tipo_eclipse = conj['eclipse'][1]  # Total, Parcial, Anular
                    desc = (f"El dia {conj['fecha']} y hora {conj['hora']} el Eclipse Solar {tipo_eclipse} y el Sol natal estan en conjunción "
                           f"en el signo {conj['signo']} y grado {conj['grado']:.2f}")
                else:
                    desc = (f"El dia {conj['fecha']} y hora {conj['hora']} la luna nueva (no eclipse) y el Sol natal estan en conjunción "
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
    - Sol natal en Capricornio 5° (275°) y Luna nueva en Capricornio 7° (277°)
      -> Diferencia directa: |275° - 277°| = 2° (es conjunción)
    - Sol natal en Capricornio 5° (275°) y Luna nueva en Cáncer 6° (96°)
      -> Diferencia directa: |275° - 96°| = 179° (no es conjunción)
    - Sol natal en Aries 2° (2°) y Luna nueva en Piscis 28° (358°)
      -> Diferencia aparente: |2° - 358°| = 356°
      -> Diferencia real: 360° - 356° = 4° (es conjunción)
    """
    # Calcular diferencia directa
    diff = abs(pos1 - pos2)
    
    # Si la diferencia es mayor a 180°, hay un camino más corto
    if diff > 180:
        diff = 360 - diff
    
    return diff
