import ephem
from zoneinfo import ZoneInfo

class Location:
    """Clase para manejar ubicaciones"""

    def __init__(self, lat: float, lon: float, name: str, timezone: str, elevation: float = 0):
        self.lat = lat
        self.lon = lon
        self.name = name
        self.timezone = timezone
        self.elevation = elevation
        self.tz = ZoneInfo(timezone)

        # Formato para ephem
        self.lat_str = f"{abs(lat)}{'s' if lat < 0 else 'n'}"
        self.lon_str = f"{abs(lon)}{'w' if lon < 0 else 'e'}"

    def create_ephem_observer(self) -> ephem.Observer:
        """Crea un observador de ephem"""
        observer = ephem.Observer()
        observer.lat = str(self.lat)
        observer.lon = str(self.lon)
        observer.elevation = self.elevation
        observer.pressure = 1013.25  # Presión atmosférica estándar
        observer.temp = 15  # Temperatura promedio
        return observer