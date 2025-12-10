import sys
import os
from datetime import datetime
import pytz

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.base_event import AstroEvent
from src.core.constants import EventType
from src.services.calendar_service import _add_moon_phase_and_eclipse_aspects

def test_lunar_angle_conjunction():
    # 1. Setup Mock Data
    
    # Natal Chart: Ascendant at 0 Aries (0.0), MC at 0 Cancer (90.0)
    natal_data = {
        'points': {},
        'angles': {
            'Asc': {'sign': 'Aries', 'position': "0°00'00\"", 'longitude': 0.0},
            'MC': {'sign': 'Cáncer', 'position': "0°00'00\"", 'longitude': 90.0}
        }
    }
    
    # Events: 
    # - New Moon at 2 Aries (Conj Asc, Orb 2)
    # - First Quarter at 1 Cancer (Conj MC, Orb 1)
    # - Full Moon at 10 Leo (No Conj)
    
    lunar_events = [
        AstroEvent(
            fecha_utc=datetime(2025, 1, 1, 12, 0, tzinfo=pytz.UTC),
            tipo_evento=EventType.LUNA_NUEVA,
            descripcion="Luna Nueva Test",
            longitud1=2.0, # 2 Aries
            signo="Aries",
            grado=2.0
        ),
        AstroEvent(
            fecha_utc=datetime(2025, 1, 8, 12, 0, tzinfo=pytz.UTC),
            tipo_evento=EventType.CUARTO_CRECIENTE,
            descripcion="Cuarto Creciente Test",
            longitud1=91.0, # 1 Cancer (90+1)
            signo="Cáncer",
            grado=1.0
        ),
        AstroEvent(
            fecha_utc=datetime(2025, 1, 15, 12, 0, tzinfo=pytz.UTC),
            tipo_evento=EventType.LUNA_LLENA,
            descripcion="Luna Llena Test",
            longitud1=130.0, # 10 Leo
            signo="Leo",
            grado=10.0
        )
    ]
    
    eclipse_events = [] # No eclipses for this test
    
    # 2. Run Function
    aspect_events = _add_moon_phase_and_eclipse_aspects(
        lunar_events, eclipse_events, natal_data, "UTC"
    )
    
    # 3. Verify Results
    print(f"✅ Found {len(aspect_events)} aspect events")
    
    for evt in aspect_events:
        print(f"  - {evt.descripcion} (Orbe: {evt.orbe:.2f})")
        
    # Assertions
    assert len(aspect_events) == 2, f"Expected 2 events, found {len(aspect_events)}"
    
    # Check New Moon Conj Asc
    evt1 = aspect_events[0]
    assert evt1.tipo_evento == EventType.ASPECTO
    assert "Luna nueva" in evt1.descripcion
    assert "Ascendente" in evt1.descripcion
    assert evt1.orbe == 2.0
    
    # Check Quarter Conj MC
    evt2 = aspect_events[1]
    assert evt2.tipo_evento == EventType.ASPECTO
    assert "Cuarto Creciente" in evt2.descripcion
    assert "Medio Cielo" in evt2.descripcion
    assert evt2.orbe == 1.0

    print("✅ All tests passed!")

if __name__ == "__main__":
    test_lunar_angle_conjunction()
