from datetime import datetime, timedelta
from typing import List
import swisseph as swe
from ..core.constants import EventType, AstronomicalConstants
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import calculate_planet_position, format_position

class IngressCalculator:
    def __init__(self, timezone_str: str = "UTC"):
        """
        Inicializa el calculador de ingresos.
        
        Args:
            timezone_str: La zona horaria a usar para los eventos generados.
        """
        self.timezone_str = timezone_str
        
    def calculate_ingresses(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """Calcula ingresos planetarios a signos zodiacales"""
        events = []
        
        for planet_name, (planet_id, _) in AstronomicalConstants.PLANETS.items():
            current_date = start_date
            prev_sign = None
            prev_speed = None

            while current_date < end_date:
                jd = julian_day(current_date)
                pos = calculate_planet_position(jd, planet_id)
                current_sign = int(pos['longitude'] / 30)
                is_retro = pos['speed'] < 0

                if prev_sign is not None and current_sign != prev_sign:
                    exact_date = self._find_exact_ingress(
                        current_date - timedelta(days=1),
                        current_date + timedelta(days=1),
                        planet_id,
                        prev_sign,
                        current_sign
                    )

                    jd_exact = julian_day(exact_date)
                    exact_pos = calculate_planet_position(jd_exact, planet_id)
                    is_retro_at_ingress = exact_pos['speed'] < 0

                    # Determinar el signo que se muestra en la descripción
                    if is_retro_at_ingress:
                        # Si es retrógrado, mostrar el signo que está dejando
                        display_sign = prev_sign
                        action = "deja a"
                    else:
                        # Si es directo, mostrar el signo al que ingresa
                        display_sign = current_sign
                        action = "ingresa a"

                    movement = " (Retrógrado)" if is_retro_at_ingress else " (Directo)"

                    # Calcular el grado exacto
                    degree = exact_pos['longitude'] % 30
                    if is_retro_at_ingress:
                        degree = 29.99  # Casi 30° del signo que deja
                    else:
                        degree = 0.00   # 0° del signo al que ingresa

                    events.append(AstroEvent(
                        fecha_utc=exact_date,
                        tipo_evento=EventType.INGRESO_SIGNO,
                        descripcion=f"{planet_name} {action} {degree:.2f}° de {AstronomicalConstants.SIGNS[display_sign]}{movement}",
                        planeta1=planet_name,
                        longitud1=exact_pos['longitude'],
                        velocidad1=exact_pos['speed'],
                        signo=AstronomicalConstants.SIGNS[display_sign],
                        grado=degree,
                        timezone_str=self.timezone_str # Pasar la zona horaria
                    ))

                prev_sign = current_sign
                prev_speed = pos['speed']
                current_date += timedelta(hours=6)

        return sorted(events, key=lambda x: x.fecha_utc)

    def _find_exact_ingress(self, start_date: datetime, end_date: datetime,
                           planet_id: int, from_sign: int, to_sign: int) -> datetime:
        """Encuentra el momento exacto del ingreso a un signo"""
        tolerance = timedelta(seconds=1)  # Aumentar precisión a 1 segundo

        while (end_date - start_date) > tolerance:
            mid_date = start_date + (end_date - start_date) / 2
            jd = julian_day(mid_date)
            pos = calculate_planet_position(jd, planet_id)
            current_sign = int(pos['longitude'] / 30)

            if current_sign == from_sign:
                start_date = mid_date
            else:
                end_date = mid_date

        return start_date
