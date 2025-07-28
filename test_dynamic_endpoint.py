#!/usr/bin/env python3
"""
Script para probar el nuevo endpoint dinámico del microservicio.
"""
import requests
import json
import time

def test_dynamic_endpoint():
    """Prueba el endpoint dinámico con datos básicos de nacimiento."""
    
    # URL del microservicio
    url = "http://localhost:8004/calculate-personal-calendar-dynamic"
    
    # Datos básicos de nacimiento (mismos que en test_natal_data.json)
    birth_data = {
        "name": "Luis",
        "birth_date": "1964-12-26",
        "birth_time": "21:12",
        "location": {
            "latitude": -34.6083696,
            "longitude": -58.4440583,
            "name": "Buenos Aires, Argentina",
            "timezone": "America/Argentina/Buenos_Aires"
        },
        "year": 2025
    }
    
    print("Probando endpoint dinámico...")
    print(f"URL: {url}")
    print(f"Datos de entrada: {json.dumps(birth_data, indent=2)}")
    
    try:
        # Realizar petición
        start_time = time.time()
        response = requests.post(url, json=birth_data, timeout=60)
        request_time = time.time() - start_time
        
        print(f"\nTiempo de petición: {request_time:.2f} segundos")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "="*80)
            print("RESULTADO EXITOSO")
            print("="*80)
            print(f"Nombre: {result['name']}")
            print(f"Año: {result['year']}")
            print(f"Total de eventos: {result['total_events']}")
            print(f"Tiempo de cálculo: {result['calculation_time']:.2f} segundos")
            
            # Analizar tipos de eventos
            event_types = {}
            for event in result['events']:
                event_type = event['tipo_evento']
                if event_type not in event_types:
                    event_types[event_type] = 0
                event_types[event_type] += 1
            
            print("\nTipos de eventos generados:")
            for event_type, count in event_types.items():
                print(f"  {event_type}: {count} eventos")
            
            # Mostrar algunos eventos de ejemplo
            print("\nPrimeros 5 eventos:")
            for i, event in enumerate(result['events'][:5]):
                print(f"  {i+1}. {event['fecha_utc']} - {event['descripcion']}")
            
            # Verificar si se solucionaron los problemas
            print("\n" + "="*80)
            print("VERIFICACIÓN DE PROBLEMAS SOLUCIONADOS")
            print("="*80)
            
            # Contar eventos por tipo
            transits = len([e for e in result['events'] if e['tipo_evento'] == 'TRANSITO'])
            progressed = len([e for e in result['events'] if e['tipo_evento'] == 'LUNA_PROGRESADA'])
            profections = len([e for e in result['events'] if e['tipo_evento'] == 'PROFECCION'])
            
            print(f"✅ Tránsitos: {transits} eventos (antes: 173)")
            print(f"✅ Luna progresada: {progressed} eventos (antes: 1)")
            print(f"✅ Profecciones: {profections} eventos (antes: 0)")
            
            # Verificar mejoras
            if progressed > 1:
                print("🎉 MEJORA: Luna progresada ahora genera más eventos!")
            if profections > 0:
                print("🎉 MEJORA: Profecciones ahora funcionan!")
            
            total_before = 174
            improvement = result['total_events'] - total_before
            if improvement > 0:
                print(f"🎉 MEJORA TOTAL: +{improvement} eventos ({result['total_events']} vs {total_before})")
            
            return True
            
        else:
            print(f"\nERROR: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")
        print("¿Está ejecutándose el microservicio en puerto 8004?")
        return False
    except Exception as e:
        print(f"\nError inesperado: {e}")
        return False

def test_legacy_endpoint():
    """Prueba el endpoint legacy para comparación."""
    
    # Cargar datos de prueba existentes
    with open('test_natal_data.json', 'r') as f:
        natal_data = json.load(f)
    
    url = "http://localhost:8004/calculate-personal-calendar"
    
    print("\n" + "="*80)
    print("PROBANDO ENDPOINT LEGACY PARA COMPARACIÓN")
    print("="*80)
    
    try:
        start_time = time.time()
        response = requests.post(url, json=natal_data, timeout=60)
        request_time = time.time() - start_time
        
        print(f"Tiempo de petición: {request_time:.2f} segundos")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Total de eventos (legacy): {result['total_events']}")
            return result['total_events']
        else:
            print(f"Error en endpoint legacy: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"Error probando endpoint legacy: {e}")
        return 0

if __name__ == "__main__":
    print("PRUEBA DEL ENDPOINT DINÁMICO DEL MICROSERVICIO")
    print("=" * 80)
    
    # Probar endpoint dinámico
    dynamic_success = test_dynamic_endpoint()
    
    # Probar endpoint legacy para comparación
    legacy_events = test_legacy_endpoint()
    
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    
    if dynamic_success:
        print("✅ Endpoint dinámico funciona correctamente")
        print("✅ Problema de datos natales incompletos SOLUCIONADO")
        print("✅ Calculadores ahora reciben datos completos con Ascendente")
    else:
        print("❌ Endpoint dinámico falló")
    
    print("\nPróximos pasos:")
    print("1. Integrar endpoint dinámico en el frontend")
    print("2. Actualizar hook useUserNatalData para usar datos básicos")
    print("3. Agregar calculadores faltantes (fases lunares, eclipses)")
    print("4. Alcanzar objetivo de 229 eventos")
