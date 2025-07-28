#!/usr/bin/env python3
"""
Script de debug para verificar la posición de la Luna Progresada
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.progressed_moon_transits import ProgressedMoonTransitsCalculator

# Datos natales de prueba (Luis Minvielle)
natal_data = {
    'name': 'Luis Minvielle (LMV red)',
    'location': {
        'latitude': -34.6118,
        'longitude': -58.3960,
        'name': 'Buenos Aires',
        'timezone': 'America/Argentina/Buenos_Aires'
    },
    'hora_local': '1964-12-26T21:12:00',
    'points': {
        'Sun': {'longitude': 275.279, 'sign': 'Capricornio', 'position': '5°16\'44"'},
        'Moon': {'longitude': 199.532, 'sign': 'Libra', 'position': '19°31\'56"'}
    },
    'houses': {
        1: {'longitude': 30.0},
        2: {'longitude': 60.0},
        3: {'longitude': 90.0},
        4: {'longitude': 120.0},
        5: {'longitude': 150.0},
        6: {'longitude': 180.0},
        7: {'longitude': 210.0},
        8: {'longitude': 240.0},
        9: {'longitude': 270.0},
        10: {'longitude': 300.0},
        11: {'longitude': 330.0},
        12: {'longitude': 0.0}
    }
}

def main():
    print("=== DEBUG: Posición de Luna Progresada ===")
    
    # Crear calculador especializado
    calculator = ProgressedMoonTransitsCalculator(natal_data)
    
    # Fecha actual
    current_date = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    print(f"Fecha actual: {current_date}")
    
    # Calcular posición
    try:
        progressed_pos = calculator._calculate_progressed_moon_position(current_date)
        print(f"Posición Luna Progresada: {progressed_pos}°")
        
        # Calcular signo y grado
        signo_num = int(progressed_pos / 30)
        signos = ['Aries', 'Tauro', 'Géminis', 'Cáncer', 'Leo', 'Virgo', 
                 'Libra', 'Escorpio', 'Sagitario', 'Capricornio', 'Acuario', 'Piscis']
        signo = signos[signo_num % 12]
        grado = progressed_pos % 30
        
        print(f"Signo: {signo}")
        print(f"Grado decimal: {grado}")
        print(f"Grado entero: {int(grado)}")
        print(f"Minutos: {int((grado - int(grado)) * 60)}")
        print(f"Segundos: {int(((grado - int(grado)) * 60 - int((grado - int(grado)) * 60)) * 60)}")
        
        # Comparar con el test
        print(f"\n=== COMPARACIÓN CON TEST ===")
        print(f"Test esperado: 5°17' Capricornio (≈275.29°)")
        print(f"Calculado: {int(grado)}°{int((grado - int(grado)) * 60)}' {signo} (≈{progressed_pos:.2f}°)")
        
        if abs(progressed_pos - 275.29) < 1.0:
            print("✅ CORRECTO: Posición muy cercana al test")
        else:
            print("❌ ERROR: Posición muy diferente al test")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
