from fastapi import APIRouter
from src.api.schemas import (
    BirthDataRequest, 
    NatalDataRequest, 
    CalculationResponse
)
from src.services.calendar_service import (
    calculate_calendar_dynamic,
    calculate_calendar_legacy
)

router = APIRouter()

@router.post("/calculate-personal-calendar-dynamic", response_model=CalculationResponse)
async def calculate_personal_calendar_dynamic_endpoint(request: BirthDataRequest):
    """
    Calculate personal astrological calendar events using dynamic natal chart calculation.
    This endpoint receives basic birth data and calculates the complete natal chart dynamically.
    """
    return await calculate_calendar_dynamic(request)

@router.post("/calculate-personal-calendar", response_model=CalculationResponse)
async def calculate_personal_calendar_endpoint(request: NatalDataRequest):
    """
    Legacy endpoint: Calculate personal astrological calendar events using pre-calculated natal chart.
    This endpoint receives a complete natal chart and uses it for calculations.
    """
    return await calculate_calendar_legacy(request)
