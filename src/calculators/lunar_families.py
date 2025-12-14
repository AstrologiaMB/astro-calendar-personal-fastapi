from datetime import datetime, timedelta
import ephem
import pytz
import math
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from ..core.constants import EventType, AstronomicalConstants
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import calculate_planet_position
import swisseph as swe

@dataclass
class LunarCycleFamily:
    family_sign: str  # The Zodiac sign common to all Moon positions (e.g., "Virgo")
    seed_event: AstroEvent      # New Moon (Month 0)
    action_event: Optional[AstroEvent]    # First Quarter (Month ~9)
    fruition_event: Optional[AstroEvent]  # Full Moon (Month ~18)
    release_event: Optional[AstroEvent]   # Last Quarter (Month ~27)
    metonic_index: int = 1 # 1-based index (1st, 2nd, 3rd return)

class LunarFamilyCalculator:
    def __init__(self, observer, timezone_str="UTC"):
        self.observer = observer
        self.timezone_str = timezone_str

    def _get_moon_sign(self, dt: datetime) -> str:
        """Calculates the Zodiac sign of the Moon at a specific datetime."""
        jd = julian_day(dt)
        # Calculate Moon position using swisseph for precision
        moon_pos = calculate_planet_position(jd, swe.MOON)
        sign_num = int(moon_pos['longitude'] / 30)
        return AstronomicalConstants.SIGNS[sign_num]

    def _create_event(self, dt: datetime, event_type: str, sign: str) -> AstroEvent:
        """Helper to create a basic AstroEvent object."""
        # Calculate degrees for description
        jd = julian_day(dt)
        moon_pos = calculate_planet_position(jd, swe.MOON)
        degree = moon_pos['longitude'] % 30
        
        if hasattr(event_type, 'value'):
            event_type_str = event_type.value
        else:
            event_type_str = str(event_type)

        return AstroEvent(
            fecha_utc=dt,
            tipo_evento=event_type, # Keep original enum/str for type safety if needed, or convert. Pydantic might handle usage.
            descripcion=f"{event_type_str} en {sign} {AstroEvent.format_degree(degree)}",
            signo=sign,
            grado=degree,
            longitud1=moon_pos['longitude'],
            timezone_str=self.timezone_str
        )

    def find_gestation_cycle(self, seed_event: AstroEvent) -> LunarCycleFamily:
        """
        Given a Seed Event (New Moon), finds the future related phases 
        that belong to the same 'Lunar Gestation Family' (Dietrech Pessin model).
        The key is that the MOON stays in the SAME SIGN (or close to it) 
        during the FQ (+9mo), FM (+18mo), and LQ (+27mo).
        """
        if seed_event.tipo_evento != EventType.LUNA_NUEVA:
            raise ValueError("Seed event must be a New Moon")

        seed_date = seed_event.fecha_utc
        family_sign = seed_event.signo
        
        # 1. Search for Action Phase (First Quarter) ~9 months later
        # Search window: 270 days +/- 45 days
        action_event = self._find_phase_match(
            start_date=seed_date + timedelta(days=240), 
            phase_func=ephem.next_first_quarter_moon, 
            target_sign=family_sign,
            event_type=EventType.CUARTO_CRECIENTE
        )

        # 2. Search for Fruition Phase (Full Moon) ~18 months later
        # Search window: 540 days +/- 45 days
        fruition_event = self._find_phase_match(
            start_date=seed_date + timedelta(days=500),
            phase_func=ephem.next_full_moon,
            target_sign=family_sign,
            event_type=EventType.LUNA_LLENA
        )

        # 3. Search for Release Phase (Last Quarter) ~27 months later
        # Search window: 810 days +/- 45 days
        release_event = self._find_phase_match(
            start_date=seed_date + timedelta(days=780),
            phase_func=ephem.next_last_quarter_moon,
            target_sign=family_sign,
            event_type=EventType.CUARTO_MENGUANTE
        )

        return LunarCycleFamily(
            family_sign=family_sign,
            seed_event=seed_event,
            action_event=action_event,
            fruition_event=fruition_event,
            release_event=release_event
        )

    def _find_phase_match(self, start_date: datetime, phase_func, target_sign: str, event_type: str) -> Optional[AstroEvent]:
        """
        Searches forward from start_date using the ephem phase function 
        to find the first occurrence where the Moon is in the target_sign.
        Limit search to ~3 months to avoid infinite loops if no match.
        """
        current_date_ephem = ephem.Date(start_date)
        # Search limit: 4 months (approx 4 cycles) should be enough to find the sign match
        limit_date = ephem.Date(start_date + timedelta(days=120))
        
        while current_date_ephem < limit_date:
            next_phase_ephem = phase_func(current_date_ephem)
            if next_phase_ephem >= limit_date:
                break
                
            # Convert to UTC datetime
            dt = ephem.Date(next_phase_ephem).datetime()
            dt = pytz.utc.localize(dt)
            
            # Check Moon Sign
            sign = self._get_moon_sign(dt)
            
            if sign == target_sign:
                return self._create_event(dt, event_type, sign)
            
            # Move to next day to find next phase (phases are ~29 days apart, +1 is safe)
            current_date_ephem = next_phase_ephem + 1
            
        return None

    def trace_active_cycles(self, target_date: datetime) -> List[LunarCycleFamily]:
        """
        Identify which Gestation Cycles are 'active' for a specific target_date.
        Checks if the target_date corresponds to a keyframe (FQ, FM, LQ) 
        and traces back to the Seed New Moon.
        """
        active_families = []
        
        # Check current phase status around target_date
        # We need to know if target_date IS a phase event. 
        # For simplicity, we search slightly back and forth or rely on specific input.
        # But usually this is called when we HAVE a calculated event for today.
        # Let's assume we want to "scan" back 9, 18, 27 months from today.
        
        # Better approach: Check if today is a Phase. 
        # If today is FQ in Virgo -> Search for NM in Virgo ~9 months ago.
        # If today is FM in Virgo -> Search for NM in Virgo ~18 months ago.
        # If today is LQ in Virgo -> Search for NM in Virgo ~27 months ago.
        
        today_event = self._detect_phase_event(target_date)
        if not today_event:
            return []
            
        moon_sign = today_event.signo
        
        seed_search_days = 0
        if today_event.tipo_evento == EventType.CUARTO_CRECIENTE:
            seed_search_days = 270 # 9 months
        elif today_event.tipo_evento == EventType.LUNA_LLENA:
            seed_search_days = 540 # 18 months
        elif today_event.tipo_evento == EventType.CUARTO_MENGUANTE:
            seed_search_days = 810 # 27 months
        else:
            return [] # New Moon is the seed itself, handled separately or is just the start.

        # Calculate approximate seed date
        approx_seed_date = target_date - timedelta(days=seed_search_days)
        
        # Search for the specific New Moon in the same sign
        # Window: +/- 45 days around approx date
        search_start = approx_seed_date - timedelta(days=45)
        
        seed_event = self._find_phase_match(
            start_date=search_start,
            phase_func=ephem.next_new_moon,
            target_sign=moon_sign, # Must match today's sign
            event_type=EventType.LUNA_NUEVA
        )
        
        if seed_event:
            # We found the parent! Now reconstruct the full family forward from that seed
            return [self.find_gestation_cycle(seed_event)]
            
        return []

    def _detect_phase_event(self, target_date: datetime) -> Optional[AstroEvent]:
        """
        Checks if the target_date is close (within 24h) to an exact phase.
        Returns the event if found.
        """
        # Search phases around target date +/- 1 day
        start_check = target_date - timedelta(days=1)
        
        # Check all 4 types
        funcs = [
            (ephem.next_new_moon, EventType.LUNA_NUEVA),
            (ephem.next_first_quarter_moon, EventType.CUARTO_CRECIENTE),
            (ephem.next_full_moon, EventType.LUNA_LLENA),
            (ephem.next_last_quarter_moon, EventType.CUARTO_MENGUANTE)
        ]
        
        for func, type_name in funcs:
            phase_ephem = func(ephem.Date(start_check))
            phase_dt = ephem.Date(phase_ephem).datetime()
            phase_dt = pytz.utc.localize(phase_dt)
            
            # If match is within same day (simple check)
            if phase_dt.date() == target_date.date():
                sign = self._get_moon_sign(phase_dt)
                return self._create_event(phase_dt, type_name, sign)
                
        return None

    @staticmethod
    def get_metonic_index(birth_date: datetime, current_date: datetime) -> int:
        """
        Calculates the Metonic Cycle index (1-based).
        Every 19 years, the cycle repeats. 
        Index 1 = 0-19, Index 2 = 19-38, etc.
        """
        # Calculate precise age in years
        # (current - birth).days / 365.2425 is decent, or relativedelta
        # Let's use simple timedelta for robustness without extra deps if possible, 
        # but exact years is safer with full dates.
        
        # Normalize timezones to avoid "can't subtract offset-naive and offset-aware"
        if birth_date.tzinfo is None and current_date.tzinfo is not None:
            # Assume birth_date is UTC if naive, or just strip current
            birth_date = pytz.utc.localize(birth_date)
        elif birth_date.tzinfo is not None and current_date.tzinfo is None:
            current_date = pytz.utc.localize(current_date)
            
        diff = current_date - birth_date
        age_years = diff.days / 365.2425
        
        if age_years < 0:
             return 1 # Fallback
             
        # 19 year cycle
        return int(age_years // 19) + 1
