"""
Módulo de configuración para el manejo de nombres de archivo y validación de datos.
"""

import os
import re

OUTPUT_DIR = '/Users/apple/astro_calendar_personal_v3/output'

def ensure_output_dir():
    """Asegura que el directorio de salida exista"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def get_general_events_filename(year: int) -> str:
    """
    Genera el nombre de archivo para eventos astronómicos generales.
    
    Args:
        year: Año de los eventos
    Returns:
        Nombre del archivo (ej: eventos_astronomicos_2025.csv)
    """
    return f"{OUTPUT_DIR}/eventos_astronomicos_{year}.csv"

def get_personal_events_filename(person_name: str, year: int) -> str:
    """
    Genera el nombre de archivo para eventos personales.
    
    Args:
        person_name: Nombre de la persona
        year: Año de los eventos
    Returns:
        Nombre del archivo (ej: eventos_personales_juan_perez_2025.csv)
    """
    normalized_name = normalize_name(person_name)
    return f"{OUTPUT_DIR}/eventos_personales_{normalized_name}_{year}.csv"

from datetime import datetime
from typing import Optional

def normalize_name(name: str) -> str:
    """
    Normaliza un nombre para usar en nombres de archivo.
    - Convierte a minúsculas
    - Reemplaza espacios por guiones bajos
    - Remueve caracteres especiales
    - Reemplaza ñ por n
    - Remueve acentos
    
    Args:
        name: Nombre a normalizar
    Returns:
        Nombre normalizado
    """
    # Mapeo de caracteres especiales
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u', 'Á': 'a', 'É': 'e', 'Í': 'i',
        'Ó': 'o', 'Ú': 'u', 'Ñ': 'n', 'Ü': 'u'
    }
    
    # Aplicar reemplazos
    normalized = name.lower()
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Reemplazar espacios y caracteres especiales
    normalized = re.sub(r'[^a-z0-9]', '_', normalized)
    normalized = re.sub(r'_+', '_', normalized)  # Colapsar múltiples guiones bajos
    normalized = normalized.strip('_')  # Remover guiones al inicio/final
    
    return normalized

def validate_name(name: str) -> bool:
    """
    Valida que un nombre sea válido.
    - No vacío
    - Al menos 2 caracteres
    - Solo letras, números, espacios y caracteres básicos
    
    Args:
        name: Nombre a validar
    Returns:
        True si el nombre es válido
    """
    if not name or len(name) < 2:
        return False
    
    # Permitir letras, números, espacios y caracteres básicos
    return bool(re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s\-\.]+$', name))

def get_natal_chart_filename(person_name: str) -> str:
    """
    Genera el nombre de archivo para una carta natal.
    
    Args:
        person_name: Nombre de la persona
    Returns:
        Nombre del archivo (ej: carta_natal_juan_perez.json)
    """
    normalized_name = normalize_name(person_name)
    return f"{OUTPUT_DIR}/carta_natal_{normalized_name}.json"

def get_events_filename(city: str, year: int) -> str:
    """
    Genera el nombre de archivo para eventos astronómicos.
    
    Args:
        city: Nombre de la ciudad
        year: Año de los eventos
    Returns:
        Nombre del archivo (ej: eventos_astronomicos_buenos_aires_2025.csv)
    """
    normalized_city = normalize_name(city)
    return f"{OUTPUT_DIR}/eventos_astronomicos_{normalized_city}_{year}.csv"

def get_report_filename(report_type: str, person_name: str) -> str:
    """
    Genera el nombre de archivo para un reporte.
    
    Args:
        report_type: Tipo de reporte (ej: lunanueva, lunallena)
        person_name: Nombre de la persona
    Returns:
        Nombre del archivo (ej: natal_lunanueva_juan_perez.csv)
    """
    normalized_name = normalize_name(person_name)
    return f"{OUTPUT_DIR}/natal_{report_type}_{normalized_name}.csv"

def get_eclipse_report_filename(eclipse_type: str, planet: str, person_name: str) -> str:
    """
    Genera el nombre de archivo para un reporte de eclipse.
    
    Args:
        eclipse_type: Tipo de eclipse ('solar' o 'lunar')
        planet: Nombre del planeta o punto (ej: 'sol', 'luna', 'mercurio')
        person_name: Nombre de la persona
    Returns:
        Nombre del archivo (ej: natal_eclipse_solar_sol_juan_perez.csv)
    """
    normalized_name = normalize_name(person_name)
    normalized_planet = normalize_name(planet)
    return f"{OUTPUT_DIR}/natal_eclipse_{eclipse_type}_{normalized_planet}_{normalized_name}.csv"

def get_default_events_filename(year: int) -> str:
    """
    Genera el nombre de archivo por defecto para eventos astronómicos.
    
    Args:
        year: Año de los eventos
    Returns:
        Nombre del archivo (ej: eventos_astronomicos_2025_BuenosAires.csv)
    """
    return f"{OUTPUT_DIR}/eventos_astronomicos_{year}_BuenosAires.csv"

def validate_year(year: int) -> bool:
    """
    Valida que un año esté en el rango permitido.
    
    Args:
        year: Año a validar
    Returns:
        True si el año es válido
    """
    return 1900 <= year <= 2100

def validate_date(date_str: str) -> Optional[datetime]:
    """
    Valida una fecha en formato YYYY-MM-DD.
    
    Args:
        date_str: Fecha a validar
    Returns:
        datetime si la fecha es válida, None si no
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def validate_time(time_str: str) -> Optional[datetime]:
    """
    Valida una hora en formato HH:MM.
    
    Args:
        time_str: Hora a validar
    Returns:
        datetime si la hora es válida, None si no
    """
    try:
        return datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return None
