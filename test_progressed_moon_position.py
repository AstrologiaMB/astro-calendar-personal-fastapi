"""
Script para verificar la posición de la Luna progresada en fechas específicas
y compararla con los resultados de AstroSeek.
"""
import json
import os
from datetime import datetime
import pytz
from src.calculators.progressed_moon_transits import ProgressedMoonTransitsCalculator

def main():
    # Crear datos natales directamente para 26/12/1964 21:12 Buenos Aires
    print("Creando datos natales para: 26/12/1964 21:12 Buenos Aires, Argentina")
    
    # Datos natales reales extraídos del archivo JSON de la carta natal
    # Sol: 5°17' Capricornio = 275.283° (270° + 5.283°)
    # Luna: 19°32' Libra = 199.533° (180° + 19.533°)
    # Mercurio: 18°56' Sagitario = 258.933° (240° + 18.933°)
    # Venus: 9°37' Sagitario = 249.617° (240° + 9.617°)
    # Marte: 22°20' Virgo = 172.333° (150° + 22.333°)
    
    natal_data = {
        'date': "1964-12-26T21:12:00-03:00",
        'location': {
            'latitude': -34.6118,  # Buenos Aires
            'longitude': -58.3960,
            'timezone': 'America/Argentina/Buenos_Aires'
        },
        'points': {
            'Sun': {'longitude': 275.283, 'latitude': 0, 'distance': 0, 'speed': 0},  # 5°17' Capricornio
            'Moon': {'longitude': 199.533, 'latitude': 0, 'distance': 0, 'speed': 0},  # 19°32' Libra
            'Mercury': {'longitude': 258.933, 'latitude': 0, 'distance': 0, 'speed': 0},  # 18°56' Sagitario
            'Venus': {'longitude': 249.617, 'latitude': 0, 'distance': 0, 'speed': 0},  # 9°37' Sagitario
            'Mars': {'longitude': 172.333, 'latitude': 0, 'distance': 0, 'speed': 0},  # 22°20' Virgo
            'Jupiter': {'longitude': 60.0, 'latitude': 0, 'distance': 0, 'speed': 0},  # Posición estimada
            'Saturn': {'longitude': 330.0, 'latitude': 0, 'distance': 0, 'speed': 0},  # Posición estimada
            'Uranus': {'longitude': 150.0, 'latitude': 0, 'distance': 0, 'speed': 0},  # Posición estimada
            'Neptune': {'longitude': 220.0, 'latitude': 0, 'distance': 0, 'speed': 0},  # Posición estimada
            'Pluto': {'longitude': 165.0, 'latitude': 0, 'distance': 0, 'speed': 0}  # Posición estimada
        }
    }
    
    print(f"Usando fecha de nacimiento: 26/12/1964 21:12 Buenos Aires, Argentina")
    
    # Crear calculador de Luna progresada
    calculator = ProgressedMoonTransitsCalculator(natal_data)
    
    # Verificar posiciones en diferentes fechas
    dates_to_check = [
        datetime(2024, 1, 1, tzinfo=pytz.UTC),  # AstroSeek: Sagitario 13°49'
        datetime(2024, 6, 6, tzinfo=pytz.UTC),  # AstroSeek: Conjunción con Mercurio
        datetime(2024, 12, 31, tzinfo=pytz.UTC),
        datetime(2025, 10, 25, tzinfo=pytz.UTC)  # Fecha de conjunción con el Sol
    ]
    
    print("\nPosiciones de la Luna progresada (método ARMC 1 Naibod):")
    print("=" * 70)
    print("Fecha          | Posición Calculada      | Posición AstroSeek    | Diferencia")
    print("-" * 70)
    
    # Posiciones conocidas de AstroSeek
    astroseek_positions = {
        "2024-01-01": "Sagitario 13°49'",
        "2024-06-06": "Sagitario 18°55'",
        "2024-12-31": "Aproximadamente Sagitario 25°",
        "2025-10-25": "Capricornio 5°17'"
    }
    
    for date in dates_to_check:
        pos = calculator._calculate_progressed_moon_position(date)
        # Convertir posición a signo y grado
        sign_num = int(pos / 30)
        sign_deg = pos % 30
        signs = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", 
                "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
        sign = signs[sign_num]
        
        date_str = date.strftime('%Y-%m-%d')
        calculated_pos = f"{sign} {sign_deg:.2f}°"
        astroseek_pos = astroseek_positions.get(date_str, "No disponible")
        
        print(f"{date_str} | {calculated_pos:<22} | {astroseek_pos:<21} | ", end="")
        
        # Verificar si hay conjunciones con planetas natales
        conjunctions = []
        for planet_id, planet_data in calculator.natal_positions.items():
            planet_pos = planet_data['longitude']
            diff = abs(pos - planet_pos)
            if diff > 180:
                diff = 360 - diff
            
            if diff <= 2.0:  # Usar el mismo orbe que en el calculador (2.0°)
                from immanuel.const import chart
                planet_names = {
                    chart.SUN: "Sol",
                    chart.MOON: "Luna",
                    chart.MERCURY: "Mercurio",
                    chart.VENUS: "Venus",
                    chart.MARS: "Marte",
                    chart.JUPITER: "Júpiter",
                    chart.SATURN: "Saturno",
                    chart.URANUS: "Urano",
                    chart.NEPTUNE: "Neptuno",
                    chart.PLUTO: "Plutón"
                }
                conjunctions.append(f"{planet_names.get(planet_id, str(planet_id))} (orbe: {diff:.2f}°)")
        
        if conjunctions:
            print(f"Conjunción con: {', '.join(conjunctions)}")
        else:
            print("Sin conjunciones")
    
    print("=" * 70)
    print("Nota: Las posiciones de AstroSeek son aproximadas y se basan en la información proporcionada.")

if __name__ == "__main__":
    main()
