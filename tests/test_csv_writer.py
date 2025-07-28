"""
Script para probar la funcionalidad de CSVWriter sin ejecutar todo el cálculo.
"""
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from src.core.base_event import AstroEvent
from src.core.constants import EventType
from src.output.csv_writer import CSVWriter

def main():
    # Crear algunos eventos de prueba
    events = [
        AstroEvent(
            fecha_utc=datetime.now(ZoneInfo("UTC")),
            tipo_evento=EventType.ASPECTO,
            descripcion="Mercurio Cuadratura Sol Natal",
            planeta1="Mercurio",
            planeta2="Sol",
            longitud1=95.5,
            longitud2=275.5,
            tipo_aspecto="Cuadratura",
            orbe=0.001,
            es_aplicativo=True,
            metadata={
                'movimiento': 'Directo',
                'estado': 'Exacto'
            }
        ),
        AstroEvent(
            fecha_utc=datetime.now(ZoneInfo("UTC")),
            tipo_evento=EventType.ASPECTO,
            descripcion="Venus Conjunción Luna Natal",
            planeta1="Venus",
            planeta2="Luna", 
            longitud1=199.5,
            longitud2=199.5,
            tipo_aspecto="Conjunción",
            orbe=0.002,
            es_aplicativo=False,
            metadata={
                'movimiento': 'Retrógrado',
                'estado': 'Separativo'
            }
        ),
        # Evento de Luna Nueva para probar campos de fase
        AstroEvent(
            fecha_utc=datetime.now(ZoneInfo("UTC")),
            tipo_evento=EventType.LUNA_NUEVA,
            descripcion="Luna Nueva en Cáncer",
            signo="Cáncer",
            grado=15.5,
            longitud1=105.5,  # 15.5° de Cáncer
            metadata={}
        )
    ]
    
    # Intentar escribir al CSV
    try:
        CSVWriter.write_events(events, "test_events.csv")
        print("\nCSV generado exitosamente!")
        print("Archivo: test_events.csv")
        
        # Mostrar contenido del archivo usando csv reader
        print("\nContenido del archivo CSV:")
        print("-" * 120)
        with open("test_events.csv", "r", encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                print(','.join(f'"{field}"' for field in row))
        print("-" * 120)
        
        print("\nVerificar que el archivo contenga:")
        print("1. Todos los campos de aspectos (incluyendo movimiento y estado)")
        print("2. Fechas y horas en formato correcto")
        print("3. Campos vacíos para datos no aplicables")
        print("4. Campos específicos para luna nueva")
    except Exception as e:
        print(f"\nError al generar CSV: {str(e)}")
        raise

if __name__ == "__main__":
    main()
