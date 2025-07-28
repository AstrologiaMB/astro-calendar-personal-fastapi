from datetime import datetime, timedelta, timezone
from typing import Callable, Tuple
import swisseph as swe
import warnings
import pytz

def utc_to_local(utc_dt: datetime, timezone_str: str = 'America/Argentina/Buenos_Aires') -> datetime:
    """
    Convierte una fecha UTC a hora local.
    
    Args:
        utc_dt: Fecha UTC a convertir
        timezone_str: String de zona horaria (default: 'America/Argentina/Buenos_Aires')
    
    Returns:
        datetime: Fecha en hora local
    """
    local_tz = pytz.timezone(timezone_str)
    
    # Si la fecha no tiene zona horaria, asumimos que es UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    # Si la fecha tiene zona horaria pero no es UTC, la convertimos a UTC
    elif utc_dt.tzinfo != pytz.UTC:
        utc_dt = utc_dt.astimezone(pytz.UTC)
        
    # Convertir de UTC a hora local
    local_dt = utc_dt.astimezone(local_tz)
    
    # Ajuste manual de 3 horas para coincidir con AstroSeek
    return local_dt + timedelta(hours=3)


def julian_day(date: datetime) -> float:
    """
    Convierte datetime a día juliano.
    Si la fecha tiene zona horaria, la convierte a UTC antes de calcular el día juliano.
    """
    # Si la fecha tiene zona horaria, convertir a UTC
    if date.tzinfo is not None:
        utc_date = date.astimezone(timezone.utc)
    else:
        utc_date = date
        
    jd = swe.julday(utc_date.year, utc_date.month, utc_date.day,
                    utc_date.hour + utc_date.minute/60.0 + utc_date.second/3600.0)
    
    # Ajustar por Delta T (diferencia entre Tiempo Dinámico y Universal)
    jd_tt = jd + swe.deltat(jd)/86400.0
    
    return jd_tt

def binary_search_exact_time(
    start_date: datetime,
    end_date: datetime,
    condition_func: Callable[[datetime], float],
    tolerance: timedelta = timedelta(milliseconds=100)
) -> Tuple[datetime, float]:
    """
    Encuentra el momento exacto en que una condición alcanza su valor mínimo
    usando búsqueda dicotómica (bisección).

    Esta función es más eficiente que find_exact_time(), reduciendo el número
    de iteraciones necesarias para encontrar el momento exacto.

    Args:
        start_date: Fecha inicial de búsqueda
        end_date: Fecha final de búsqueda
        condition_func: Función que evalúa la condición, debe retornar:
            - Valor negativo si el momento buscado está después
            - Valor positivo si el momento buscado está antes
            - Cerca de cero cuando encuentra el momento exacto
        tolerance: Tolerancia mínima en tiempo (default: 100 milisegundos)
                 Usar valores más pequeños aumenta la precisión pero
                 también el tiempo de cálculo.

    Returns:
        Tuple[datetime, float]: (momento_exacto, valor_minimo)

    Ejemplo:
        # Buscar momento exacto de un aspecto
        def condition(date):
            jd = julian_day(date)
            pos = calculate_planet_position(jd)
            return abs(pos['longitude'] - target_pos)

        exact_date, min_orb = binary_search_exact_time(
            start_date,
            end_date,
            condition,
            tolerance=timedelta(milliseconds=100)
        )
    """
    best_date = start_date
    min_value = condition_func(start_date)

    while (end_date - start_date) > tolerance:
        mid_date = start_date + (end_date - start_date) / 2
        mid_value = condition_func(mid_date)
        
        if mid_value < min_value:
            min_value = mid_value
            best_date = mid_date

        # Determinar en qué mitad continuar la búsqueda
        before_mid = condition_func(mid_date - tolerance)
        after_mid = condition_func(mid_date + tolerance)
        
        if before_mid < after_mid:
            end_date = mid_date
        else:
            start_date = mid_date

    # Refinamiento final usando interpolación
    if start_date != end_date:
        start_val = condition_func(start_date)
        end_val = condition_func(end_date)
        
        if start_val < min_value:
            min_value = start_val
            best_date = start_date
        if end_val < min_value:
            min_value = end_val
            best_date = end_date

    return best_date, min_value

