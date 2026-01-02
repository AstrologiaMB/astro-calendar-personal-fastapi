import time
import traceback
import ephem
import httpx
import pytz
from datetime import datetime
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
from fastapi import HTTPException

# Import internal modules (paths remain relative to root as python path includes root)
from src.core.location import Location
from src.calculators.natal_chart import calcular_carta_natal
from src.calculators.transits_calculator_factory import TransitsCalculatorFactory
from src.calculators.profections_calculator import ProfectionsCalculator
from src.calculators.lunar_phases import LunarPhaseCalculator
from src.calculators.eclipses import EclipseCalculator
from src.core.base_event import AstroEvent
from src.core.constants import EventType

from src.api.schemas import (
    BirthDataRequest, 
    NatalDataRequest, 
    CalculationResponse, 
    AstroEventResponse,
    LocationData
)

# --- Helper Functions ---

def _convertir_a_grados_absolutos(signo: str, grado: float, desde_ingles: bool = True) -> float:
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

def _parsear_posicion(posicion: str) -> float:
    """
    Convierte una posición en formato '27°45\'16"' a grados decimales.
    """
    partes = posicion.replace('°', ' ').replace('\'', ' ').replace('"', ' ').split()
    grados = float(partes[0])
    minutos = float(partes[1]) if len(partes) > 1 else 0
    segundos = float(partes[2]) if len(partes) > 2 else 0
    return grados + minutos/60 + segundos/3600

def _calcular_orbe(pos1: float, pos2: float) -> float:
    """
    Calcula el orbe más corto entre dos posiciones zodiacales.
    """
    diff = abs(pos1 - pos2)
    if diff > 180:
        diff = 360 - diff
    return diff

