from fastapi import APIRouter
from src.api.schemas import (
    BirthDataRequest, 
    NatalDataRequest, 
    CalculationResponse
)
from src.api.schemas_strict import CalculationResponseStrict
from src.services.calendar_service import (
    calculate_calendar_dynamic,
    calculate_calendar_legacy,
    calculate_calendar_dynamic_strict
)

router = APIRouter()

@router.post("/calculate-personal-calendar-dynamic", response_model=CalculationResponseStrict)
async def calculate_personal_calendar_dynamic_endpoint(request: BirthDataRequest):
    """
    Calculate personal astrological calendar events using dynamic natal chart calculation.
    This endpoint receives basic birth data and calculates the complete natal chart dynamically.
    Returns Strict Types (datetime, etc).
    """
    return await calculate_calendar_dynamic_strict(request)

@router.post("/calculate-personal-calendar", response_model=CalculationResponse)
async def calculate_personal_calendar_endpoint(request: NatalDataRequest):
    """
    Legacy endpoint: Calculate personal astrological calendar events using pre-calculated natal chart.
    This endpoint receives a complete natal chart and uses it for calculations.
    """
    return await calculate_calendar_legacy(request)
