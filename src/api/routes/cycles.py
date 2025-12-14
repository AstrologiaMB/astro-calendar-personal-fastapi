from fastapi import APIRouter, HTTPException
from datetime import datetime
from src.api.schemas import (
    CycleAnalysisRequest, 
    ActiveCyclesResponse
)
from src.services.cycles_service import get_active_cycles

router = APIRouter()

@router.post("/calculate-cycles", response_model=ActiveCyclesResponse)
async def calculate_cycles_endpoint(request: CycleAnalysisRequest):
    """
    Identify active Lunar Gestation Cycles (Families) for a specific date.
    Traces back from the target date (if it's a key phase) to the Seed New Moon,
    and returns the full 27-month cycle timeline.
    Also calculates Metonic Index based on birth date.
    """
    try:
        target_dt = datetime.fromisoformat(request.target_date)
        birth_dt = datetime.fromisoformat(request.birth_date)
        
        # Calculate
        return get_active_cycles(
            target_date=target_dt,
            location_data=request.location,
            birth_date=birth_dt
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