def _add_moon_phase_and_eclipse_aspects(lunar_events: List[AstroEvent], eclipse_events: List[AstroEvent], 
                                       natal_data: dict, timezone_str: str) -> List[AstroEvent]:
    """
    Agrega eventos de aspectos para fases lunares y eclipses con planetas natales y ángulos.
    Detecta conjunciones con orbe estricto de 4 grados.
    """
    aspect_events = []
    
    # Mapeo de nombres de planetas y ángulos
    PLANET_NAMES = {
        'Sun': 'Sol', 'Moon': 'Luna', 'Mercury': 'Mercurio',
        'Venus': 'Venus', 'Mars': 'Marte', 'Jupiter': 'Júpiter',
        'Saturn': 'Saturno', 'Uranus': 'Urano',
        'Neptune': 'Neptuno', 'Pluto': 'Plutón',
        'Asc': 'Ascendente', 'MC': 'Medio Cielo',
        'Dsc': 'Descendente', 'Ic': 'Fondo del Cielo'
    }
    
    # Crear un set de fechas de eclipses para evitar duplicaciones
    eclipse_dates = set()
    for eclipse_event in eclipse_events:
        # Usar fecha y hora para identificar eclipses únicos
        eclipse_key = (eclipse_event.fecha_utc.date(), eclipse_event.fecha_utc.hour, eclipse_event.fecha_utc.minute)
        eclipse_dates.add(eclipse_key)
    
    # Procesar eventos de fases lunares (solo si no hay eclipse en esa fecha/hora)
    for event in lunar_events:
        if event.tipo_evento in [EventType.LUNA_NUEVA, EventType.LUNA_LLENA, 
                               EventType.CUARTO_CRECIENTE, EventType.CUARTO_MENGUANTE]:
            # Verificar si hay un eclipse en la misma fecha/hora
            event_key = (event.fecha_utc.date(), event.fecha_utc.hour, event.fecha_utc.minute)
            if event_key in eclipse_dates:
                # Si hay eclipse, saltamos la fase lunar para evitar duplicación
                continue
                
            pos = event.longitud1
            planeta1 = "Luna"
            
            if event.tipo_evento == EventType.LUNA_NUEVA:
                # Luna nueva: Sol y Luna conjuncion. Usamos la posición tal cual.
                planeta1 = "Sol" 
            elif event.tipo_evento == EventType.LUNA_LLENA:
                # Luna llena: Luna opuesta al Sol. Usamos la posición de la Luna.
                planeta1 = "Luna"
            
            # Nombre para mostrar del tipo de fase
            tipo_display = {
                EventType.LUNA_NUEVA: "Luna nueva",
                EventType.LUNA_LLENA: "Luna llena",
                EventType.CUARTO_CRECIENTE: "Cuarto Creciente",
                EventType.CUARTO_MENGUANTE: "Cuarto Menguante"
            }.get(event.tipo_evento, event.tipo_evento.value)

            # Buscar conjunciones con planetas y ángulos
            points_to_check = {**natal_data.get('points', {}), **natal_data.get('angles', {})} # Unir puntos y ángulos si están separados, o usar points si incluye todo
            
            # Nota: natal_data['points'] ya suele incluir Asc/MC/etc si viene de natal_chart.py
            # Iteramos sobre todos los puntos disponibles
            for point_name, data in points_to_check.items():
                if point_name in PLANET_NAMES:
                    planet_pos = _convertir_a_grados_absolutos(
                        data['sign'],
                        _parsear_posicion(data['position'])
                    )
                    orb = _calcular_orbe(pos, planet_pos)
                    
                    if orb <= 4.0:  # Orbe estricto de 4°
                        grado = event.grado
                        conj_event = AstroEvent(
                            fecha_utc=event.fecha_utc,
                            tipo_evento=EventType.ASPECTO,
                            descripcion=f"{tipo_display} en {event.signo} {AstroEvent.format_degree(grado)} en conjunción con {PLANET_NAMES[point_name]} natal",
                            planeta1=planeta1,
                            planeta2=PLANET_NAMES[point_name],
                            longitud1=pos,
                            longitud2=planet_pos,
                            tipo_aspecto="Conjunción",
                            orbe=orb,
                            timezone_str=timezone_str,
                            metadata={
                                "posicion1": f"{event.signo} {AstroEvent.format_degree(grado)}",
                                "posicion2": data['position'], 
                                "phase_type": event.tipo_evento.value
                            }
                        )
                        aspect_events.append(conj_event)
    
    # Procesar eventos de eclipses
    for event in eclipse_events:
        if event.tipo_evento in [EventType.ECLIPSE_SOLAR, EventType.ECLIPSE_LUNAR]:
            pos = event.longitud1
            planeta1 = "Luna"
            
            if event.tipo_evento == EventType.ECLIPSE_SOLAR:
                # Eclipse solar: Sol conjunción Luna. Usamos la posición directa.
                planeta1 = "Sol" 
            
            tipo_display = "Eclipse lunar" if event.tipo_evento == EventType.ECLIPSE_LUNAR else "Eclipse solar"
            
            # Buscar conjunciones
            points_to_check = {**natal_data.get('points', {}), **natal_data.get('angles', {})}

            for point_name, data in points_to_check.items():
                if point_name in PLANET_NAMES:
                    planet_pos = _convertir_a_grados_absolutos(
                        data['sign'],
                        _parsear_posicion(data['position'])
                    )
                    orb = _calcular_orbe(pos, planet_pos)
                    
                    if orb <= 4.0:  # Orbe de 4°
                        grado = event.grado
                        # Agregar insignia de FUEGO si es eclipse
                        desc_prefix = f"🔥 {tipo_display}" 
                        conj_event = AstroEvent(
                            fecha_utc=event.fecha_utc,
                            tipo_evento=EventType.ASPECTO,
                            descripcion=f"{desc_prefix} en {event.signo} {AstroEvent.format_degree(grado)} en conjunción con {PLANET_NAMES[point_name]} natal",
                            planeta1=planeta1,
                            planeta2=PLANET_NAMES[point_name],
                            longitud1=pos,
                            longitud2=planet_pos,
                            tipo_aspecto="Conjunción",
                            orbe=orb,
                            timezone_str=timezone_str,
                            metadata={
                                "posicion1": f"{event.signo} {AstroEvent.format_degree(grado)}",
                                "posicion2": data['position'],
                                "phase_type": event.tipo_evento.value,
                                "is_eclipse": True
                            }
                        )
                        aspect_events.append(conj_event)
    
    return aspect_events

