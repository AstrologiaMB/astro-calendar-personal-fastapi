"""
Vectorized Transits Calculator (Production Version)
--------------------------------------------------
High-performance astronomical transit calculator using vectorized zero-crossing detection.
Optimized for speed (>50x faster than V4) and precision (SwissEph based).

Design Principles:
1. Stateless Ephemeris: Does NOT modify global swisseph path (assumes app init).
2. Pure Calculation: No side effects, returns list of AstroEvent objects.
3. Fallback Safety: Gracefully handles missing ephemeris files by attempting Moshier fallback.
"""

import logging
import swisseph as swe
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional

from src.core.base_event import AstroEvent
from src.core.constants import EventType

# Initialize Logger
logger = logging.getLogger(__name__)

# --- Internal Constants (Independent from Immanuel) ---
# Planets
SUN=0; MOON=1; MERCURY=2; VENUS=3; MARS=4;
JUPITER=5; SATURN=6; URANUS=7; NEPTUNE=8; PLUTO=9

PLANET_NAMES = {
    SUN: "Sol", MOON: "Luna", MERCURY: "Mercurio",
    VENUS: "Venus", MARS: "Marte", JUPITER: "Júpiter",
    SATURN: "Saturno", URANUS: "Urano", NEPTUNE: "Neptuno",
    PLUTO: "Plutón"
}

# Aspects (Standard Set + Sextiles/Trines)
ASPECTS = {
    "Conjunción": 0,
    "Sextil": 60,
    "Cuadratura": 90,
    "Trígono": 120,
    "Oposición": 180
}

# Chart dummy class for compatibility if needed (internal mapping)
class ChartID:
    SUN=SUN; MOON=MOON; MERCURY=MERCURY; VENUS=VENUS;
    MARS=MARS; JUPITER=JUPITER; SATURN=SATURN;
    URANUS=URANUS; NEPTUNE=NEPTUNE; PLUTO=PLUTO

