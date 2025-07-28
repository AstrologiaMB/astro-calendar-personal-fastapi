#!/usr/bin/env python3

import json
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.astronomical_transits_calculator_v4 import AstronomicalTransitsCalculatorV4
from src.core.constants import EventType

def test_house_transits():
    # Cargar datos de prueba
    with open('test_natal_data.json', 'r') as f:
        natal_data = json.load(f)
    
    print("=== PRUEBA DE TRÁNSITOS POR CASAS ===")
    print(f"Datos natales cargados: {natal_data['name']}")
    
    # Crear calculador V4
    print("\n1. Creando calculador V4...")
    calculator = AstronomicalTransitsCalculatorV4(natal_data)
    
    # Verificar casas
    print(f"2. Casas cargadas: {len(calculator.house_cusps)}")
    if calculator.house_cusps:
        for house, cusp in calculator.house_cusps.items():
            print(f"   Casa {house}: {cusp:.2f}°")
    
    # Probar cálculo de estado de casas
    test_date = datetime(2025, 6, 17, tzinfo=ZoneInfo('UTC'))
    print(f"\n3. Probando cálculo de estado para fecha: {test_date}")
    
    house_event = calculator.calculate_house_transits_state(test_date)
    if house_event:
        print("✅ Evento de casas creado exitosamente")
        print(f"   Tipo: {house_event.tipo_evento}")
        print(f"   Descripción: {house_event.descripcion}")
        if hasattr(house_event, 'metadata') and house_event.metadata:
            print(f"   Metadata: {house_event.metadata}")
    else:
        print("❌ No se pudo crear evento de casas")
    
    # Probar calculate_all
    print(f"\n4. Probando calculate_all()...")
    start_date = datetime(2025, 1, 1, tzinfo=ZoneInfo('UTC'))
    end_date = datetime(2025, 12, 31, tzinfo=ZoneInfo('UTC'))
    
    all_events = calculator.calculate_all(start_date, end_date)
    print(f"   Total de eventos: {len(all_events)}")
    
    # Buscar eventos de casas
    house_events = [e for e in all_events if e.tipo_evento == EventType.TRANSITO_CASA_ESTADO]
    print(f"   Eventos de casas encontrados: {len(house_events)}")
    
    if house_events:
        for he in house_events:
            print(f"   ✅ {he.tipo_evento} - {he.descripcion}")
    else:
        print("   ❌ No se encontraron eventos de casas en calculate_all()")

if __name__ == "__main__":
    test_house_transits()
