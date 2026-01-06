"""
POC: Vectorized Transits Calculator (Paranoid Mode)
Standalone implementation that does NOT touch existing code.
Uses Numpy for Zero-Crossing detection to achieve >100x speedup.
"""
import swisseph as swe
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any

# Import only necessary core components (Interface Compliance)
from src.core.base_event import AstroEvent
from src.core.constants import EventType
# from immanuel.const import chart, calc <-- REMOVED to avoid side effects

# Hardcoded constants from immanuel/swisseph for isolation
SUN=0; MOON=1; MERCURY=2; VENUS=3; MARS=4;
JUPITER=5; SATURN=6; URANUS=7; NEPTUNE=8; PLUTO=9

# Settings for POC
POC_ASPECTS = {
    "Conjunción": 0,
    "Oposición": 180,
    "Cuadratura": 90,
    "Sextil": 60,
    "Trígono": 120
}
POC_PLANETS = [
    SUN, MOON, MERCURY, VENUS, MARS,
    JUPITER, SATURN, URANUS, NEPTUNE, PLUTO
]
PLANET_NAMES = {
    SUN: "Sol", MOON: "Luna", MERCURY: "Mercurio",
    VENUS: "Venus", MARS: "Marte", JUPITER: "Júpiter",
    SATURN: "Saturno", URANUS: "Urano", NEPTUNE: "Neptuno",
    PLUTO: "Plutón"
}
chart = type('chart', (), {}) # Dummy for compatibility with logic below if needed
chart.SUN=SUN; chart.MOON=MOON; chart.MERCURY=MERCURY; chart.VENUS=VENUS;
chart.MARS=MARS; chart.JUPITER=JUPITER; chart.SATURN=SATURN;
chart.URANUS=URANUS; chart.NEPTUNE=NEPTUNE; chart.PLUTO=PLUTO

