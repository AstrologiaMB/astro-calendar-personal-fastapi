from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class RelevanceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class HouseTransitStrict(BaseModel):
    """Modelo estricto para tránsitos por casas."""
    tipo: str = Field(..., description="Tipo de tránsito (ej. 'transito_planetario', 'luna_progresada')")
    planeta: str
    simbolo: str
    signo: Optional[str] = None
    grado: Optional[float] = None
    casa: int
    casa_significado: str

class AstroEventStrict(BaseModel):
    """
    Modelo estricto para eventos astrológicos.
    Elimina la ambigüedad de 'Dict[str, Any]' y fuerza tipos concretos.
    """
    model_config = ConfigDict(from_attributes=True)

    # Core Fields
    fecha_utc: datetime = Field(..., description="Fecha y hora exacta en UTC")
    hora_utc: str = Field(..., description="Hora formateada HH:MM para compatibilidad UI")
    tipo_evento: str
    descripcion: str
    relevance: RelevanceLevel = Field(default=RelevanceLevel.LOW)

    # Aspect Fields (Optional)
    planeta1: Optional[str] = None
    planeta2: Optional[str] = None
    posicion1: Optional[str] = None
    posicion2: Optional[str] = None
    tipo_aspecto: Optional[str] = None
    orbe: Optional[str] = None
    es_aplicativo: Optional[str] = None
    harmony: Optional[str] = None
    
    # Location/Geometry Fields
    elevacion: Optional[str] = None
    azimut: Optional[str] = None
    signo: Optional[str] = None
    grado: Optional[str] = None
    posicion: Optional[str] = None
    
    # Natal Fields
    casa_natal: Optional[int] = None
    
    # Nested Structures (formerly in metadata)
    house_transits: Optional[List[HouseTransitStrict]] = None
    interpretacion: Optional[str] = None
    
    # Legacy fallbacks (Minimize usage, track for removal)
    visibilidad_local: Optional[str] = None
    
    # Lunar Calendar Specifics
    phase_type: Optional[str] = Field(None, description="Tipo de fase lunar asociada")

class CalculationResponseStrict(BaseModel):
    events: List[AstroEventStrict]
    total_events: int
    calculation_time: float
    year: int
    name: str
    transits_count: int = 0
    progressed_moon_count: int = 0
    profections_count: int = 0
    from_cache: bool = False
