from datetime import datetime, timedelta
from typing import List, Dict, Optional
import swisseph as swe
from ..core.constants import EventType, AstronomicalConstants
from ..core.base_event import AstroEvent
from ..utils.time_utils import julian_day
from ..utils.math_utils import format_position

class NodeCalculator:
    """Calculador de ingresos del Nodo Lunar"""
    def __init__(self, timezone_str: str = "UTC"):
        """
        Inicializa el calculador de nodos.
        
        Args:
            timezone_str: La zona horaria a usar para los eventos generados.
        """
        self.timezone_str = timezone_str
        
    def _calculate_node_position(self, date: datetime) -> Dict:
        """Calcula posición y velocidad del nodo lunar"""
        jd = julian_day(date)
        result = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH)
        
        return {
            'date': date,
            'longitude': result[0][0],
            'latitude': result[0][1],
            'distance': result[0][2],
            'speed': result[0][3],
            'position_str': format_position(result[0][0])
        }

    def _find_exact_ingress(self, start_date: datetime, end_date: datetime,
                           from_sign: int, to_sign: int) -> Optional[Dict]:
        """Encuentra el momento exacto del ingreso del nodo a un signo"""
        # Primera fase: búsqueda cada hora
        interval = timedelta(hours=1)
        current_date = start_date
        transition_found = False
        
        while current_date <= end_date:
            pos = self._calculate_node_position(current_date)
            current_sign = int(pos['longitude'] / 30)
            
            if current_sign != from_sign:
                transition_found = True
                break
                
            current_date += interval
            
        if not transition_found:
            return None
            
        # Segunda fase: refinamiento cada minuto
        refined_start = current_date - interval
        refined_end = current_date
        interval = timedelta(minutes=1)
        
        current_date = refined_start
        best_date = None
        min_distance = float('inf')
        best_pos = None
        
        while current_date <= refined_end:
            pos = self._calculate_node_position(current_date)
            sign_boundary = to_sign * 30.0
            distance = abs(pos['longitude'] - sign_boundary)
            
            if distance < min_distance:
                min_distance = distance
                best_date = current_date
                best_pos = pos
                
            current_date += interval
            
        return best_pos if best_date else None

    def calculate_node_ingresses(self, start_date: datetime, end_date: datetime) -> List[AstroEvent]:
        """Calcula ingresos del Nodo Norte a signos zodiacales"""
        events = []
        current_date = start_date
        check_interval = timedelta(hours=12)  # Los nodos se mueven lentamente
        prev_sign = None
        
        # Obtener posición inicial para verificar dirección del movimiento
        initial_pos = self._calculate_node_position(current_date)
        is_retrograde = initial_pos['speed'] < 0
        
        while current_date < end_date:
            pos = self._calculate_node_position(current_date)
            current_sign = int(pos['longitude'] / 30)
            
            # Verificar cambio de dirección
            current_retrograde = pos['speed'] < 0
            if current_retrograde != is_retrograde:
                is_retrograde = current_retrograde
                
            if prev_sign is not None and current_sign != prev_sign:
                exact_pos = self._find_exact_ingress(
                    current_date - timedelta(days=1),
                    current_date + timedelta(days=1),
                    prev_sign,
                    current_sign
                )
                
                if exact_pos:
                    movement = " (Retrógrado)" if is_retrograde else " (Directo)"
                    
                    events.append(AstroEvent(
                        fecha_utc=exact_pos['date'],
                        tipo_evento=EventType.INGRESO_SIGNO,
                        descripcion=f"Nodo Norte ingresa a 0° de {AstronomicalConstants.SIGNS[current_sign]}{movement}",
                        elevacion=None,
                        azimut=None,
                        timezone_str=self.timezone_str # Pasar la zona horaria
                    ))
            
            prev_sign = current_sign
            current_date += check_interval
            
        return events
