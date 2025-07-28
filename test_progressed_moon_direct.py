"""
Test directo para verificar el cálculo de Luna Progresada
usando el calculador especializado.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calculators.progressed_moon_transits import ProgressedMoonTransitsCalculator

def test_progressed_moon_calculation():
    """
    Test directo del cálculo de Luna Progresada para verificar
    qué devuelve el calculador especializado.
    """
    
    # Cargar datos natales de prueba (26/12/1964 21:12 Buenos Aires)
    with open("test_natal_data.json", "r", encoding="utf-8") as f:
        natal_data = json.load(f)
    
    print("=== DATOS NATALES ===")
    print(f"Fecha de nacimiento: {natal_data['hora_local']}")
    print(f"Ubicación: {natal_data['location']['name']}")
    print(f"Zona horaria: {natal_data['location']['timezone']}")
    print(f"Luna natal: {natal_data['points']['Moon']['position']} {natal_data['points']['Moon']['sign']}")
    print(f"Luna natal longitud: {natal_data['points']['Moon']['longitude']}°")
    
    # Crear calculador especializado
    calculator = ProgressedMoonTransitsCalculator(natal_data)
    
    print(f"\n=== CALCULADOR ESPECIALIZADO ===")
    print(f"Fecha de nacimiento detectada: {calculator.birth_date}")
    print(f"Zona horaria del usuario: {calculator.user_timezone}")
    
    # Fechas de prueba
    test_dates = [
        datetime(2025, 10, 25, tzinfo=ZoneInfo("UTC")),  # Fecha mencionada por el usuario
        datetime(2025, 6, 30, tzinfo=ZoneInfo("UTC")),   # Fecha actual
        datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC")),    # Inicio de año
    ]
    
    print(f"\n=== CÁLCULOS DE LUNA PROGRESADA ===")
    
    for test_date in test_dates:
        try:
            # Calcular posición de Luna Progresada
            progressed_pos = calculator._calculate_progressed_moon_position(test_date)
            
            # Calcular signo y grado
            from src.core.constants import AstronomicalConstants
            sign = AstronomicalConstants.get_sign_name(progressed_pos)
            degree_in_sign = progressed_pos % 30
            
            print(f"\nFecha: {test_date.strftime('%Y-%m-%d')}")
            print(f"  Posición absoluta: {progressed_pos:.6f}°")
            print(f"  Signo: {sign}")
            print(f"  Grado en signo: {degree_in_sign:.6f}°")
            print(f"  Formato: {degree_in_sign:.1f}° {sign}")
            
            # Formato más detallado
            whole_degrees = int(degree_in_sign)
            minutes_decimal = (degree_in_sign - whole_degrees) * 60
            minutes = int(minutes_decimal)
            seconds = int((minutes_decimal - minutes) * 60)
            print(f"  Formato detallado: {whole_degrees}°{minutes}'{seconds}\" {sign}")
            
        except Exception as e:
            print(f"\nError calculando para {test_date}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_progressed_moon_calculation()
