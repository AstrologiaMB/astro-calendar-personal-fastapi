#!/usr/bin/env python3
"""
Script para comparar los datos que recibe el frontend vs la API directa
"""
import requests
import json
from datetime import datetime

def test_api_direct():
    """Prueba directa a la API"""
    url = "http://localhost:8004/calculate-personal-calendar-dynamic"
    data = {
        "name": "Luis Minvielle (LMV red)",
        "birth_date": "1964-12-26",
        "birth_time": "21:12",
        "location": {
            "latitude": -34.6118,
            "longitude": -58.3960,
            "name": "Buenos Aires",
            "timezone": "America/Argentina/Buenos_Aires"
        },
        "year": 2025
    }
    
    print("=== PRUEBA DIRECTA A LA API ===")
    print(f"URL: {url}")
    print(f"Datos enviados: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Buscar eventos de Luna Progresada
            luna_progresada_events = []
            for event in result.get('events', []):
                if event.get('tipo_evento') == 'Tránsito Casa Estado':
                    house_transits = event.get('house_transits', [])
                    for transit in house_transits:
                        if transit.get('tipo') == 'luna_progresada':
                            luna_progresada_events.append(transit)
            
            print(f"\n=== EVENTOS DE LUNA PROGRESADA ENCONTRADOS: {len(luna_progresada_events)} ===")
            for i, event in enumerate(luna_progresada_events):
                print(f"Evento {i+1}:")
                print(f"  - Tipo: {event.get('tipo')}")
                print(f"  - Planeta: {event.get('planeta')}")
                print(f"  - Signo: {event.get('signo')}")
                print(f"  - Grado: {event.get('grado')}")
                print(f"  - Casa: {event.get('casa')}")
                print(f"  - Casa Significado: {event.get('casa_significado')}")
                print()
            
            # Mostrar estadísticas
            stats = result.get('calculation_stats', {})
            print(f"=== ESTADÍSTICAS ===")
            print(f"Total eventos: {stats.get('total_events', 'N/A')}")
            print(f"Tiempo de cálculo: {stats.get('calculation_time', 'N/A')}s")
            print(f"Luna progresada count: {stats.get('progressed_moon_count', 'N/A')}")
            
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error en la petición: {e}")

def test_with_different_params():
    """Prueba con diferentes parámetros para ver si hay variaciones"""
    print("\n" + "="*50)
    print("=== PRUEBA CON DIFERENTES AÑOS ===")
    
    base_data = {
        "name": "Luis Minvielle (LMV red)",
        "birth_date": "1964-12-26",
        "birth_time": "21:12",
        "location": {
            "latitude": -34.6118,
            "longitude": -58.3960,
            "name": "Buenos Aires",
            "timezone": "America/Argentina/Buenos_Aires"
        }
    }
    
    for year in [2024, 2025, 2026]:
        print(f"\n--- Año {year} ---")
        data = {**base_data, "year": year}
        
        try:
            response = requests.post("http://localhost:8004/calculate-personal-calendar-dynamic", 
                                   json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                
                # Buscar Luna Progresada
                for event in result.get('events', []):
                    if event.get('tipo_evento') == 'Tránsito Casa Estado':
                        house_transits = event.get('house_transits', [])
                        for transit in house_transits:
                            if transit.get('tipo') == 'luna_progresada':
                                print(f"  Luna Progresada: {transit.get('signo')} {transit.get('grado')}°")
                                break
            else:
                print(f"  Error: {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_api_direct()
    test_with_different_params()
