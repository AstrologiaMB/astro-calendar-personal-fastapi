from datetime import datetime
from typing import List, Optional
import ephem
from ..calculators.lunar_families import LunarFamilyCalculator, LunarCycleFamily
from ..core.location import Location
from ..api.schemas import (
    LocationData, 
    ActiveCyclesResponse, 
    CycleFamilyResponse, 
    CyclePhaseResponse
)
from ..core.base_event import AstroEvent

def _map_event_to_response(event: Optional[AstroEvent]) -> Optional[CyclePhaseResponse]:
    if not event:
        return None
    return CyclePhaseResponse(
        date=event.fecha_utc.isoformat(),
        phase=event.tipo_evento,
        sign=event.signo,
        degree=event.grado,
        description=event.descripcion
    )

def get_active_cycles(target_date: datetime, location_data: LocationData, birth_date: Optional[datetime] = None) -> ActiveCyclesResponse:
    # Initialize Location and Observer
    location = Location(
        lat=location_data.latitude,
        lon=location_data.longitude,
        name=location_data.name,
        timezone=location_data.timezone
    )
    observer = location.create_ephem_observer()
    
    # Initialize Calculator
    calculator = LunarFamilyCalculator(observer, location_data.timezone)
    
    # Trace Cycles
    active_families = calculator.trace_active_cycles(target_date)
    
    response_families = []
    for family in active_families:
        metonic_idx = 1
        if birth_date:
            # Use seed date year vs birth year
            metonic_idx = LunarFamilyCalculator.get_metonic_index(birth_date, family.seed_event.fecha_utc)
            
        response_families.append(CycleFamilyResponse(
            family_sign=family.family_sign,
            metonic_index=metonic_idx,
            seed=_map_event_to_response(family.seed_event),
            action=_map_event_to_response(family.action_event),
            fruition=_map_event_to_response(family.fruition_event),
            release=_map_event_to_response(family.release_event)
        ))
        
    return ActiveCyclesResponse(
        date=target_date.isoformat(),
        active_cycles=response_families
    )