class PocVectorizedTransitsCalculator:
    def __init__(self, natal_data: dict):
        self.natal_data = natal_data
        self.natal_positions = {}
        for pname, data in natal_data['points'].items():
            pid = getattr(chart, pname.upper(), None)
            if pid is not None:
                self.natal_positions[pid] = data['longitude']
    
    def calculate_all(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        # 1. Ephemeris Pre-calculation (The "Heavy Lift")
        # Generate daily JD points for the whole year
        total_days = (end_date - start_date).days + 2
        dates = [start_date + timedelta(days=i) for i in range(total_days)]
        jds = np.array([swe.julday(d.year, d.month, d.day, d.hour + d.minute/60.0) for d in dates])
        
        # Calculate positions for all planets for all days at once
        # Shape: (NumPlanets, NumDays)
        curr_positions = np.zeros((len(POC_PLANETS), len(jds)))
        
        for i, pid in enumerate(POC_PLANETS):
            for j, jd in enumerate(jds):
                # FORCE PATH CLEAR - Nuclear option
                swe.set_ephe_path(None)
                
                # Use standard calc_ut 
                try:
                     res = swe.calc_ut(jd, pid)
                     curr_positions[i, j] = res[0][0]
                except swe.Error:
                     # If default fails, fallback to Moshier
                     res = swe.calc_ut(jd, pid, swe.FLG_MOSEPH)
                     curr_positions[i, j] = res[0][0]

        events = []
        
        # 2. Vectorized Search
        for i, transit_pid in enumerate(POC_PLANETS):
            transit_lons = curr_positions[i]
            
            for natal_pid, natal_lon in self.natal_positions.items():
                for asp_name, asp_angle in POC_ASPECTS.items():
                    # Calculate difference relative to aspect
                    # We want: abs(Transit - Natal - Aspect) ≈ 0
                    # Handling 360 wrap-around is tricky in vectorization, 
                    # so we look for crossing of (Target)
                    
                    target = (natal_lon + asp_angle) % 360
                    
                    # Normalize diff to [-180, 180] 
                    diffs = (transit_lons - target + 180) % 360 - 180
                    
                    # Manual Zero-Crossing Detection with Wrap-around protection
                    # We look for sign changes where the jump is SMALL (not wrapping 360 deg)
                    
                    # diffs[:-1] * diffs[1:] < 0  checks for sign change
                    # abs(diffs[:-1] - diffs[1:]) < 180 checks that we didn't jump across the cut
                    
                    candidates = (diffs[:-1] * diffs[1:] <= 0) & (np.abs(diffs[:-1] - diffs[1:]) < 180)
                    
                    # DEBUG PRINT FOR SUN
                    if i == 0 and natal_pid == chart.SUN and asp_name == "Conjunción":
                       print(f"DEBUG SUN CONJUNCTION SUN:")
                       print(f"Natal: {natal_lon}, Target: {target}")
                       print(f"Transit Lon [0]: {transit_lons[0]}")
                       print(f"Diff [0]: {diffs[0]}")
                       print(f"Candidates found: {np.sum(candidates)}")
                    
                    day_indices = np.where(candidates)[0]
                    
                    for day_idx in day_indices:
                        # 3. Refinement (Root Finding)
                        # We know event is between day_idx and day_idx+1
                        t0 = jds[day_idx]
                        t1 = jds[day_idx+1]
                        
                        exact_time = self._find_precise_time(transit_pid, target, t0, t1)
                        if exact_time:
                            # Create Event
                            dt = self._jd_to_datetime(exact_time)
                            
                            # Filter out of range
                            if not (start_date <= dt <= end_date):
                                continue
                                
                            # Re-verify logic (sanity check)
                            final_pos = swe.calc_ut(exact_time, transit_pid)[0][0]
                            final_orb = abs(self._normalize_diff(final_pos, target))
                            
                            if final_orb > 0.1: # False positive check
                                continue
                                
                            events.append(AstroEvent(
                                fecha_utc=dt,
                                tipo_evento=EventType.ASPECTO,
                                descripcion=f"{PLANET_NAMES[transit_pid]} {asp_name} {PLANET_NAMES[natal_pid]} Natal",
                                planeta1=PLANET_NAMES[transit_pid],
                                planeta2=PLANET_NAMES[natal_pid],
                                longitud1=final_pos,
                                longitud2=natal_lon,
                                tipo_aspecto=asp_name,
                                orbe=final_orb,
                                es_aplicativo=False, # Would need derivative check
                                metadata={"method": "vectorized_poc"}
                            ))
                            
        return sorted(events, key=lambda x: x.fecha_utc)

    def _find_precise_time(self, pid, target_lon, jd_start, jd_end, steps=10):
        # fast binary search / bisection
        low = jd_start
        high = jd_end
        
        for _ in range(steps):
            mid = (low + high) / 2
            try:
                pos = swe.calc_ut(mid, pid)[0][0]
            except swe.Error:
                pos = swe.calc_ut(mid, pid, swe.FLG_MOSEPH)[0][0]
            diff = self._normalize_diff(pos, target_lon)
            
            if abs(diff) < 0.0001: # 0.0001 degree ~ seconds precision
                return mid
            
            # Check signs to decide direction
            try:
                pos_low = swe.calc_ut(low, pid)[0][0]
            except swe.Error:
                pos_low = swe.calc_ut(low, pid, swe.FLG_MOSEPH)[0][0]
            diff_low = self._normalize_diff(pos_low, target_lon)
            
            if diff * diff_low < 0:
                high = mid
            else:
                low = mid
                
        return (low + high) / 2



    def _normalize_diff(self, a, b):
        d = (a - b + 180) % 360 - 180
        return d
    
    def _jd_to_datetime(self, jd):
        y, m, d, h = swe.revjul(jd)
        # Handle fractional hours
        hour = int(h)
        mins = int((h - hour) * 60)
        secs = int(((h - hour) * 60 - mins) * 60)
        return datetime(y, m, d, hour, mins, secs, tzinfo=ZoneInfo("UTC"))