def convert_astro_event_to_response(event: AstroEvent) -> AstroEventResponse:
    """Convert AstroEvent object to API response format."""
    # Format the date and time
    fecha_utc = event.fecha_utc.strftime("%Y-%m-%d")
    hora_utc = event.fecha_utc.strftime("%H:%M")
    
    # Format orbe if present
    orbe_str = None
    if hasattr(event, 'orbe') and event.orbe is not None:
        if event.orbe < 0.01:
            orbe_str = "0°00'00\""
        else:
            degrees = int(event.orbe)
            minutes = int((event.orbe - degrees) * 60)
            seconds = int(((event.orbe - degrees) * 60 - minutes) * 60)
            orbe_str = f"{degrees}°{minutes:02d}'{seconds:02d}\""
    
    # Determine harmony based on aspect type
    harmony = None
    if hasattr(event, 'tipo_aspecto') and event.tipo_aspecto:
        if event.tipo_aspecto in ['Conjunción', 'Sextil', 'Trígono']:
            harmony = 'Armónico' if event.tipo_aspecto != 'Conjunción' else 'Neutro'
        elif event.tipo_aspecto in ['Cuadratura', 'Oposición']:
            harmony = 'Tensión'
    
    # Format positions if available
    posicion1 = None
    posicion2 = None
    if hasattr(event, 'metadata') and event.metadata:
        posicion1 = event.metadata.get('posicion1')
        posicion2 = event.metadata.get('posicion2')
    
    # Handle special case for house transits state
    descripcion = event.descripcion
    house_transits_data = None
    if hasattr(event, 'tipo_evento') and event.tipo_evento == EventType.TRANSITO_CASA_ESTADO:
        # For house transits, send structured data instead of text parsing
        if hasattr(event, 'metadata') and event.metadata and 'house_transits' in event.metadata:
            house_transits_data = event.metadata['house_transits']
            descripcion = "Estado actual de tránsitos de largo plazo"
    
    return AstroEventResponse(
        fecha_utc=fecha_utc,
        hora_utc=hora_utc,
        tipo_evento=event.tipo_evento.value if hasattr(event.tipo_evento, 'value') else str(event.tipo_evento),
        descripcion=descripcion,
        planeta1=getattr(event, 'planeta1', None),
        planeta2=getattr(event, 'planeta2', None),
        posicion1=posicion1,
        posicion2=posicion2,
        tipo_aspecto=getattr(event, 'tipo_aspecto', None),
        orbe=orbe_str,
        es_aplicativo="Sí" if getattr(event, 'es_aplicativo', False) else "No",
        harmony=harmony,
        elevacion=str(getattr(event, 'elevacion', "") or ""),
        azimut=str(getattr(event, 'azimut', "") or ""),
        signo=getattr(event, 'signo', None),
        grado=str(getattr(event, 'grado', "") or ""),
        posicion=getattr(event, 'posicion', None),
        casa_natal=getattr(event, 'casa_natal', None),
        house_transits=house_transits_data,
        metadata=getattr(event, 'metadata', None)
    )

def convert_natal_data_format(request: NatalDataRequest) -> dict:
    """Convert the request format to the internal natal data format."""
    natal_data = {
        'name': request.name,
        'location': {
            'latitude': request.location.latitude,
            'longitude': request.location.longitude,
            'name': request.location.name,
            'timezone': request.location.timezone
        },
        'hora_local': request.hora_local,
        'points': {},
        'houses': {}
    }
    
    # Convert points
    for planet_name, point_data in request.points.items():
        natal_data['points'][planet_name] = {
            'sign': point_data.sign,
            'position': point_data.position,
            'longitude': point_data.longitude,
            'latitude': point_data.latitude,
            'distance': point_data.distance,
            'speed': point_data.speed,
            'retrograde': point_data.retrograde
        }
    
    # Convert houses
    for house_num, house_data in request.houses.items():
        natal_data['houses'][house_num] = {
            'sign': house_data.sign,
            'position': house_data.position,
            'longitude': house_data.longitude
        }
    
    return natal_data

# --- Service Functions ---

