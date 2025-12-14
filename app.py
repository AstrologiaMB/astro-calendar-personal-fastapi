"""
FastAPI Microservice for Personal Astrological Calendar
Transforms the interactive astro_calendar_personal_v3 into a REST API service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from src.api.routes.calendar import router as calendar_router
from src.api.routes.cycles import router as cycles_router
from src.api.schemas import HealthResponse, InfoResponse

app = FastAPI(
    title="Personal Astrology Calendar API",
    description="Complete microservice for calculating personal astrological events: transits, lunar phases, eclipses, progressed moon, and profections",
    version="2.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the calendar router
app.include_router(calendar_router)
app.include_router(cycles_router)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0"
    )

@app.get("/info", response_model=InfoResponse)
async def service_info():
    """Service information endpoint."""
    return InfoResponse(
        service="Personal Astrology Calendar API",
        version="2.0.0",
        description="Complete microservice for calculating personal astrological events: transits, lunar phases, eclipses, progressed moon, and profections",
        endpoints=[
            "/calculate-personal-calendar",
            "/health",
            "/info"
        ],
        features=[
            "Astronomical transits (V4 calculator)",
            "Progressed moon conjunctions",
            "Annual profections",
            "Lunar phases (new moon, full moon)",
            "Solar and lunar eclipses",
            "Lunar phases with natal houses",
            "Eclipse events with natal houses",
            "High-precision ephemeris calculations",
            "Spanish language descriptions"
        ]
    )

@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    return {
        "service": "Personal Astrology Calendar API",
        "version": "2.0.0",
        "status": "running",
        "description": "Complete personal astrology calendar with transits, lunar phases, eclipses, and profections",
        "endpoints": {
            "calculate": "/calculate-personal-calendar",
            "health": "/health",
            "info": "/info"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
