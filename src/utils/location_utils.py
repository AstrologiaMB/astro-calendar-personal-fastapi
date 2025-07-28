from datetime import datetime
from typing import Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.location import Location as GeopyLocation
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
from ..core.location import Location
import time

# Create geocoder at module level for reuse
geocoder = Nominatim(user_agent="astro_calendar_personal")

def get_coordinates(place_name: str, max_retries: int = 3, timeout: int = 10) -> Optional[Tuple[float, float, float]]:
    """
    Convert a place name to coordinates (latitude, longitude, elevation).
    
    Args:
        place_name: Name of the place to geocode
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for each request
        
    Returns:
        Tuple containing (latitude, longitude, elevation) or None if not found
        
    Raises:
        ValueError: If the place cannot be found
    """
    for attempt in range(max_retries):
        try:
            location: GeopyLocation = geocoder.geocode(place_name, timeout=timeout)
            
            if location is None:
                raise ValueError(f"Could not find coordinates for {place_name}")
                
            # Nominatim provides altitude/elevation when available, default to 0 if not
            elevation = getattr(location, 'altitude', 0) or 0
            
            return location.latitude, location.longitude, elevation
        except GeocoderTimedOut:
            if attempt == max_retries - 1:  # Last attempt
                raise ValueError(f"Geocoding timed out for {place_name} after {max_retries} attempts")
            time.sleep(1)  # Wait before retrying
        except Exception as e:
            raise ValueError(f"Error geocoding {place_name}: {str(e)}")

def get_timezone(latitude: float, longitude: float) -> str:
    """
    Get the timezone identifier for given coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        Timezone identifier string (e.g. 'America/New_York')
        
    Raises:
        ValueError: If no timezone found for coordinates
    """
    tf = TimezoneFinder()
    timezone = tf.timezone_at(lat=latitude, lng=longitude)
    
    if timezone is None:
        # For locations without a specific timezone (e.g., oceans),
        # calculate the approximate timezone based on longitude
        hours_offset = round(longitude / 15)
        if hours_offset <= 0:
            timezone = f"Etc/GMT+{abs(hours_offset)}"
        else:
            timezone = f"Etc/GMT-{hours_offset}"
    
    return timezone

def create_location_from_place(place_name: str) -> Location:
    """
    Create a Location instance from a place name.
    
    Args:
        place_name: Name of the place
        
    Returns:
        Location instance
        
    Raises:
        ValueError: If the place cannot be found or timezone cannot be determined
    """
    lat, lon, elevation = get_coordinates(place_name)
    timezone = get_timezone(lat, lon)
    return Location(lat, lon, place_name, timezone, elevation)

def local_to_utc(local_time: datetime, timezone: str) -> datetime:
    """
    Convert local time to UTC.
    
    Args:
        local_time: Local datetime
        timezone: Timezone identifier string
        
    Returns:
        UTC datetime
    """
    local_tz = ZoneInfo(timezone)
    local_with_tz = local_time.replace(tzinfo=local_tz)
    return local_with_tz.astimezone(ZoneInfo('UTC'))

def utc_to_local(utc_time: datetime, timezone: str) -> datetime:
    """
    Convert UTC time to local time.
    
    Args:
        utc_time: UTC datetime
        timezone: Timezone identifier string
        
    Returns:
        Local datetime
    """
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=ZoneInfo('UTC'))
    local_tz = ZoneInfo(timezone)
    return utc_time.astimezone(local_tz)
