"""
Módulo para calcular conjunciones entre la Luna progresada y planetas natales.
Versión optimizada con algoritmo simplificado y validado astronómicamente.
"""
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.core import config
from src.core.base_event import AstroEvent
from src.core.constants import EventType, AstronomicalConstants
import immanuel.charts as charts
from immanuel.const import chart, calc
from immanuel.setup import settings
from immanuel.tools import ephemeris, date, forecast
import swisseph as swe

# Configuración de immanuel para aspectos
settings.aspects = [calc.CONJUNCTION]  # Solo conjunciones
settings.default_orb = 2.0  # Orbe de 2° para Luna progresada
settings.exact_orb = 0.001  # Aspecto exacto dentro de 0.001°

# Mapeo de IDs a nombres de planetas
PLANET_NAMES = {
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

# Lista de planetas a procesar (excluye Luna para evitar conjunción consigo misma)
PLANETS_TO_CHECK = [
    chart.SUN,
    chart.MERCURY,
    chart.VENUS,
    chart.MARS,
    chart.JUPITER,
    chart.SATURN,
    chart.URANUS,
    chart.NEPTUNE,
    chart.PLUTO
]

# Mapeo de aspectos
ASPECT_NAMES = {
    calc.CONJUNCTION: "Conjunción"
}

# Mapeo de estado del aspecto
ASPECT_STATE = {
    calc.APPLICATIVE: "Aplicativo",
    calc.EXACT: "Exacto",
    calc.SEPARATIVE: "Separativo"
}

class ProgressedMoonTransitsCalculator:
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de conjunciones de Luna progresada.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
        """
        self.natal_data = natal_data
        
        # Obtener la zona horaria del usuario desde los datos natales
        self.user_timezone = ZoneInfo("UTC")  # Default a UTC
        if 'location' in natal_data and 'timezone' in natal_data['location']:
            try:
                self.user_timezone = ZoneInfo(natal_data['location']['timezone'])
            except Exception:
                # Si hay un error al obtener la zona horaria, usar UTC
                print(f"Error al obtener zona horaria {natal_data['location']['timezone']}, usando UTC")
        
        # Extraer fecha de nacimiento de los datos natales
        self.birth_date = datetime(1980, 1, 1, tzinfo=self.user_timezone)
        
        # Si hay una fecha en los datos natales en formato ISO, usarla
        if 'date' in natal_data:
            birth_date_str = natal_data['date']
            self.birth_date = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
            print(f"Usando fecha de nacimiento de 'date': {self.birth_date}")
        # Si no, intentar extraerla de la hora_local en datos_usuario
        elif 'hora_local' in natal_data:
            try:
                # La hora_local está en formato ISO
                birth_date_str = natal_data['hora_local']
                
                # Primero, convertir a datetime sin zona horaria
                if '+' in birth_date_str or '-' in birth_date_str[10:]:
                    # Ya tiene zona horaria, usar directamente
                    dt = datetime.fromisoformat(birth_date_str)
                else:
                    # No tiene zona horaria, asumir que ya está en la zona horaria del usuario
                    dt = datetime.fromisoformat(birth_date_str)
                    dt = dt.replace(tzinfo=self.user_timezone)
                
                # Asegurarse de que esté en la zona horaria del usuario
                self.birth_date = dt if dt.tzinfo == self.user_timezone else dt.astimezone(self.user_timezone)
                print(f"Usando fecha de nacimiento de 'hora_local': {self.birth_date}")
                
                # Añadir la fecha al formato 'date' para compatibilidad
                natal_data['date'] = self.birth_date.isoformat()
            except Exception as e:
                print(f"Error al extraer fecha de nacimiento de hora_local: {e}")
        
        # Si aún no tenemos fecha de nacimiento, intentar reconstruirla a partir de los datos disponibles
        if self.birth_date.year == 1980:  # Si seguimos usando la fecha por defecto
            try:
                # Usar la posición del Sol como referencia
                if 'points' in natal_data and 'Sun' in natal_data['points']:
                    sun_longitude = natal_data['points']['Sun']['longitude']
                    
                    # Estimar el mes y día a partir de la posición del Sol
                    month = int(sun_longitude / 30) + 1  # 0° = Aries = Marzo
                    if month > 12:
                        month -= 12
                    day = int((sun_longitude % 30) / 30 * 30) + 1
                    
                    # Usar un año razonable (30 años atrás)
                    current_year = datetime.now().year
                    
                    # Crear la fecha de nacimiento
                    self.birth_date = datetime(current_year - 30, month, min(day, 28), 12, 0, tzinfo=self.user_timezone)
                    print(f"Usando fecha de nacimiento aproximada basada en la posición del Sol: {self.birth_date}")
            except Exception as e:
                print(f"Error al reconstruir fecha de nacimiento: {e}")
                print("Usando fecha de nacimiento por defecto")
        
        # Crear diccionario de posiciones natales
        self.natal_positions = {}
        for planet_name, data in natal_data['points'].items():
            if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                             'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
                self.natal_positions[getattr(chart, planet_name.upper())] = {
                    'longitude': data['longitude'],
                    'latitude': 0,
                    'distance': 0,
                    'speed': 0
                }

    def _calculate_progressed_moon_position(self, current_date: datetime) -> float:
        """
        Calcula la posición de la Luna progresada para una fecha específica utilizando
        el método ARMC 1 Naibod, que es el método utilizado por AstroSeek.
        
        Args:
            current_date: Fecha para la que calcular la Luna progresada
            
        Returns:
            Posición de la Luna progresada en grados absolutos (0-360)
        """
        try:
            # Si la fecha es anterior o igual a la fecha de nacimiento, devolver la posición natal
            if current_date <= self.birth_date:
                return self.natal_positions[chart.MOON]['longitude']
                
            # Asegurar que las fechas estén en UTC antes de convertirlas a fechas julianas
            birth_date_utc = self.birth_date.astimezone(ZoneInfo("UTC"))
            current_date_utc = current_date.astimezone(ZoneInfo("UTC"))
            
            # Convertir la fecha de nacimiento a fecha juliana
            birth_jd = date.to_jd(birth_date_utc)
            
            # Convertir la fecha actual a fecha juliana
            current_jd = date.to_jd(current_date_utc)
            
            # Calcular años transcurridos (para el cálculo de la progresión)
            # Usamos el año solar exacto (365.24219893 días)
            year_days = calc.YEAR_DAYS
            years_passed = (current_jd - birth_jd) / year_days
            
            # Calcular la fecha juliana progresada y el ARMC progresado usando el método Naibod
            progressed_jd = birth_jd + years_passed
            
            # Obtener el ARMC natal
            natal_armc = ephemeris.angle(
                index=chart.ARMC,
                jd=birth_jd,
                lat=self.natal_data['location']['latitude'],
                lon=self.natal_data['location']['longitude'],
                house_system=chart.PLACIDUS  # AstroSeek usa Placidus por defecto
            )['lon']
            
            # Calcular el ARMC progresado usando el método Naibod
            # El método Naibod avanza el ARMC a razón del movimiento medio del Sol (0.98564733° por día)
            progressed_armc_lon = swe.degnorm(natal_armc + years_passed * calc.MEAN_MOTIONS[chart.SUN])
            
            # Calcular la oblicuidad de la eclíptica para la fecha progresada
            obliquity = ephemeris.obliquity(progressed_jd)
            
            # Obtener la posición de la Luna para la fecha progresada
            progressed_objects = ephemeris.armc_objects(
                object_list=[chart.MOON],
                jd=progressed_jd,
                armc=progressed_armc_lon,
                lat=self.natal_data['location']['latitude'],
                lon=self.natal_data['location']['longitude'],
                obliquity=obliquity,
                house_system=chart.PLACIDUS
            )
            
            # Devolver la longitud de la Luna progresada
            return progressed_objects[chart.MOON]['lon']
            
        except Exception as e:
            print(f"Error al calcular la Luna progresada: {e}")
            # Fallback a un método más simple si hay un error
            years_passed = (current_date - self.birth_date).total_seconds() / (365.25 * 24 * 60 * 60)
            # Velocidad media de la Luna progresada (aproximadamente 13.2° por año)
            moon_advancement = years_passed * 13.2
            natal_moon_pos = self.natal_positions[chart.MOON]['longitude']
            progressed_pos = (natal_moon_pos + moon_advancement) % 360
            return progressed_pos

    def _find_conjunction_simple(self, planet_id: int, start_date: datetime, end_date: datetime) -> tuple:
        """
        Algoritmo simplificado para encontrar conjunción de Luna progresada.
        Busca día a día dentro del período especificado respetando límites temporales.
        
        Args:
            planet_id: ID del planeta natal
            start_date: Fecha inicial del período
            end_date: Fecha final del período
            
        Returns:
            Tupla (fecha de conjunción, orbe, posición Luna progresada) o None si no hay conjunción
        """
        natal_pos = self.natal_positions[planet_id]['longitude']
        
        best_date = None
        min_orb = float('inf')
        best_prog_pos = None
        
        # Buscar día a día (la Luna progresada se mueve muy lentamente)
        current = start_date
        days_checked = 0
        
        while current <= end_date:
            # Calcular posición de Luna progresada
            prog_moon_pos = self._calculate_progressed_moon_position(current)
            
            # Calcular diferencia angular
            diff = abs(prog_moon_pos - natal_pos)
            if diff > 180:
                diff = 360 - diff
            
            # Si está dentro del orbe y es mejor que el anterior
            if diff <= settings.default_orb and diff < min_orb:
                min_orb = diff
                best_date = current
                best_prog_pos = prog_moon_pos
                
            days_checked += 1
            current += timedelta(days=1)
        
        if best_date:
            return (best_date, min_orb, best_prog_pos)
        else:
            return None

    def _format_degree_simple(self, degrees: float) -> str:
        """
        Formatea grados en formato simple para descripción.
        
        Args:
            degrees: Grados decimales
            
        Returns:
            Formato: "5°16'"
        """
        whole_degrees = int(degrees)
        minutes = int((degrees - whole_degrees) * 60)
        return f"{whole_degrees}°{minutes}'"

    def _determinar_casa_natal(self, longitud: float) -> int:
        """
        Determina la casa natal para una posición zodiacal.
        
        Args:
            longitud: Longitud eclíptica en grados
            
        Returns:
            Número de casa natal (1-12) o None si no se puede determinar
        """
        try:
            from src.calculators.new_moon_houses import determinar_casa_natal
            signo = AstronomicalConstants.get_sign_name(longitud)
            grado = longitud % 30
            return determinar_casa_natal(signo, grado, self.natal_data['houses'], debug=False)
        except Exception as e:
            print(f"Error determinando casa natal: {e}")
            return None

    def calculate_all(self, start_date: datetime = None, end_date: datetime = None) -> list:
        """
        Calcula todas las conjunciones de Luna progresada para el período especificado
        usando el algoritmo optimizado.
        
        Args:
            start_date: Fecha inicial (default: 1 enero del año actual)
            end_date: Fecha final (default: 31 diciembre del año actual)
            
        Returns:
            Lista de eventos de conjunciones
        """
        # Si no se especifican fechas, usar el año actual completo
        if not start_date:
            start_date = datetime(datetime.now().year, 1, 1, tzinfo=ZoneInfo("UTC"))
        if not end_date:
            end_date = datetime(datetime.now().year, 12, 31, 23, 59, tzinfo=ZoneInfo("UTC"))

        # Registrar tiempo de inicio
        start_time = time.time()
        
        print("\nCalculando conjunciones de Luna progresada con algoritmo optimizado...")
        
        # Lista para almacenar eventos
        all_events = []
        
        # Verificar conjunciones para cada planeta natal
        for planet_id in PLANETS_TO_CHECK:
            if planet_id in self.natal_positions:
                # Buscar conjunción usando algoritmo simplificado
                result = self._find_conjunction_simple(planet_id, start_date, end_date)
                
                if result:
                    conj_date, orb, prog_moon_pos = result
                    
                    # Obtener signo y grado para la posición de la Luna progresada
                    moon_sign = AstronomicalConstants.get_sign_name(prog_moon_pos)
                    moon_degree = prog_moon_pos % 30
                    
                    # Obtener signo y grado para la posición natal
                    natal_pos = self.natal_positions[planet_id]['longitude']
                    natal_sign = AstronomicalConstants.get_sign_name(natal_pos)
                    natal_degree = natal_pos % 30
                    
                    # Formatear posiciones en formato de grados
                    def format_position(degrees):
                        whole_degrees = int(degrees)
                        minutes_decimal = (degrees - whole_degrees) * 60
                        minutes = int(minutes_decimal)
                        seconds = int((minutes_decimal - minutes) * 60)
                        return f"{whole_degrees}°{minutes}'{seconds}\""
                    
                    moon_position_str = f"{format_position(moon_degree)} {moon_sign}"
                    natal_position_str = f"{format_position(natal_degree)} {natal_sign}"
                    
                    # Determinar casa natal donde ocurre la conjunción
                    casa_natal = self._determinar_casa_natal(prog_moon_pos)
                    
                    # Crear descripción enriquecida
                    base_desc = f"Luna progresada Conjunción {PLANET_NAMES[planet_id]} Natal en {moon_sign} {self._format_degree_simple(moon_degree)}"
                    if casa_natal:
                        descripcion = f"{base_desc} en Casa {casa_natal}"
                    else:
                        descripcion = base_desc
                    
                    # Convertir la fecha a la zona horaria del usuario para mostrarla correctamente
                    local_conj_date = conj_date.astimezone(self.user_timezone)
                    
                    # Crear evento
                    event = AstroEvent(
                        fecha_utc=conj_date,
                        tipo_evento=EventType.LUNA_PROGRESADA,
                        descripcion=descripcion,
                        planeta1="Luna Progresada",
                        planeta2=PLANET_NAMES[planet_id],
                        longitud1=prog_moon_pos,
                        longitud2=natal_pos,
                        tipo_aspecto="Conjunción",
                        orbe=orb,
                        es_aplicativo=(orb > settings.exact_orb),
                        casa_natal=casa_natal,
                        signo=moon_sign,
                        grado=self._format_degree_simple(moon_degree),
                        metadata={
                            'estado': ASPECT_STATE[calc.EXACT] if orb <= settings.exact_orb else ASPECT_STATE[calc.APPLICATIVE],
                            'movimiento': 'Directo',  # La Luna progresada siempre se mueve en dirección directa
                            'posicion1': moon_position_str,
                            'posicion2': natal_position_str
                        },
                        timezone_str=self.user_timezone.key  # Usar la zona horaria del usuario
                    )
                    all_events.append(event)
                    print(f"Encontrada conjunción con {PLANET_NAMES[planet_id]} el {conj_date.strftime('%Y-%m-%d')} (orbe: {orb:.2f}°)")
        
        # Ordenar eventos por fecha
        all_events.sort(key=lambda x: x.fecha_utc)
        
        # Mostrar resumen
        elapsed = time.time() - start_time
        print(f"\nCálculo completado en {elapsed:.2f} segundos")
        print(f"Total de conjunciones encontradas: {len(all_events)}")
        
        return all_events
