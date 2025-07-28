"""
Módulo para calcular profecciones anuales en astrología.
Implementa el método tradicional de profecciones donde cada signo representa un año de vida.
"""
from datetime import datetime, timedelta
from src.core.base_event import AstroEvent
from src.core.constants import EventType

class ProfectionsCalculator:
    def __init__(self, natal_data: dict):
        """
        Inicializa el calculador de profecciones.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
        """
        self.natal_data = natal_data
        self.birth_date = None
        self.ascendente_natal = None
        
        # Inicializar datos natales
        self._initialize_natal_data()
        
    def _initialize_natal_data(self):
        """Extrae la fecha de nacimiento y el ascendente del diccionario de datos natales."""
        if 'date' in self.natal_data:
            birth_date_str = self.natal_data['date']
            self.birth_date = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
        
        # Mapeo de signos del inglés al español
        SIGN_TRANSLATION = {
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
            'Pisces': 'Piscis'
        }
        
        # Obtener el signo del ascendente
        if 'points' in self.natal_data and 'Asc' in self.natal_data['points']:
            english_sign = self.natal_data['points']['Asc']['sign']
            # Traducir el signo del inglés al español
            if english_sign in SIGN_TRANSLATION:
                self.ascendente_natal = SIGN_TRANSLATION[english_sign]
                print(f"Signo ascendente traducido: {english_sign} -> {self.ascendente_natal}")
            else:
                self.ascendente_natal = english_sign
                print(f"Advertencia: No se pudo traducir el signo ascendente: {english_sign}")
    
    def calcular_senor_del_anio(self, fecha_objetivo: datetime):
        """
        Calcula el señor del año según las profecciones anuales.
        
        Args:
            fecha_objetivo: Fecha para la que se quiere calcular el señor del año
            
        Returns:
            Diccionario con información sobre el señor del año
        """
        # Verificar que tenemos los datos necesarios
        if not self.birth_date or not self.ascendente_natal:
            return {
                "error": "Datos natales incompletos. Se requiere fecha de nacimiento y ascendente."
            }
        
        # Convertir fechas a objetos datetime
        fecha_obj = fecha_objetivo
        
        # Calcular el último cumpleaños antes de la fecha objetivo
        ultimo_cumple = datetime(fecha_obj.year, self.birth_date.month, self.birth_date.day, 
                                self.birth_date.hour, self.birth_date.minute, tzinfo=fecha_obj.tzinfo)
        
        if ultimo_cumple > fecha_obj:
            ultimo_cumple = datetime(fecha_obj.year - 1, self.birth_date.month, self.birth_date.day,
                                    self.birth_date.hour, self.birth_date.minute, tzinfo=fecha_obj.tzinfo)
        
        # Calcular el próximo cumpleaños después de la fecha objetivo
        proximo_cumple = datetime(fecha_obj.year, self.birth_date.month, self.birth_date.day,
                                 self.birth_date.hour, self.birth_date.minute, tzinfo=fecha_obj.tzinfo)
        
        if proximo_cumple <= fecha_obj:
            proximo_cumple = datetime(fecha_obj.year + 1, self.birth_date.month, self.birth_date.day,
                                     self.birth_date.hour, self.birth_date.minute, tzinfo=fecha_obj.tzinfo)
        
        # Calcular edad en el último cumpleaños
        edad_actual = ultimo_cumple.year - self.birth_date.year
        
        # Calcular edad en el próximo cumpleaños
        edad_proxima = edad_actual + 1
        
        # Mapeo de signos (en orden)
        signos = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", 
                  "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
        
        # Mapeo de regentes tradicionales
        regentes = {
            "Aries": "Marte",
            "Tauro": "Venus",
            "Géminis": "Mercurio",
            "Cáncer": "Luna",
            "Leo": "Sol",
            "Virgo": "Mercurio",
            "Libra": "Venus",
            "Escorpio": "Marte",
            "Sagitario": "Júpiter",
            "Capricornio": "Saturno",
            "Acuario": "Saturno",
            "Piscis": "Júpiter"
        }
        
        # Encontrar índice del signo ascendente
        indice_ascendente = signos.index(self.ascendente_natal)
        
        # Calcular signo profectado actual
        indice_actual = (indice_ascendente + edad_actual) % 12
        signo_actual = signos[indice_actual]
        senor_actual = regentes[signo_actual]
        
        # Calcular próximo signo profectado
        indice_proximo = (indice_ascendente + edad_proxima) % 12
        signo_proximo = signos[indice_proximo]
        senor_proximo = regentes[signo_proximo]
        
        # Calcular cuántos días faltan para el cambio
        dias_para_cambio = (proximo_cumple - fecha_obj).days
        
        return {
            "edad_actual": edad_actual,
            "casa_profectada_actual": f"Casa 1 en {signo_actual}",
            "senor_del_anio_actual": senor_actual,
            "fecha_inicio": ultimo_cumple.strftime("%Y-%m-%d"),
            "fecha_fin": proximo_cumple.strftime("%Y-%m-%d"),
            "dias_para_cambio": dias_para_cambio,
            "proximo_senor_del_anio": senor_proximo,
            "proxima_casa_profectada": f"Casa 1 en {signo_proximo}"
        }
        
    def calculate_profection_events(self, start_date: datetime, end_date: datetime):
        """
        Calcula eventos de profección para un período específico.
        
        Args:
            start_date: Fecha inicial del período
            end_date: Fecha final del período
            
        Returns:
            Lista de eventos de profección
        """
        events = []
        
        # Verificar que tenemos los datos necesarios
        if not self.birth_date or not self.ascendente_natal:
            print("Error: Datos natales incompletos. Se requiere fecha de nacimiento y ascendente.")
            return events
        
        # Verificar si hay un cambio de señor del año en el período
        current_date = start_date
        while current_date <= end_date:
            # Verificar si es el cumpleaños (día de cambio de profección)
            if current_date.month == self.birth_date.month and current_date.day == self.birth_date.day:
                # Calcular profección para este cumpleaños
                profection_data = self.calcular_senor_del_anio(current_date)
                
                # Crear evento para el cambio de señor del año
                event = AstroEvent(
                    fecha_utc=current_date,
                    tipo_evento=EventType.PROFECCION,
                    descripcion=f"Cambio de Señor del Año: {profection_data['senor_del_anio_actual']}",
                    metadata=profection_data
                )
                events.append(event)
            
            # Avanzar al siguiente día
            current_date += timedelta(days=1)
        
        return events
        
    def display_profection_info(self, fecha_objetivo: datetime = None):
        """
        Muestra información detallada sobre la profección actual en formato de consola.
        
        Args:
            fecha_objetivo: Fecha para la que se quiere mostrar la información (por defecto, fecha actual)
        """
        if fecha_objetivo is None:
            fecha_objetivo = datetime.now()
            
        # Calcular profección
        profection_data = self.calcular_senor_del_anio(fecha_objetivo)
        
        # Verificar si hay error
        if 'error' in profection_data:
            print(f"Error: {profection_data['error']}")
            return
            
        # Mostrar información en formato de consola con bordes
        print("╔══════════════════════════════════════════════════════════╗")
        print("║                   PROFECCIONES ANUALES                   ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║ Fecha de nacimiento: {self.birth_date.strftime('%d/%m/%Y %H:%M')} ({self.natal_data['location']['name']})".ljust(62) + "║")
        print(f"║ Fecha de consulta:   {fecha_objetivo.strftime('%d/%m/%Y')}".ljust(62) + "║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║ Edad actual:         {profection_data['edad_actual']} años".ljust(62) + "║")
        print(f"║ Casa profectada:     {profection_data['casa_profectada_actual']}".ljust(62) + "║")
        print(f"║ SEÑOR DEL AÑO:       {profection_data['senor_del_anio_actual']}".ljust(62) + "║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║ Período activo:      {profection_data['fecha_inicio']} - {profection_data['fecha_fin']}".ljust(62) + "║")
        print(f"║ Días restantes:      {profection_data['dias_para_cambio']} días".ljust(62) + "║")
        print(f"║ Próximo señor:       {profection_data['proximo_senor_del_anio']} ({profection_data['proxima_casa_profectada'].split(' en ')[1]})".ljust(62) + "║")
        print("╚══════════════════════════════════════════════════════════╝")
