"""
Módulo para generar el análisis de lunas llenas en casas natales.
"""
import json
import csv

def generate_full_moon_houses_report(natal_file: str, events_file: str, output_file: str = 'natal_lunallena.csv'):
    """
    Genera un reporte de las lunas llenas y las casas natales donde ocurren.
    
    Args:
        natal_file: Ruta al archivo JSON con la carta natal
        events_file: Ruta al archivo CSV con los eventos astronómicos
        output_file: Ruta donde guardar el archivo de salida
    """
    # Cargar datos de la carta natal
    with open(natal_file, 'r') as f:
        natal_data = json.load(f)
    
    # Cargar datos de lunas llenas
    full_moons = []
    with open(events_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['tipo_evento'] == 'Luna Llena':
                # Extraer solo el grado numérico de la posición
                grado = float(row['grado'].split('°')[0])
                full_moons.append({
                    'fecha': row['fecha_local'],
                    'hora': row['hora_local'],
                    'signo': row['signo'],
                    'grado': grado
                })
    
    # Generar reporte
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Fecha', 'Hora', 'Casa Natal', 'Descripción'])
        
        for moon in full_moons:
            # Determinar casa natal
            casa = determinar_casa_natal(moon['signo'], moon['grado'], natal_data['houses'])
            
            # Generar descripción
            desc = (f"La luna llena del día {moon['fecha']} y hora {moon['hora']} "
                   f"se hizo en la casa {casa} natal")
            
            # Escribir fila
            writer.writerow([
                moon['fecha'],
                moon['hora'],
                casa,
                desc
            ])
    
    return output_file

# Mapeo de nombres de signos inglés-español
SIGN_TRANSLATIONS = {
    # Inglés a Español
    'Aries': 'Aries',
    'Taurus': 'Tauro',
    'Gemini': 'Géminis',
    'Cancer': 'Cáncer',
    'Leo': 'Leo',
    'Virgo': 'Virgo',
    'Libra': 'Libra',
    'Scorpio': 'Escorpio',
    'Sagittarius': 'Sagitario',
    'Capricorn': 'Capricornio',
    'Aquarius': 'Acuario',
    'Pisces': 'Piscis',
    # Español a Inglés
    'Tauro': 'Taurus',
    'Géminis': 'Gemini',
    'Cáncer': 'Cancer',
    'Escorpio': 'Scorpio',
    'Sagitario': 'Sagittarius',
    'Capricornio': 'Capricorn',
    'Acuario': 'Aquarius',
    'Piscis': 'Pisces'
}

# Lista ordenada de signos en español
SIGNOS = [
    'Aries', 'Tauro', 'Géminis', 'Cáncer', 'Leo', 'Virgo',
    'Libra', 'Escorpio', 'Sagitario', 'Capricornio', 'Acuario', 'Piscis'
]

def _convertir_a_grados_absolutos(signo: str, grado: float, desde_ingles: bool = False) -> float:
    """
    Convierte una posición zodiacal (signo y grado) a grados absolutos (0-360).
    
    Args:
        signo: Nombre del signo zodiacal
        grado: Grado dentro del signo
        desde_ingles: True si el signo está en inglés y hay que traducirlo a español
    """
    # Si el signo está en inglés y hay que traducirlo
    if desde_ingles:
        signo = SIGN_TRANSLATIONS.get(signo, signo)
    return SIGNOS.index(signo) * 30 + grado

def _parsear_posicion(posicion: str) -> float:
    """
    Convierte una posición en formato '27°45\'16"' a grados decimales.
    """
    # Eliminar caracteres especiales
    partes = posicion.replace('°', ' ').replace('\'', ' ').replace('"', ' ').split()
    grados = float(partes[0])
    minutos = float(partes[1]) if len(partes) > 1 else 0
    segundos = float(partes[2]) if len(partes) > 2 else 0
    return grados + minutos/60 + segundos/3600

def determinar_casa_natal(signo: str, grado: float, casas: dict) -> int:
    """
    Determina en qué casa natal cae una posición zodiacal.
    
    Args:
        signo: Nombre del signo zodiacal (en español)
        grado: Grado dentro del signo
        casas: Diccionario con los datos de las casas natales
        
    Returns:
        Número de la casa natal (1-12)
    """
    print(f"\nCalculando casa para {signo} {grado}°")
    
    # Convertir posición de la luna a grados absolutos (ya viene en español)
    pos_luna = _convertir_a_grados_absolutos(signo, grado)
    print(f"Posición absoluta de la luna: {pos_luna}°")
    
    # Convertir posiciones de las casas a grados absolutos
    casas_abs = {}
    for num, datos in casas.items():
        pos_abs = _convertir_a_grados_absolutos(
            datos['sign'],
            _parsear_posicion(datos['position']),
            desde_ingles=True  # Las casas vienen en inglés del JSON
        )
        casas_abs[int(num)] = pos_abs
        print(f"Casa {num}: {datos['sign']} {datos['position']} -> {pos_abs}°")
    
    print("\nComparando con límites de casas:")
    # Mantener el orden original de las casas (1-12)
    casas_ordenadas = [(i, casas_abs[i]) for i in range(1, 13)]
    for i in range(len(casas_ordenadas)):
        casa_actual = casas_ordenadas[i]
        casa_siguiente = casas_ordenadas[(i + 1) % 12]
        print(f"Casa {casa_actual[0]}: {casa_actual[1]}° -> Casa {casa_siguiente[0]}: {casa_siguiente[1]}°")
    
    # Para cada casa, determinar si el punto está entre su inicio y el inicio de la siguiente
    pos_luna_norm = pos_luna
    for i in range(len(casas_ordenadas)):
        casa_actual = casas_ordenadas[i]
        casa_siguiente = casas_ordenadas[(i + 1) % 12]
        
        inicio = casa_actual[1]
        fin = casa_siguiente[1]
        
        # Si la casa cruza 0°
        if fin < inicio:
            # Si la posición está después del inicio o antes del fin
            if pos_luna >= inicio or pos_luna < fin:
                return casa_actual[0]
        # Caso normal
        elif inicio <= pos_luna < fin:
            return casa_actual[0]
    
    # Si no se encontró (no debería ocurrir)
    raise ValueError(f"No se pudo determinar la casa para {signo} {grado}°")
