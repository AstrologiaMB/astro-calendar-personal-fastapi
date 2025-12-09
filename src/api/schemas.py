from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Pydantic models for request/response
class LocationData(BaseModel):
    latitude: float
    longitude: float
    name: str
    timezone: str

class BirthDataRequest(BaseModel):
    """Request model for basic birth data that will be used to calculate natal chart dynamically."""
    name: str
    birth_date: str = Field(description="Birth date in YYYY-MM-DD format")
    birth_time: str = Field(description="Birth time in HH:MM format")
    location: LocationData
    year: int = Field(default=2025, description="Year for which to calculate events")

# Legacy models for backward compatibility (if needed)
class PointData(BaseModel):
    sign: str
    position: str
    longitude: float
    latitude: Optional[float] = 0
    distance: Optional[float] = 0
    speed: Optional[float] = 0
    retrograde: Optional[bool] = False

class HouseData(BaseModel):
    sign: str
    position: str
    longitude: float

class NatalDataRequest(BaseModel):
    points: Dict[str, PointData]
    houses: Dict[str, HouseData]
    location: LocationData
    hora_local: str
    name: str
    year: int = Field(default=2025, description="Year for which to calculate events")

class AstroEventResponse(BaseModel):
    fecha_utc: str
    hora_utc: str
    tipo_evento: str
    descripcion: str
    planeta1: Optional[str] = None
    planeta2: Optional[str] = None
    posicion1: Optional[str] = None
    posicion2: Optional[str] = None
    tipo_aspecto: Optional[str] = None
    orbe: Optional[str] = None
    es_aplicativo: Optional[str] = None
    harmony: Optional[str] = None
    elevacion: Optional[str] = ""
    azimut: Optional[str] = ""
    signo: Optional[str] = None
    grado: Optional[str] = None
    posicion: Optional[str] = None
    casa_natal: Optional[int] = None
    house_transits: Optional[List[Dict[str, Any]]] = None
    interpretacion: Optional[str] = None # Nuevo campo para la interpretación

class CalculationResponse(BaseModel):
    events: List[AstroEventResponse]
    total_events: int
    calculation_time: float
    year: int
    name: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class InfoResponse(BaseModel):
    service: str
    version: str
    description: str
    endpoints: List[str]
    features: List[str]
