#!/usr/bin/env python3
"""
Script para debuggear y comparar datos natales entre el formato original y el microservicio.
"""
import json
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append('/Users/apple/astro_calendar_personal_v3')

from src.calculators.natal_chart import calcular_carta_natal

def generar_datos_natales_completos():
    """Genera datos natales completos como hace el script original."""
    
    # Datos de Luis (mismos que en test_natal_data.json)
    datos_usuario = {
        "hora_local": "1964-12-26T21:12:00",
        "lat": -34.6083696,
        "lon": -58.4440583,
        "zona_horaria": "America/Argentina/Buenos_Aires",
        "lugar": "Buenos Aires, Argentina"
    }
    
    print("Generando carta natal completa con calcular_carta_natal()...")
    natal_data = calcular_carta_natal(datos_usuario)
    natal_data['name'] = "Luis"
    
    return natal_data

def comparar_datos():
    """Compara datos natales completos vs. datos actuales del microservicio."""
    
    # Generar datos completos
    datos_completos = generar_datos_natales_completos()
    
    # Cargar datos actuales del microservicio
    with open('test_natal_data.json', 'r') as f:
        datos_actuales = json.load(f)
    
    print("\n" + "="*80)
    print("COMPARACIÓN DE DATOS NATALES")
    print("="*80)
    
    print("\n1. PUNTOS/PLANETAS:")
    print("-" * 40)
    print("Datos completos (script original):")
    for punto, data in datos_completos['points'].items():
        print(f"  {punto}: {data['sign']} {data['position']}")
    
    print("\nDatos actuales (microservicio):")
    for punto, data in datos_actuales['points'].items():
        print(f"  {punto}: {data['sign']} {data['position']}")
    
    print("\n2. CAMPOS FALTANTES EN MICROSERVICIO:")
    print("-" * 40)
    puntos_faltantes = set(datos_completos['points'].keys()) - set(datos_actuales['points'].keys())
    if puntos_faltantes:
        for punto in puntos_faltantes:
            data = datos_completos['points'][punto]
            print(f"  ❌ {punto}: {data['sign']} {data['position']}")
    else:
        print("  ✅ No faltan puntos")
    
    print("\n3. CAMPOS CRÍTICOS PARA CALCULADORES:")
    print("-" * 40)
    campos_criticos = ['Asc', 'MC', 'Dsc', 'Ic', 'North Node', 'South Node']
    for campo in campos_criticos:
        if campo in datos_completos['points']:
            data = datos_completos['points'][campo]
            status = "✅" if campo in datos_actuales['points'] else "❌"
            print(f"  {status} {campo}: {data['sign']} {data['position']}")
        else:
            print(f"  ⚠️  {campo}: No disponible en datos completos")
    
    print("\n4. OTROS CAMPOS:")
    print("-" * 40)
    print(f"Datos completos tiene 'hora_local': {'✅' if 'hora_local' in datos_completos else '❌'}")
    print(f"Datos actuales tiene 'hora_local': {'✅' if 'hora_local' in datos_actuales else '❌'}")
    
    if 'hora_local' in datos_completos:
        print(f"  hora_local completos: {datos_completos['hora_local']}")
    if 'hora_local' in datos_actuales:
        print(f"  hora_local actuales: {datos_actuales['hora_local']}")
    
    print("\n5. GUARDAR DATOS COMPLETOS:")
    print("-" * 40)
    
    # Guardar datos completos para referencia
    with open('test_natal_data_COMPLETO.json', 'w') as f:
        json.dump(datos_completos, f, indent=2, ensure_ascii=False)
    print("✅ Datos completos guardados en: test_natal_data_COMPLETO.json")
    
    # Crear versión corregida para el microservicio
    datos_corregidos = datos_actuales.copy()
    
    # Agregar campos faltantes críticos
    for campo in ['Asc', 'MC', 'Dsc', 'Ic']:
        if campo in datos_completos['points']:
            datos_corregidos['points'][campo] = datos_completos['points'][campo]
    
    # Asegurar que tiene hora_local
    if 'hora_local' not in datos_corregidos and 'hora_local' in datos_completos:
        datos_corregidos['hora_local'] = datos_completos['hora_local']
    
    with open('test_natal_data_CORREGIDO.json', 'w') as f:
        json.dump(datos_corregidos, f, indent=2, ensure_ascii=False)
    print("✅ Datos corregidos guardados en: test_natal_data_CORREGIDO.json")
    
    return datos_completos, datos_actuales, datos_corregidos

if __name__ == "__main__":
    try:
        datos_completos, datos_actuales, datos_corregidos = comparar_datos()
        
        print("\n" + "="*80)
        print("RESUMEN")
        print("="*80)
        print(f"Puntos en datos completos: {len(datos_completos['points'])}")
        print(f"Puntos en datos actuales: {len(datos_actuales['points'])}")
        print(f"Puntos en datos corregidos: {len(datos_corregidos['points'])}")
        
        print("\nPróximos pasos:")
        print("1. Usar test_natal_data_CORREGIDO.json en el microservicio")
        print("2. Actualizar función convert_natal_data_format() para preservar todos los campos")
        print("3. Verificar que profecciones y luna progresada funcionen con datos completos")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
