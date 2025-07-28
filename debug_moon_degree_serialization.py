"""
Debug script para verificar si el problema está en la serialización JSON
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.progressed_moon_transits import ProgressedMoonTransitsCalculator

def test_moon_degree_serialization():
    """
    Test para verificar si el problema está en la serialización JSON
    """
    
    # Datos natales de prueba
    natal_data = {
        'name': 'Usuario',
        'location': {
            'latitude': -34.6083696,
            'longitude': -58.4440583,
            'name': 'Buenos Aires, Argentina',
            'timezone': 'America/Argentina/Buenos_Aires'
        },
        'hora_local': '1964-12-26T21:12:00',
        'points': {
            'Moon': {
                'sign': 'Virgo',
                'position': '22°19\'51"',
                'longitude': 172.33,
                'retrograde': False
            }
        },
        'houses': {}
    }
    
    # Crear calculador especializado
    calculator = ProgressedMoonTransitsCalculator(natal_data)
    
    # Fecha de prueba (30 de junio 2025)
    test_date = datetime(2025, 6, 30, tzinfo=ZoneInfo("UTC"))
    
    # Calcular posición de Luna Progresada
    progressed_pos = calculator._calculate_progressed_moon_position(test_date)
    
    # Calcular grado en signo (igual que en el código de producción)
    moon_degree = round(progressed_pos % 30, 1)
    
    print(f"=== VALORES ANTES DE SERIALIZACIÓN ===")
    print(f"progressed_pos: {progressed_pos}")
    print(f"progressed_pos % 30: {progressed_pos % 30}")
    print(f"moon_degree (round(..., 1)): {moon_degree}")
    print(f"Tipo de moon_degree: {type(moon_degree)}")
    
    # Crear el diccionario como en el código de producción
    moon_data = {
        'tipo': 'luna_progresada',
        'planeta': 'Luna Progresada',
        'simbolo': '🌙',
        'signo': 'Capricornio',
        'grado': moon_degree,
        'casa': 6,
        'casa_significado': 'Trabajo y Salud'
    }
    
    print(f"\n=== DICCIONARIO PYTHON ===")
    print(f"moon_data['grado']: {moon_data['grado']}")
    print(f"Tipo: {type(moon_data['grado'])}")
    
    # Serializar a JSON (como hace FastAPI)
    json_str = json.dumps(moon_data, ensure_ascii=False)
    print(f"\n=== JSON SERIALIZADO ===")
    print(f"JSON: {json_str}")
    
    # Deserializar de vuelta
    deserialized = json.loads(json_str)
    print(f"\n=== DESPUÉS DE DESERIALIZACIÓN ===")
    print(f"deserialized['grado']: {deserialized['grado']}")
    print(f"Tipo: {type(deserialized['grado'])}")
    
    # Test con diferentes valores decimales
    print(f"\n=== TESTS CON DIFERENTES VALORES ===")
    test_values = [1.0, 1.1, 1.5, 1.9, 2.0]
    
    for val in test_values:
        data = {'grado': val}
        json_str = json.dumps(data)
        deserialized = json.loads(json_str)
        print(f"Original: {val} ({type(val)}) -> JSON: {json_str} -> Deserializado: {deserialized['grado']} ({type(deserialized['grado'])})")

if __name__ == "__main__":
    test_moon_degree_serialization()