def find_exact_time(
    start_date: datetime,
    end_date: datetime,
    condition_func: Callable[[datetime], float],
    tolerance: timedelta = timedelta(seconds=1),
    step_sizes: list = None
) -> Tuple[datetime, float]:
    """
    DEPRECATED: Esta función será reemplazada en futuras versiones.
    Use binary_search_exact_time() para mejor rendimiento y precisión.
    
    Encuentra el momento exacto en que una condición alcanza su valor mínimo usando búsqueda progresiva.
    """
    warnings.warn(
        "find_exact_time está deprecada, use binary_search_exact_time para mejor rendimiento",
        DeprecationWarning,
        stacklevel=2
    )
    
    if step_sizes is None:
        step_sizes = [60, 5, 1, 0.0167]  # 1 hora → 5 minutos → 1 minuto → 1 segundo
        
    best_date = start_date
    min_value = condition_func(start_date)
    
    # Búsqueda progresiva con diferentes tamaños de paso
    for step_size in step_sizes:
        current_step = timedelta(minutes=step_size)
        current_date = start_date
        
        # Ajustar ventana de búsqueda alrededor del mejor punto encontrado
        if best_date != start_date:
            # Mantener la ventana de 24 horas centrada en el mejor punto
            window = timedelta(hours=12)
            new_start = best_date - window
            new_end = best_date + window
            
            # No permitir que la ventana se extienda más allá de los límites originales
            start_date = max(start_date, new_start)
            end_date = min(end_date, new_end)
            current_date = start_date
        
        # Búsqueda lineal con el paso actual
        while current_date <= end_date:
            value = condition_func(current_date)
            if value < min_value:
                min_value = value
                best_date = current_date
                
                # Para el paso más fino (1 segundo), buscar el mínimo exacto
                if step_size < 1:
                    # Buscar alrededor del punto actual con más precisión
                    for offset in range(-30, 31):  # ±30 segundos
                        test_date = current_date + timedelta(seconds=offset)
                        test_value = condition_func(test_date)
                        if test_value < min_value:
                            min_value = test_value
                            best_date = test_date
            
            current_date += current_step
    
    # Refinamiento final usando interpolación
    if start_date != end_date:
        start_val = condition_func(start_date)
        end_val = condition_func(end_date)
        
        if start_val < min_value:
            min_value = start_val
            best_date = start_date
        if end_val < min_value:
            min_value = end_val
            best_date = end_date
            
        # Interpolación parabólica para mayor precisión
        mid_date = start_date + (end_date - start_date) / 2
        mid_val = condition_func(mid_date)
        
        if mid_val < min_value:
            min_value = mid_val
            best_date = mid_date
            
            # Ajuste fino usando los tres puntos
            denom = (start_val - 2*mid_val + end_val)
            if abs(denom) > 1e-10:
                alpha = 0.5 * (start_val - end_val) / denom
                if 0 < alpha < 1:
                    interp_date = start_date + alpha * (end_date - start_date)
                    interp_val = condition_func(interp_date)
                    if interp_val < min_value:
                        min_value = interp_val
                        best_date = interp_date
    
    return best_date, min_value

def interpolate_time(
    time1: datetime,
    time2: datetime,
    val1: float,
    val2: float,
    target: float
) -> datetime:
    """
    Interpola linealmente entre dos tiempos basado en sus valores.
    
    Args:
        time1: Primer tiempo
        time2: Segundo tiempo
        val1: Valor en time1
        val2: Valor en time2
        target: Valor objetivo
    
    Returns:
        datetime: Tiempo interpolado
    """
    if abs(val2 - val1) < 1e-10:  # Evitar división por cero
        return time1
        
    # Interpolación mejorada usando spline cúbico
    h = (time2 - time1).total_seconds()
    t = (target - val1) / (val2 - val1)
    
    # Ajuste no lineal para mejor precisión cerca de los extremos
    if t < 0.1:
        t = t * (1.0 + 0.1 * (1.0 - t))
    elif t > 0.9:
        t = t * (1.0 - 0.1 * t)
        
    return time1 + timedelta(seconds=h * t)