async def calculate_calendar_dynamic(request: BirthDataRequest) -> CalculationResponse:
    start_time = time.time()
    
    try:
        print(f"Calculating personal calendar for {request.name} using dynamic natal chart calculation...")
        
        # Create location object
        location = Location(
            lat=request.location.latitude,
            lon=request.location.longitude,
            name=request.location.name,
            timezone=request.location.timezone,
            elevation=25
        )
        
        # Validate timezone
        try:
            _ = ZoneInfo(location.timezone)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid timezone '{location.timezone}': {str(e)}"
            )
        
        # Prepare birth data for natal chart calculation (same format as main.py)
        birth_data = {
            "hora_local": f"{request.birth_date}T{request.birth_time}:00",
            "lat": request.location.latitude,
            "lon": request.location.longitude,
            "zona_horaria": request.location.timezone,
            "lugar": request.location.name
        }
        
        # Calculate complete natal chart dynamically (same as script original)
        print("Calculating complete natal chart with calcular_carta_natal()...")
        natal_data = calcular_carta_natal(birth_data)
        natal_data['name'] = request.name
        
        print(f"Natal chart calculated successfully with {len(natal_data['points'])} points")
        print(f"Critical points included: Asc={('Asc' in natal_data['points'])}, MC={('MC' in natal_data['points'])}")
        
        # Set up date range for the year
        start_date = datetime(request.year, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(request.year + 1, 1, 1, tzinfo=pytz.UTC)
        
        all_events = []
        
        # Calculate transits using V4 calculator
        print(f"Calculating transits for {request.name} using V4 calculator...")
        transits_calculator = TransitsCalculatorFactory.create_calculator(
            natal_data,
            calculator_type="astronomical_v4",
            use_parallel=False,
            timezone_str=location.timezone
        )
        transit_events = transits_calculator.calculate_all(start_date, end_date)
        all_events.extend(transit_events)
        print(f"Calculated {len(transit_events)} transit events")
        
        # Debug: Check for house transit events
        house_events = [e for e in transit_events if hasattr(e, 'tipo_evento') and e.tipo_evento == EventType.TRANSITO_CASA_ESTADO]
        print(f"DEBUG: Found {len(house_events)} house transit events in V4 calculator")
        if house_events:
            for he in house_events:
                print(f"DEBUG: House event - {he.tipo_evento} - {he.descripcion}")
        
        # Calculate progressed moon
        print("Calculating progressed moon conjunctions...")
        progressed_calculator = TransitsCalculatorFactory.create_calculator(
            natal_data,
            calculator_type="progressed_moon"
        )
        progressed_events = progressed_calculator.calculate_all(start_date, end_date)
        all_events.extend(progressed_events)
        print(f"Calculated {len(progressed_events)} progressed moon events")
        
        # Calculate profections
        print("Calculating annual profections...")
        profections_calculator = ProfectionsCalculator(natal_data)
        profection_events = profections_calculator.calculate_profection_events(start_date, end_date)
        all_events.extend(profection_events)
        print(f"Calculated {len(profection_events)} profection events")
        
        # Calculate lunar phases (new moon, full moon)
        print("Calculating lunar phases...")
        observer = ephem.Observer()
        observer.lat = str(location.lat)
        observer.lon = str(location.lon)
        observer.elevation = location.elevation
        
        lunar_calculator = LunarPhaseCalculator(observer, location.timezone, natal_data.get('houses'))
        lunar_events = lunar_calculator.calculate_phases(start_date, end_date)
        all_events.extend(lunar_events)
        print(f"Calculated {len(lunar_events)} lunar phase events")
        
        # Calculate eclipses (solar and lunar)
        print("Calculating eclipses...")
        eclipse_calculator = EclipseCalculator(observer, location.timezone, natal_data.get('houses'))
        eclipse_events = eclipse_calculator.calculate_eclipses(start_date, end_date)
        all_events.extend(eclipse_events)
        print(f"Calculated {len(eclipse_events)} eclipse events")
        
        # Add moon phase and eclipse aspect events (replicating original algorithm)
        print("Adding moon phase and eclipse aspect events...")
        aspect_events = _add_moon_phase_and_eclipse_aspects(
            lunar_events, eclipse_events, natal_data, location.timezone
        )
        all_events.extend(aspect_events)
        print(f"Added {len(aspect_events)} aspect events")
        
        # Sort events by date
        all_events.sort(key=lambda x: x.fecha_utc)
        
        # Convert to response format
        response_events = [convert_astro_event_to_response(event) for event in all_events]

        # --- INICIO: Fase 3 - Llamada al servicio de Interpretaciones ---
        print("📞 Llamando al servicio de interpretaciones para enriquecer eventos...")
        try:
                response = await client.post(
                    "http://127.0.0.1:8002/interpretar-eventos",
                    json={
                        "eventos": [
                            {
                                "fecha_utc": evento.fecha_utc,
                                "hora_utc": evento.hora_utc,
                                "tipo_evento": evento.tipo_evento,
                                "descripcion": evento.descripcion,
                                "planeta1": evento.planeta1,
                                "planeta2": evento.planeta2,
                                "tipo_aspecto": evento.tipo_aspecto,
                                "signo": evento.signo,
                                "grado": evento.grado,
                                "casa_natal": evento.casa_natal,
                                "posicion1": evento.posicion1,
                                "posicion2": evento.posicion2,
                                "orbe": evento.orbe
                            }
                            for evento in response_events
                        ]
                    },
                    timeout=60.0 # Timeout de 60 segundos
                )
                response.raise_for_status() # Lanza una excepción si el status no es 2xx
                
                # Procesar la respuesta
                datos_interpretados = response.json()
                mapa_interpretaciones = {
                    item['descripcion']: item['interpretacion'] 
                    for item in datos_interpretados.get('eventos_interpretados', [])
                }
                
                # Enriquecer los eventos originales con las interpretaciones
                for evento in response_events:
                    if evento.descripcion in mapa_interpretaciones:
                        evento.interpretacion = mapa_interpretaciones[evento.descripcion]
                
                print("✅ Eventos enriquecidos con interpretaciones.")

        except httpx.RequestError as e:
            print(f"⚠️ Error de red al llamar al servicio de interpretaciones: {e}. Devolviendo eventos sin interpretar.")
        except Exception as e:
            print(f"⚠️ Error inesperado durante la fase de interpretación: {e}. Devolviendo eventos sin interpretar.")
        # --- FIN: Fase 3 ---

        calculation_time = time.time() - start_time
        
        return CalculationResponse(
            events=response_events,
            total_events=len(response_events),
            calculation_time=calculation_time,
            year=request.year,
            name=request.name
        )
        
    except Exception as e:
        print(f"Error calculating personal calendar: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating personal calendar: {str(e)}"
        )

async def calculate_calendar_legacy(request: NatalDataRequest) -> CalculationResponse:
    start_time = time.time()
    
    try:
        # Convert request format to internal format
        natal_data = convert_natal_data_format(request)
        
        # Create location object
        location = Location(
            lat=request.location.latitude,
            lon=request.location.longitude,
            name=request.location.name,
            timezone=request.location.timezone,
            elevation=25
        )
        
        # Validate timezone
        try:
            _ = ZoneInfo(location.timezone)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid timezone '{location.timezone}': {str(e)}"
            )
        
        # Set up date range for the year
        start_date = datetime(request.year, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(request.year + 1, 1, 1, tzinfo=pytz.UTC)
        
        all_events = []
        
        # Calculate transits using V4 calculator
        print(f"Calculating transits for {request.name} using V4 calculator...")
        transits_calculator = TransitsCalculatorFactory.create_calculator(
            natal_data,
            calculator_type="astronomical_v4",
            use_parallel=False,
            timezone_str=location.timezone
        )
        transit_events = transits_calculator.calculate_all(start_date, end_date)
        all_events.extend(transit_events)
        print(f"Calculated {len(transit_events)} transit events")
        
        # Debug: Check for house transit events
        house_events = [e for e in transit_events if hasattr(e, 'tipo_evento') and e.tipo_evento == EventType.TRANSITO_CASA_ESTADO]
        print(f"DEBUG: Found {len(house_events)} house transit events in V4 calculator")
        if house_events:
            for he in house_events:
                print(f"DEBUG: House event - {he.tipo_evento} - {he.descripcion}")
        
        # Calculate progressed moon
        print("Calculating progressed moon conjunctions...")
        progressed_calculator = TransitsCalculatorFactory.create_calculator(
            natal_data,
            calculator_type="progressed_moon"
        )
        progressed_events = progressed_calculator.calculate_all(start_date, end_date)
        all_events.extend(progressed_events)
        print(f"Calculated {len(progressed_events)} progressed moon events")
        
        # Calculate profections
        print("Calculating annual profections...")
        profections_calculator = ProfectionsCalculator(natal_data)
        profection_events = profections_calculator.calculate_profection_events(start_date, end_date)
        all_events.extend(profection_events)
        print(f"Calculated {len(profection_events)} profection events")
        
        # Calculate lunar phases (new moon, full moon)
        print("Calculating lunar phases...")
        observer = ephem.Observer()
        observer.lat = str(location.lat)
        observer.lon = str(location.lon)
        observer.elevation = location.elevation
        
        lunar_calculator = LunarPhaseCalculator(observer, location.timezone, natal_data.get('houses'))
        lunar_events = lunar_calculator.calculate_phases(start_date, end_date)
        all_events.extend(lunar_events)
        print(f"Calculated {len(lunar_events)} lunar phase events")
        
        # Calculate eclipses (solar and lunar)
        print("Calculating eclipses...")
        eclipse_calculator = EclipseCalculator(observer, location.timezone, natal_data.get('houses'))
        eclipse_events = eclipse_calculator.calculate_eclipses(start_date, end_date)
        all_events.extend(eclipse_events)
        print(f"Calculated {len(eclipse_events)} eclipse events")
        
        # Sort events by date
        all_events.sort(key=lambda x: x.fecha_utc)
        
        # Convert to response format
        response_events = [convert_astro_event_to_response(event) for event in all_events]
        
        calculation_time = time.time() - start_time
        
        return CalculationResponse(
            events=response_events,
            total_events=len(response_events),
            calculation_time=calculation_time,
            year=request.year,
            name=request.name
        )
        
    except Exception as e:
        print(f"Error calculating personal calendar: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating personal calendar: {str(e)}"
        )