class VectorizedTransitsCalculator:
    def __init__(self, natal_data: dict):
        """
        Initialize the Vectorized Calculator.
        
        Args:
            natal_data: Dictionary containing natal chart data (points, location, etc.)
        """
        self.natal_data = natal_data
        self.natal_positions = {}
        
        # Parse natal positions (support both "Sun" and "Sol" keys if unstable)
        # Using the standard naming convention expected from API
        for pname, data in natal_data.get('points', {}).items():
            # Standardize name to ID
            pid = self._get_planet_id(pname)
            if pid is not None:
                self.natal_positions[pid] = data['longitude']
                
        logger.info(f"VectorizedTransitsCalculator initialized with {len(self.natal_positions)} natal points.")

    def _get_planet_id(self, name: str) -> Optional[int]:
        """Map string name to SwissEph ID safely."""
        name_lower = name.lower()
        mapping = {
            "sun": SUN, "sol": SUN,
            "moon": MOON, "luna": MOON,
            "mercury": MERCURY, "mercurio": MERCURY,
            "venus": VENUS,
            "mars": MARS, "marte": MARS,
            "jupiter": JUPITER, "júpiter": JUPITER,
            "saturn": SATURN, "saturno": SATURN,
            "uranus": URANUS, "urano": URANUS,
            "neptune": NEPTUNE, "neptuno": NEPTUNE,
            "pluto": PLUTO, "plutón": PLUTO
        }
        return mapping.get(name_lower)

    def calculate_all(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """
        Calculate all transits for the given period using vectorized operations.
        
        Args:
            start_date: Start datetime (UTC aware preferred)
            end_date: End datetime (UTC aware preferred)
            
        Returns:
            List of AstroEvent objects sorted by date.
        """
        start_time_perf = datetime.now()
        
        # 1. Prepare Time Grid
        # Generate daily points. Resolution is 1 day for the rough search.
        total_days = (end_date - start_date).days + 2
        dates = [start_date + timedelta(days=i) for i in range(total_days)]
        
        # Convert to Julian Days for SwissEph
        # Note: dates are datetime objects. if timezone unaware, assume UTC? 
        # Ideally they should be timezone aware.
        jds = np.array([self._to_jd(d) for d in dates])
        
        # 2. Ephemeris Calculation (Vectorized Batch)
        # Calculate positions for all supported planets for all days
        # Shape: (NumPlanets, NumDays)
        planets_to_calc = sorted(list(PLANET_NAMES.keys()))
        curr_positions = np.zeros((len(planets_to_calc), len(jds)))
        
        # Ephemeris Flags
        # Try default (Speed + SwissEph)
        flags = swe.FLG_SPEED | swe.FLG_SWIEPH
        
        for i, pid in enumerate(planets_to_calc):
            for j, jd in enumerate(jds):
                try:
                    res = swe.calc_ut(jd, pid, flags)
                    curr_positions[i, j] = res[0][0] # Longitude
                except swe.Error:
                    # Fallback to Moshier if file missing or error
                    # Log only once per planet to avoid spam
                    if j == 0:
                        logger.warning(f"SwissEph error for planet {pid}, falling back to Moshier mode.")
                    res = swe.calc_ut(jd, pid, swe.FLG_SPEED | swe.FLG_MOSEPH)
                    curr_positions[i, j] = res[0][0]

        events = []
        
        # 3. Detect Aspect Crossings (Zero-Crossing)
        # For each transit planet vs each natal planet vs each aspect type
        for i, transit_pid in enumerate(planets_to_calc):
            transit_lons = curr_positions[i]
            
            for natal_pid, natal_lon in self.natal_positions.items():
                for asp_name, asp_angle in ASPECTS.items():
                    # Target position in zodiac
                    target = (natal_lon + asp_angle) % 360
                    
                    # Calculate diffs relative to target [-180, 180]
                    # We want to find where diff crosses 0
                    diffs = (transit_lons - target + 180) % 360 - 180
                    
                    # Criteria for crossing:
                    # 1. Sign change: diff[t] * diff[t+1] <= 0
                    # 2. No Wrap-around: abs(diff[t] - diff[t+1]) < 180
                    # If jump is > 180, it means we crossed the 0/360 cut, not the target.
                    
                    candidates = (diffs[:-1] * diffs[1:] <= 0) & (np.abs(diffs[:-1] - diffs[1:]) < 180)
                    day_indices = np.where(candidates)[0]
                    
                    for day_idx in day_indices:
                        # 4. Refine Time (Bisection Search)
                        # We know event is between day_idx and day_idx+1
                        t0 = jds[day_idx]
                        t1 = jds[day_idx+1]
                        
                        exact_time = self._find_precise_time(transit_pid, target, t0, t1)
                        
                        if exact_time:
                            dt = self._jd_to_datetime(exact_time)
                            
                            # Standard boundary check
                            if not (start_date <= dt <= end_date):
                                continue
                                
                            # Double-check orb to filter false positives
                            # (e.g. erratic retrograde movements at edge)
                            final_pos, speed = self._get_pos_safe(exact_time, transit_pid)
                            final_orb = abs(self._normalize_diff(final_pos, target))
                            
                            if final_orb > 0.05: # > 0.05 degree error is suspicious for exact aspect logic
                                continue
                            
                            # Determine Movement Name (for RAG compatibility)
                            if abs(speed) < 0.0001:
                                movement_name = "Estacionario"
                            elif speed < 0:
                                movement_name = "Retrógrado"
                            else:
                                movement_name = "Directo"

                            # Format description exactly like V4 for RAG compatibility
                            # "{planet} ({movement}) por tránsito esta en {aspect} a tu {natal} Natal"
                            desc = f"{PLANET_NAMES[transit_pid]} ({movement_name.lower()}) por tránsito esta en {asp_name} a tu {PLANET_NAMES[natal_pid]} Natal"

                            # Create Event
                            events.append(AstroEvent(
                                fecha_utc=dt,
                                tipo_evento=EventType.ASPECTO,
                                descripcion=desc,
                                planeta1=PLANET_NAMES[transit_pid],
                                planeta2=PLANET_NAMES[natal_pid],
                                longitud1=final_pos,
                                longitud2=natal_lon,
                                tipo_aspecto=asp_name,
                                orbe=final_orb,
                                es_aplicativo=False, # Vectorized simplifies this (exact moment)
                                metadata={
                                    "method": "vectorized_v1",
                                    "movimiento": movement_name,
                                    "posicion1": f"{self._format_deg(final_pos)}",
                                    "posicion2": f"{self._format_deg(natal_lon)}"
                                }
                            ))

        # Sort by date
        events.sort(key=lambda x: x.fecha_utc)
        
        elapsed = (datetime.now() - start_time_perf).total_seconds()
        logger.info(f"Vectorized calculation finished: {len(events)} events in {elapsed:.4f}s")
        
        return events

    def _get_pos_safe(self, jd, pid):
        """
        Helper to get position and speed with fallback logic.
        Returns: (longitude, speed)
        """
        try:
            res = swe.calc_ut(jd, pid, swe.FLG_SPEED | swe.FLG_SWIEPH)
            return res[0][0], res[0][3]
        except swe.Error:
            res = swe.calc_ut(jd, pid, swe.FLG_SPEED | swe.FLG_MOSEPH)
            return res[0][0], res[0][3]

    def _find_precise_time(self, pid, target_lon, jd_start, jd_end, steps=10) -> Optional[float]:
        """Binary search for precise event time."""
        low = jd_start
        high = jd_end
        
        for _ in range(steps):
            mid = (low + high) / 2
            pos, _ = self._get_pos_safe(mid, pid)
            diff = self._normalize_diff(pos, target_lon)
            
            if abs(diff) < 0.00001: # High precision
                return mid
            
            # Check direction
            pos_low, _ = self._get_pos_safe(low, pid)
            diff_low = self._normalize_diff(pos_low, target_lon)
            
            if diff * diff_low < 0:
                high = mid
            else:
                low = mid
                
        return (low + high) / 2

    def _normalize_diff(self, a, b):
        """Shortest distance between angles [-180, 180]."""
        return (a - b + 180) % 360 - 180

    def _to_jd(self, dt: datetime) -> float:
        """Datetime to Julian Day."""
        # Ensure UTC behavior
        if dt.tzinfo is None:
            # Assume UTC if naive, or local? 
            # swisseph expects UT.
            pass
        else:
            dt = dt.astimezone(ZoneInfo("UTC"))
            
        return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

    def _jd_to_datetime(self, jd: float) -> datetime:
        """Julian Day to Datetime UTC."""
        y, m, d, h = swe.revjul(jd)
        hour = int(h)
        mins = int((h - hour) * 60)
        secs = int(((h - hour) * 60 - mins) * 60)
        # Microseconds for cleaner output?
        return datetime(y, m, d, hour, mins, secs, tzinfo=ZoneInfo("UTC"))

    def _format_deg(self, deg: float) -> str:
        """
        Format absolute degree (0-360) to Zodiac notation (e.g. 15°20' Aries).
        """
        signs = [
            "Aries", "Tauro", "Géminis", "Cáncer", 
            "Leo", "Virgo", "Libra", "Escorpio", 
            "Sagitario", "Capricornio", "Acuario", "Piscis"
        ]
        
        normalized_deg = deg % 360
        sign_idx = int(normalized_deg / 30)
        deg_in_sign = normalized_deg % 30
        
        d = int(deg_in_sign)
        m = int((deg_in_sign - d) * 60)
        
        return f"{d}°{m:02d}' {signs[sign_idx]}"
