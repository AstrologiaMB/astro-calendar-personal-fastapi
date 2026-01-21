from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
from .constants import EventType, AstronomicalConstants

@dataclass
class AstroEvent:
    """Clase base para eventos astronómicos"""
    fecha_utc: datetime
    tipo_evento: EventType
    descripcion: str
    elevacion: Optional[float] = None
    azimut: Optional[float] = None
    # Campos para aspectos
    planeta1: Optional[str] = None
    planeta2: Optional[str] = None
    longitud1: Optional[float] = None
    longitud2: Optional[float] = None
    velocidad1: Optional[float] = None
    velocidad2: Optional[float] = None
    tipo_aspecto: Optional[str] = None
    orbe: Optional[float] = None
    es_aplicativo: Optional[bool] = None
    # Campos para signos y grados
    signo: Optional[str] = None
    grado: Optional[float] = None
    # Campos para información natal
    casa_natal: Optional[int] = None
    planeta_natal: Optional[str] = None
    posicion_natal: Optional[float] = None
    # Campo para visibilidad local de eclipses
    visibilidad_local: Optional[str] = None
    # Zona horaria para conversión a hora local
    timezone_str: str = "UTC"
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Nueva clasificación de importancia (high, medium, low)
    relevance: str = "low"

    def __post_init__(self):
        """Inicialización posterior con validaciones y cálculos adicionales"""
        # Asegurar que fecha_utc tenga zona horaria UTC
        if self.fecha_utc.tzinfo is None:
            # Si no tiene zona horaria, asumir que es UTC
            self.fecha_utc = self.fecha_utc.replace(tzinfo=ZoneInfo("UTC"))
            
        # Convertir a hora local usando la zona horaria proporcionada
        try:
            tz_local = ZoneInfo(self.timezone_str)
        except Exception:
            # Si hay un error con la zona horaria proporcionada, usar UTC
            print(f"Error al obtener zona horaria {self.timezone_str}, usando UTC")
            tz_local = ZoneInfo("UTC")
            
        self.fecha_local = self.fecha_utc.astimezone(tz_local)
        
        # Para aspectos, calcular datos adicionales
        if self.tipo_evento == EventType.ASPECTO:
            self._calculate_aspect_details()

    def _calculate_aspect_details(self):
        """Calcula detalles adicionales para aspectos"""
        if self.tipo_evento == EventType.ASPECTO and self.longitud1 is not None and self.longitud2 is not None:
            # Calcular signos zodiacales
            self.signo1 = AstronomicalConstants.get_sign_name(self.longitud1)
            self.signo2 = AstronomicalConstants.get_sign_name(self.longitud2)
            
            # Calcular grados en signo
            self.grado1 = self.longitud1 % 30
            self.grado2 = self.longitud2 % 30

    @staticmethod
    def format_degree(degree: float) -> str:
        """Formatea un grado decimal a formato sexagesimal (grados, minutos, segundos)"""
        # Obtener la parte entera (grados)
        degrees = int(degree)
        
        # Calcular los minutos
        minutes_decimal = (degree - degrees) * 60
        minutes = int(minutes_decimal)
        
        # Calcular los segundos
        seconds = int((minutes_decimal - minutes) * 60)
        
        return f"{degrees}°{minutes:02d}'{seconds:02d}\""
        
    def format_position(self, longitude: float) -> str:
        """Formatea una posición zodiacal"""
        sign = AstronomicalConstants.get_sign_name(longitude)
        degree = longitude % 30
        formatted_degree = self.format_degree(degree)
        return f"{formatted_degree} {sign}"

    def to_dict(self) -> dict:
        """Convierte el evento a un diccionario para CSV"""
        base_dict = {
            'fecha_utc': self.fecha_utc.strftime('%Y-%m-%d'),
            'hora_utc': self.fecha_utc.strftime('%H:%M'),
            'fecha_local': self.fecha_local.strftime('%Y-%m-%d'),
            'hora_local': self.fecha_local.strftime('%H:%M'),
            'tipo_evento': self.tipo_evento.value,
            'descripcion': self.descripcion,
            'elevacion': f"{self.elevacion:.1f}°" if self.elevacion is not None else "",
            'azimut': f"{self.azimut:.1f}°" if self.azimut is not None else ""
        }
        
        # Añadir campo de visibilidad local si existe
        if self.visibilidad_local is not None:
            base_dict['visibilidad_local'] = self.visibilidad_local
        
        # Añadir campos específicos de aspectos si es necesario
        if self.tipo_evento == EventType.ASPECTO or self.tipo_evento == EventType.LUNA_PROGRESADA:
            aspect_dict = {
                'planeta1': self.planeta1,
                'planeta2': self.planeta2,
                'posicion1': self.format_position(self.longitud1) if self.longitud1 is not None else "",
                'posicion2': self.format_position(self.longitud2) if self.longitud2 is not None else "",
                'tipo_aspecto': self.tipo_aspecto,
                'orbe': self.format_degree(self.orbe) if self.orbe is not None else "",
                'es_aplicativo': "Sí" if self.es_aplicativo else "No"
            }
            
            # Asegurar que el estado esté presente para eventos de Luna progresada
            if self.tipo_evento == EventType.LUNA_PROGRESADA and 'estado' not in self.metadata:
                self.metadata['estado'] = "Exacto"  # Por defecto, considerar exacto
                
            base_dict.update(aspect_dict)
        
        # Añadir campos de signo y grado para lunas y eclipses
        elif self.tipo_evento in [EventType.LUNA_NUEVA, EventType.LUNA_LLENA, 
                                EventType.ECLIPSE_SOLAR, EventType.ECLIPSE_LUNAR]:
            if self.signo is not None and self.grado is not None:
                phase_dict = {
                    'signo': self.signo,
                    'grado': self.format_degree(self.grado),
                    'posicion': self.format_position(self.longitud1) if self.longitud1 is not None else ""
                }
                base_dict.update(phase_dict)
            
        # Añadir campos natales si existen
        natal_dict = {}
        if self.casa_natal is not None:
            natal_dict['casa_natal'] = self.casa_natal
        if self.planeta_natal is not None:
            natal_dict['planeta_natal'] = self.planeta_natal
        if self.posicion_natal is not None:
            natal_dict['posicion_natal'] = self.format_position(self.posicion_natal)
        base_dict.update(natal_dict)

        # Añadir metadata adicional
        base_dict.update(self.metadata)
        
        return base_dict
