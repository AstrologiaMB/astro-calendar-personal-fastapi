"""
Calendario Astrológico Personalizado v3
Calcula eventos astrológicos y tránsitos planetarios para un año específico.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import json
import pytz
import os
import time
from pathlib import Path
from src.core import config
from src.core.location import Location
from src.core.constants import EventType, AstronomicalConstants
from src.core.base_event import AstroEvent
from src.utils.location_utils import create_location_from_place
from src.calculators.natal_chart import calcular_carta_natal
from src.calculators.lunar_phases import LunarPhaseCalculator
from src.calculators.eclipses import EclipseCalculator
from src.calculators.ingresses import IngressCalculator
from src.calculators.retrogrades import RetrogradeCalculator
from src.calculators.nodes import NodeCalculator
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory
from src.output.csv_writer import CSVWriter

class AstronomicalCalendar:
    def __init__(self, year: int, natal_data: dict = None, use_precise_eclipse_calculator: bool = False, 
                 use_immanuel_eclipse_calculator: bool = False, use_parallel_transits_calculator: bool = False, 
                 calculate_progressed_moon: bool = False, calculate_profections: bool = False,
                 transits_calculator_type: str = "standard"):
        self.year = year
        self.natal_data = natal_data
        self.use_precise_eclipse_calculator = use_precise_eclipse_calculator
        self.use_immanuel_eclipse_calculator = use_immanuel_eclipse_calculator
        self.use_parallel_transits_calculator = use_parallel_transits_calculator
        self.calculate_progressed_moon = calculate_progressed_moon
        self.calculate_profections = calculate_profections
        self.transits_calculator_type = transits_calculator_type
        
        # Si hay datos natales, usar esa ubicación
        if natal_data and 'location' in natal_data:
            loc = natal_data['location']
            self.location = Location(
                lat=loc['latitude'],
                lon=loc['longitude'],
                name=loc['name'],
                timezone=loc['timezone'],
                elevation=25
            )
        else:
            # Ubicación por defecto: Buenos Aires
            self.location = Location(
                lat=-34.60,
                lon=-58.45,
                name="Buenos_Aires",
                timezone="America/Argentina/Buenos_Aires",
                elevation=25
            )
            
        # Validar la zona horaria obtenida
        try:
            from zoneinfo import ZoneInfo # Importar aquí para evitar dependencia circular si se mueve Location
            _ = ZoneInfo(self.location.timezone)
            print(f"Timezone '{self.location.timezone}' for location '{self.location.name}' validated successfully.")
        except Exception as e:
            raise ValueError(f"Error: The timezone '{self.location.timezone}' determined for location '{self.location.name}' is invalid or could not be processed. Please check the location input. Original error: {e}")

        self.general_events = []  # Eventos astronómicos generales
        self.personal_events = [] # Eventos personales/natales

        # Inicializar calculadores
        observer = self.location.create_ephem_observer()
        self.lunar_calculator = LunarPhaseCalculator(observer, self.location.timezone)
        
        # Usar el factory para crear el calculador de eclipses según la preferencia del usuario
        from src.calculators.eclipse_calculator_factory import EclipseCalculatorFactory
        self.eclipse_calculator = EclipseCalculatorFactory.create_calculator(
            observer, 
            use_precise=self.use_precise_eclipse_calculator,
            use_immanuel=self.use_immanuel_eclipse_calculator,
            timezone_str=self.location.timezone
        )
        
        self.ingress_calculator = IngressCalculator(timezone_str=self.location.timezone)
        self.retrograde_calculator = RetrogradeCalculator(timezone_str=self.location.timezone)
        self.node_calculator = NodeCalculator(timezone_str=self.location.timezone)

    def calculate_all_events(self):
        """Calcula todos los eventos del año"""
        print(f"\nCalculando eventos astronómicos para {self.year}...")
        start_total = time.time()
        
        start_date = datetime(self.year, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(self.year + 1, 1, 1, tzinfo=pytz.UTC)

        # Asegurar que existe el directorio de salida
        config.ensure_output_dir()

        # Calcular eventos generales
        start = time.time()
        print("\n1/5 Calculando fases lunares...")
        self.general_events.extend(self.lunar_calculator.calculate_phases(start_date, end_date))
        print(f"Completado en {time.time() - start:.2f} segundos")
        
        start = time.time()
        print("\n2/5 Calculando eclipses...")
        if self.use_immanuel_eclipse_calculator:
            calculator_type = "Immanuel"
        elif self.use_precise_eclipse_calculator:
            calculator_type = "de alta precisión"
        else:
            calculator_type = "estándar"
        print(f"Usando calculador {calculator_type}")
        self.general_events.extend(self.eclipse_calculator.calculate_eclipses(start_date, end_date))
        print(f"Completado en {time.time() - start:.2f} segundos")
        
        start = time.time()
        print("\n3/5 Calculando ingresos...")
        self.general_events.extend(self.ingress_calculator.calculate_ingresses(start_date, end_date))
        print(f"Completado en {time.time() - start:.2f} segundos")
        
        start = time.time()
        print("\n4/5 Calculando retrogradaciones...")
        self.general_events.extend(self.retrograde_calculator.calculate_retrogrades(start_date, end_date))
        print(f"Completado en {time.time() - start:.2f} segundos")
        
        start = time.time()
        print("\n5/5 Calculando nodos...")
        self.general_events.extend(self.node_calculator.calculate_node_ingresses(start_date, end_date))
        print(f"Completado en {time.time() - start:.2f} segundos")

        # Ordenar eventos generales por fecha
        self.general_events.sort(key=lambda x: x.fecha_utc)

        # Si hay datos natales, calcular eventos personales
        if self.natal_data and 'name' in self.natal_data:
            print("\nCalculando eventos personales...")
            
            # Contador para la numeración de pasos
            step_count = 1
            total_steps = 3  # Base: tránsitos, lunas, eclipses
            if self.calculate_progressed_moon:
                total_steps += 1
            if self.calculate_profections:
                total_steps += 1
            
            # Calcular tránsitos
            start = time.time()
            print(f"\n{step_count}/{total_steps} Calculando tránsitos...")
            step_count += 1
            
            # Determinar el tipo de calculador a utilizar para mostrar
            if self.transits_calculator_type == "optimized":
                calculator_display = "optimizado (método matemático/analítico)"
            elif self.transits_calculator_type == "astronomical":
                calculator_display = "astronómico (basado en efemérides precisas)"
            elif self.transits_calculator_type == "astronomical_v3":
                calculator_display = "astronómico V3 (versión mejorada con detección y preservación de eventos estacionarios)"
            elif self.use_parallel_transits_calculator:
                calculator_display = "paralelo (procesamiento multi-núcleo)"
            else:
                calculator_display = "estándar"
                
            print(f"Usando calculador de tránsitos {calculator_display}")
            
            transits_calculator = TransitsCalculatorFactory.create_calculator(
                self.natal_data, 
                calculator_type=self.transits_calculator_type,
                use_parallel=self.use_parallel_transits_calculator,
                timezone_str=self.location.timezone # Pass timezone here
            )
            self.personal_events.extend(transits_calculator.calculate_all(start_date, end_date))
            print(f"Completado en {time.time() - start:.2f} segundos")
            
            # Calcular conjunciones de Luna progresada si se solicitó
            if self.calculate_progressed_moon:
                start = time.time()
                print(f"\n{step_count}/{total_steps} Calculando conjunciones de Luna progresada...")
                step_count += 1
                progressed_calculator = TransitsCalculatorFactory.create_calculator(
                    self.natal_data,
                    calculator_type="progressed_moon"
                )
                self.personal_events.extend(progressed_calculator.calculate_all(start_date, end_date))
                print(f"Completado en {time.time() - start:.2f} segundos")
            
            # Calcular profecciones anuales si se solicitó
            if self.calculate_profections:
                start = time.time()
                print(f"\n{step_count}/{total_steps} Calculando profecciones anuales...")
                step_count += 1
                from src.calculators.profections_calculator import ProfectionsCalculator
                profections_calculator = ProfectionsCalculator(self.natal_data)
                
                # Mostrar información detallada en consola
                print("\nInformación de profección para el año actual:")
                year_start = datetime(self.year, 1, 1, tzinfo=pytz.UTC)
                profections_calculator.display_profection_info(year_start)
                
                # Calcular eventos para el CSV
                self.personal_events.extend(profections_calculator.calculate_profection_events(start_date, end_date))
                print(f"Completado en {time.time() - start:.2f} segundos")
            
            # Agregar información de casas para lunas
            print(f"\n{step_count}/{total_steps} Agregando información de casas para lunas...")
            step_count += 1
            self._add_moon_phase_house_events()
            
            # Agregar información de casas para eclipses
            print(f"\n{step_count}/{total_steps} Agregando información de casas para eclipses...")
            self._add_eclipse_house_events()

            # Ordenar eventos personales por fecha
            self.personal_events.sort(key=lambda x: x.fecha_utc)

    def _convertir_a_grados_absolutos(self, signo: str, grado: float, desde_ingles: bool = True) -> float:
        """
        Convierte una posición zodiacal (signo y grado) a grados absolutos (0-360).
        """
        # Mapeo de signos a su posición base (0-330)
        SIGNOS_BASE = {
            # Inglés
            'Aries': 0, 'Taurus': 30, 'Gemini': 60, 'Cancer': 90,
            'Leo': 120, 'Virgo': 150, 'Libra': 180, 'Scorpio': 210,
            'Sagittarius': 240, 'Capricorn': 270, 'Aquarius': 300, 'Pisces': 330,
            # Español
            'Aries': 0, 'Tauro': 30, 'Géminis': 60, 'Cáncer': 90,
            'Leo': 120, 'Virgo': 150, 'Libra': 180, 'Escorpio': 210,
            'Sagitario': 240, 'Capricornio': 270, 'Acuario': 300, 'Piscis': 330
        }
        return SIGNOS_BASE[signo] + grado

    def _parsear_posicion(self, posicion: str) -> float:
        """
        Convierte una posición en formato '27°45\'16"' a grados decimales.
        """
        partes = posicion.replace('°', ' ').replace('\'', ' ').replace('"', ' ').split()
        grados = float(partes[0])
        minutos = float(partes[1]) if len(partes) > 1 else 0
        segundos = float(partes[2]) if len(partes) > 2 else 0
        return grados + minutos/60 + segundos/3600

    def _calcular_orbe(self, pos1: float, pos2: float) -> float:
        """
        Calcula el orbe más corto entre dos posiciones zodiacales.
        """
        diff = abs(pos1 - pos2)
        if diff > 180:
            diff = 360 - diff
        return diff

    def _add_moon_phase_house_events(self):
        """Agrega información de casas natales y conjunciones a eventos de lunas"""
        for event in self.general_events:
            if event.tipo_evento in [EventType.LUNA_NUEVA, EventType.LUNA_LLENA]:
                # Crear copia del evento con información natal
                natal_event = AstroEvent(
                    fecha_utc=event.fecha_utc,
                    tipo_evento=event.tipo_evento,
                    descripcion=event.descripcion,
                    signo=event.signo,
                    grado=event.grado,
                    longitud1=event.longitud1,
                    timezone_str=self.location.timezone  # Usar la zona horaria del usuario
                )
                
                # Calcular casa natal
                casa = self._determinar_casa_natal(event.longitud1)
                if casa:
                    natal_event.casa_natal = casa
                    natal_event.descripcion += f" en Casa {casa}"
                    self.personal_events.append(natal_event)
                
                # Verificar conjunciones con planetas natales
                # Para luna llena usamos la posición de la luna, para luna nueva la posición del sol
                pos = event.longitud1
                if event.tipo_evento == EventType.LUNA_NUEVA:
                    # Para luna nueva, sumar 180° a la posición de la luna para obtener la posición del sol
                    pos = (pos + 180) % 360
                
                for planet_name, data in self.natal_data['points'].items():
                    if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                                     'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                        planet_pos = self._convertir_a_grados_absolutos(
                            data['sign'],
                            self._parsear_posicion(data['position'])
                        )
                        orb = self._calcular_orbe(pos, planet_pos)
                        
                        if orb <= 4.0:  # Orbe de 4°
                            # Mapeo de nombres de planetas
                            PLANET_NAMES = {
                                'Sun': 'Sol', 'Moon': 'Luna', 'Mercury': 'Mercurio',
                                'Venus': 'Venus', 'Mars': 'Marte', 'Jupiter': 'Júpiter',
                                'Saturn': 'Saturno', 'Uranus': 'Urano',
                                'Neptune': 'Neptuno', 'Pluto': 'Plutón'
                            }
                            
                            # Crear evento para la conjunción
                            tipo = "Luna llena" if event.tipo_evento == EventType.LUNA_LLENA else "Luna nueva"
                            planeta1 = "Luna" if event.tipo_evento == EventType.LUNA_LLENA else "Sol"
                            grado = event.grado
                            conj_event = AstroEvent(
                                fecha_utc=event.fecha_utc,
                                tipo_evento=EventType.ASPECTO,
                                descripcion=f"{tipo} en {event.signo} {AstroEvent.format_degree(grado)} en conjunción con {PLANET_NAMES[planet_name]} natal",
                                planeta1=planeta1,
                                planeta2=PLANET_NAMES[planet_name],
                                longitud1=pos,
                                longitud2=planet_pos,
                                tipo_aspecto="Conjunción",
                                orbe=orb,
                                timezone_str=self.location.timezone  # Usar la zona horaria del usuario
                            )
                            self.personal_events.append(conj_event)

    def _add_eclipse_house_events(self):
        """Agrega información de casas natales y conjunciones a eventos de eclipses"""
        for event in self.general_events:
            if event.tipo_evento in [EventType.ECLIPSE_SOLAR, EventType.ECLIPSE_LUNAR]:
                # Crear copia del evento con información natal
                natal_event = AstroEvent(
                    fecha_utc=event.fecha_utc,
                    tipo_evento=event.tipo_evento,
                    descripcion=event.descripcion,
                    signo=event.signo,
                    grado=event.grado,
                    longitud1=event.longitud1,
                    timezone_str=self.location.timezone  # Usar la zona horaria del usuario
                )
                
                # Calcular casa natal
                casa = self._determinar_casa_natal(event.longitud1)
                if casa:
                    natal_event.casa_natal = casa
                    natal_event.descripcion += f" en Casa {casa}"
                    self.personal_events.append(natal_event)
                
                # Verificar conjunciones con planetas natales
                # Para eclipse lunar usamos la posición de la luna, para eclipse solar la posición del sol
                pos = event.longitud1
                if event.tipo_evento == EventType.ECLIPSE_SOLAR:
                    # Para eclipse solar, sumar 180° a la posición de la luna para obtener la posición del sol
                    pos = (pos + 180) % 360
                
                for planet_name, data in self.natal_data['points'].items():
                    if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                                     'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                        planet_pos = self._convertir_a_grados_absolutos(
                            data['sign'],
                            self._parsear_posicion(data['position'])
                        )
                        orb = self._calcular_orbe(pos, planet_pos)
                        
                        if orb <= 4.0:  # Orbe de 4°
                            # Mapeo de nombres de planetas
                            PLANET_NAMES = {
                                'Sun': 'Sol', 'Moon': 'Luna', 'Mercury': 'Mercurio',
                                'Venus': 'Venus', 'Mars': 'Marte', 'Jupiter': 'Júpiter',
                                'Saturn': 'Saturno', 'Uranus': 'Urano',
                                'Neptune': 'Neptuno', 'Pluto': 'Plutón'
                            }
                            
                            # Crear evento para la conjunción
                            tipo = "Eclipse lunar" if event.tipo_evento == EventType.ECLIPSE_LUNAR else "Eclipse solar"
                            planeta1 = "Luna" if event.tipo_evento == EventType.ECLIPSE_LUNAR else "Sol"
                            grado = event.grado
                            conj_event = AstroEvent(
                                fecha_utc=event.fecha_utc,
                                tipo_evento=EventType.ASPECTO,
                                descripcion=f"{tipo} en {event.signo} {AstroEvent.format_degree(grado)} en conjunción con {PLANET_NAMES[planet_name]} natal",
                                planeta1=planeta1,
                                planeta2=PLANET_NAMES[planet_name],
                                longitud1=pos,
                                longitud2=planet_pos,
                                tipo_aspecto="Conjunción",
                                orbe=orb,
                                timezone_str=self.location.timezone  # Usar la zona horaria del usuario
                            )
                            self.personal_events.append(conj_event)

    def _determinar_casa_natal(self, longitud: float) -> Optional[int]:
        """Determina la casa natal para una posición zodiacal"""
        from src.calculators.new_moon_houses import determinar_casa_natal
        signo = AstronomicalConstants.get_sign_name(longitud)
        grado = longitud % 30
        try:
            return determinar_casa_natal(signo, grado, self.natal_data['houses'], debug=False)
        except Exception:
            return None

    def save_to_csv(self) -> tuple[str, Optional[str]]:
        """
        Guarda los eventos en archivos CSV.
        
        Returns:
            Tupla con (nombre_archivo_general, nombre_archivo_personal)
            El segundo elemento es None si no hay eventos personales
        """
        # Guardar eventos generales
        general_filename = config.get_general_events_filename(self.year)
        CSVWriter.write_events(self.general_events, general_filename)
        
        # Guardar eventos personales si existen
        personal_filename = None
        if self.natal_data and 'name' in self.natal_data:
            # La lista self.personal_events ya contiene los eventos filtrados
            # (si se usó V4) o todos los eventos (si se usaron otros calculadores).
            # El filtrado de Aspectos "Exacto"/"Estacionario" ahora se hace DENTRO de V4.
            # Simplemente preparamos los eventos para el CSV writer.
            
            events_to_write = []
            for event in self.personal_events:
                 # Crear una copia o modificar directamente si es seguro
                 # Eliminar campos no deseados antes de escribir
                 event.elevacion = None
                 event.azimut = None
                 events_to_write.append(event)

            print(f"Total de eventos personales a escribir: {len(events_to_write)}")
            
            personal_filename = config.get_personal_events_filename(
                self.natal_data['name'], 
                self.year
            )
            # Escribir los eventos personales (ya filtrados por V4 si aplica)
            CSVWriter.write_events(events_to_write, personal_filename)
        
        return general_filename, personal_filename

def solicitar_datos_natales() -> tuple[dict, str]:
    """Solicita al usuario sus datos natales."""
    print("\n=== Datos Natales ===")
    try:
        # Solicitar nombre
        while True:
            nombre = input("Ingrese su nombre completo: ")
            if not config.validate_name(nombre):
                print("Error: El nombre debe contener solo letras, números, espacios y caracteres básicos")
                continue
            break

        # Solicitar lugar de nacimiento
        lugar = input("Ingrese su lugar de nacimiento (Ciudad, País): ")
        
        # Solicitar fecha y hora
        while True:
            fecha = input("Ingrese su fecha de nacimiento (YYYY-MM-DD): ")
            if not config.validate_date(fecha):
                print("Error: Por favor use el formato YYYY-MM-DD (ejemplo: 1964-12-26)")
                continue
            break
        
        while True:
            hora = input("Ingrese su hora de nacimiento (HH:MM): ")
            if not config.validate_time(hora):
                print("Error: Por favor use el formato HH:MM en 24 horas (ejemplo: 21:12)")
                continue
            break

        # Obtener datos de ubicación
        location = create_location_from_place(lugar)
        
        # Preparar datos para el cálculo
        datos_usuario = {
            "hora_local": f"{fecha}T{hora}:00",
            "lat": location.lat,
            "lon": location.lon,
            "zona_horaria": location.timezone,
            "lugar": lugar
        }
        
        # Calcular carta natal
        natal_data = calcular_carta_natal(datos_usuario)
        
        # Agregar el nombre a los datos natales
        natal_data['name'] = nombre
        
        # Retornar tanto los datos natales como el nombre
        return natal_data, nombre
        
    except Exception as e:
        print(f"Error al obtener datos natales: {str(e)}")
        return None, None

def main():
    try:
        start_time = time.time()  # Inicio total
        
        # Solicitar datos natales
        print("Bienvenido al Calendario Astrológico Personalizado")
        natal_data, nombre = solicitar_datos_natales()
        
        if natal_data:
            print("\nCarta natal calculada exitosamente!")
            print("\nCarta Natal:")
            print("-" * 50)
            
            # Mostrar datos de ubicación
            loc = natal_data['location']
            print(f"Lugar: {loc['name']}")
            print(f"Coordenadas: {loc['latitude']:.2f}°, {loc['longitude']:.2f}°")
            print(f"Zona Horaria: {loc['timezone']}")
            
            # Posiciones planetarias
            print("\nPosiciones Planetarias:")
            print("-" * 30)
            for planeta, datos in natal_data['points'].items():
                if planeta in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                             'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                    retro = " (R)" if datos.get('retrograde') else ""
                    print(f"{planeta:8}: {datos['sign']} {datos['position']}{retro}")
            
            # Ángulos principales
            print("\nÁngulos Principales:")
            print("-" * 30)
            for angulo in ['Asc', 'MC', 'Dsc', 'Ic']:
                if angulo in natal_data['points']:
                    datos = natal_data['points'][angulo]
                    print(f"{angulo:8}: {datos['sign']} {datos['position']}")
            
            # Nodos lunares
            print("\nNodos Lunares:")
            print("-" * 30)
            for nodo in ['North Node', 'South Node']:
                if nodo in natal_data['points']:
                    datos = natal_data['points'][nodo]
                    print(f"{nodo:12}: {datos['sign']} {datos['position']}")
            
            # Casas
            print("\nCasas Astrológicas:")
            print("-" * 30)
            for num, datos in natal_data['houses'].items():
                print(f"Casa {num:2}: {datos['sign']} {datos['position']}")
            
            print("\n" + "="*50 + "\n")
            
            # Guardar carta natal
            natal_filename = config.get_natal_chart_filename(nombre)
            with open(natal_filename, "w", encoding='utf-8') as f:
                json.dump(natal_data, f, indent=2, ensure_ascii=False)
            print(f"Carta natal guardada en: {natal_filename}\n")
        
        # Solicitar año
        while True:
            try:
                year = int(input("\nIngresa el año para el calendario (ejemplo: 2025): "))
                if not config.validate_year(year):
                    print("Error: El año debe estar entre 1900 y 2100")
                    continue
                break
            except ValueError:
                print("Error: Por favor ingrese un número válido")
        
        # Preguntar qué calculador de eclipses se desea utilizar
        use_precise = False
        use_immanuel = False
        while True:
            response = input("\n¿Qué calculador de eclipses desea utilizar? (1: Estándar, 2: Alta precisión, 3: Immanuel): ")
            if response == "1":
                print("Se utilizará el calculador de eclipses estándar.")
                break
            elif response == "2":
                use_precise = True
                print("Se utilizará el calculador de eclipses de alta precisión.")
                break
            elif response == "3":
                use_immanuel = True
                print("Se utilizará el calculador de eclipses basado en Immanuel.")
                break
            else:
                print("Por favor, responda '1', '2' o '3'.")
                
        # Preguntar qué calculador de tránsitos desea utilizar
        use_parallel = False
        calculator_type = "standard"
        while True:
            response = input("\n¿Qué calculador de tránsitos desea utilizar?\n"
                           "1: Estándar (más lento pero probado)\n"
                           "2: Paralelo (procesamiento multi-núcleo, 3-5x más rápido)\n"
                           "3: Astronómico V3 (Recomendado: rápido y preciso)\n"
                           "4: Astronómico V4 (Experimental: optimizaciones)\n"
                           "Seleccione una opción (1/2/3/4): ")
            if response == "1":
                calculator_type = "standard"
                print("Se utilizará el calculador de tránsitos estándar.")
                break
            elif response == "2":
                use_parallel = True
                calculator_type = "standard" # Parallel uses standard logic internally
                print("Se utilizará el calculador de tránsitos paralelo.")
                break
            elif response == "3":
                calculator_type = "astronomical_v3"
                print("Se utilizará el calculador de tránsitos astronómico V3 (mejorado).")
                break
            elif response == "4":
                calculator_type = "astronomical_v4"
                print("Se utilizará el calculador de tránsitos astronómico V4 (experimental).")
                break
            else:
                print("Por favor, seleccione una opción válida (1, 2, 3 o 4).")
                
        # Preguntar si se desea calcular conjunciones de Luna progresada
        calculate_progressed_moon = False
        while True:
            response = input("\n¿Desea calcular conjunciones de Luna progresada con planetas natales? (s/n): ").lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                calculate_progressed_moon = True
                print("Se calcularán conjunciones de Luna progresada.")
                break
            elif response in ['n', 'no']:
                print("No se calcularán conjunciones de Luna progresada.")
                break
            else:
                print("Por favor, responda 's' o 'n'.")
                
        # Preguntar si se desea calcular profecciones anuales
        calculate_profections = False
        while True:
            response = input("\n¿Desea calcular profecciones anuales? (s/n): ").lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                calculate_profections = True
                print("Se calcularán profecciones anuales.")
                break
            elif response in ['n', 'no']:
                print("No se calcularán profecciones anuales.")
                break
            else:
                print("Por favor, responda 's' o 'n'.")

        # Crear calendario y calcular eventos
        calendar = AstronomicalCalendar(year, natal_data, use_precise, use_immanuel, use_parallel, 
                                       calculate_progressed_moon, calculate_profections,
                                       transits_calculator_type=calculator_type)
        calendar.calculate_all_events()

        # Guardar resultados
        general_filename, personal_filename = calendar.save_to_csv()

        # Mostrar confirmación
        print(f"\nSe ha generado el archivo general: {general_filename}")
        print(f"Eventos astronómicos generales: {len(calendar.general_events)}")
        
        if personal_filename:
            print(f"\nSe ha generado el archivo personal: {personal_filename}")
            print(f"Eventos personales: {len(calendar.personal_events)}")
        
        # Mostrar tiempo total
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\nTiempo total de ejecución: {total_time:.2f} segundos")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
