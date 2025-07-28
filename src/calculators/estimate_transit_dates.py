def estimate_transit_dates(self, planet_id, natal_position, aspect_angle, year, start_date=None, end_date=None):
    """
    Estima las fechas en que un planeta transitará por una posición específica.
    Versión mejorada con muestreo adaptativo.
    
    Args:
        planet_id: ID del planeta transitante
        natal_position: Posición natal en grados
        aspect_angle: Ángulo del aspecto (0 para conjunción, 180 para oposición, etc.)
        year: Año para el cálculo
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        
    Returns:
        Lista de fechas estimadas
    """
    # Usar la zona horaria del usuario para las fechas por defecto
    if start_date is None:
        start_date = datetime(year, 1, 1, tzinfo=self.user_timezone)
    if end_date is None:
        end_date = datetime(year, 12, 31, 23, 59, tzinfo=self.user_timezone)
    
    # Calcular la posición objetivo
    target_position = (natal_position + aspect_angle) % 360
    
    # Para cuadraturas, hay dos posiciones posibles (90° y 270°)
    target_positions = [target_position]
    if aspect_angle == 90:
        target_positions.append((natal_position - 90) % 360)
    
    # Obtener la posición inicial del planeta
    jd_start = self.datetime_to_jd(start_date)
    planet_data = ephemeris.planet(planet_id, jd_start)
    initial_position = planet_data['lon']
    initial_speed = planet_data['speed']
    
    # Verificar si el planeta está retrógrado al inicio
    is_retrograde_initial = initial_speed < 0
    
    estimated_dates = []
    
    # Calcular el período en días para que el planeta recorra 360°
    period = ORBITAL_PERIODS.get(planet_id, 365.25)  # Usar 365.25 como valor predeterminado
    
    # Calcular cuántos ciclos completos puede hacer el planeta en el período
    days_in_period = (end_date - start_date).total_seconds() / 86400.0
    cycles = max(1, int(days_in_period / period) + 1)
    
    # Ajustar el tamaño de la ventana de estimación basado en:
    # 1. Período orbital (planetas más lentos necesitan ventanas más amplias)
    # 2. Tipo de aspecto (las cuadraturas necesitan más muestreo)
    # 3. Velocidad del planeta (planetas más lentos necesitan más muestreo)
    
    # Factor base para el tamaño de la ventana
    window_base_size = 15  # Aumentado de 10 a 15 días para mejor cobertura
    
    # Factor de ajuste basado en el período orbital
    window_factor = min(1.0, 30 / period)  # Factor de ajuste basado en el período
    
    # Ajuste adicional para cuadraturas (más difíciles de detectar)
    aspect_factor = 2.0 if aspect_angle == 90 else 1.0  # Duplicado para cuadraturas
    
    # Ajuste para planetas lentos (Júpiter, Saturno, etc.)
    planet_speed_factor = 1.0
    if planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
        planet_speed_factor = 2.0  # 100% más de muestreo para planetas lentos
    
    # Calcular tamaño final de la ventana
    window_size = int(window_base_size / window_factor * aspect_factor * planet_speed_factor)
    
    # Limitar el tamaño máximo de la ventana
    window_size = min(window_size, 45)  # Aumentado de 30 a 45 para mejor cobertura
    
    # Generar offsets para la ventana de estimación con mayor densidad
    # Reducir el paso para tener más puntos de muestreo
    step_size = max(1, window_size // 16)  # Más denso que el original (window_size // 8)
    offsets = list(range(-window_size, window_size + 1, step_size))
    if 0 not in offsets:
        offsets.append(0)
    offsets.sort()
    
    # Variables para seguimiento de velocidad
    last_speed = None
    last_recalc_date = start_date
    
    # Para cada posición objetivo
    for target_pos in target_positions:
        # Calcular la diferencia angular inicial
        angle_diff = self.normalize_angle_diff(target_pos, initial_position)
        
        # Ajustar el cálculo de días basado en la dirección del movimiento y la velocidad real
        # Usar la velocidad real del planeta en lugar de la velocidad media
        if abs(initial_speed) < 0.0001:  # Si el planeta está casi estacionario
            # Usar la velocidad media como fallback
            days_to_target = abs(angle_diff) / AVERAGE_SPEED[planet_id]
            first_date = start_date + timedelta(days=period / 4)  # Comenzar a 1/4 del período
        elif is_retrograde_initial:
            # Si el planeta está retrógrado, la dirección es opuesta
            days_to_target = abs(angle_diff) / abs(initial_speed)
            # Si el ángulo es positivo, necesitamos ir en dirección negativa (y viceversa)
            first_date = start_date + timedelta(days=days_to_target if angle_diff < 0 else period - days_to_target)
        else:
            # Movimiento directo normal, usar velocidad real
            days_to_target = abs(angle_diff) / abs(initial_speed)
            first_date = start_date + timedelta(days=days_to_target if angle_diff > 0 else period - days_to_target)
        
        # Si la primera fecha está después del final del período, no hay tránsitos
        if first_date > end_date:
            continue
        
        # Ajustar la primera fecha si está antes del inicio
        if first_date < start_date:
            first_date = start_date + timedelta(days=period - (days_to_target % period))
        
        # Generar fechas estimadas para cada ciclo
        current_date = first_date
        for _ in range(cycles):
            if current_date <= end_date:
                # Obtener intervalo adaptativo
                sampling_interval = self.get_adaptive_sampling_interval(
                    planet_id, 
                    aspect_angle, 
                    current_date,
                    last_speed
                )
                
                # Añadir fecha actual
                estimated_dates.append((current_date, target_pos))
                
                # Añadir fechas adicionales alrededor de la estimación para mayor precisión
                for offset in offsets:
                    check_date = current_date + timedelta(days=offset)
                    if start_date <= check_date <= end_date:
                        estimated_dates.append((check_date, target_pos))
                
                # Actualizar velocidad cada cierto tiempo
                days_since_last_recalc = (current_date - last_recalc_date).days
                recalc_interval = 7  # Valor predeterminado
                
                # Ajustar intervalo de recálculo según el planeta
                if planet_id in [chart.MERCURY, chart.VENUS]:
                    recalc_interval = 3
                elif planet_id in [chart.JUPITER, chart.SATURN, chart.URANUS, chart.NEPTUNE, chart.PLUTO]:
                    recalc_interval = 10
                
                if days_since_last_recalc >= recalc_interval:
                    jd_current = self.datetime_to_jd(current_date)
                    current_data = ephemeris.planet(planet_id, jd_current)
                    last_speed = abs(current_data['speed'])
                    last_recalc_date = current_date
                
                # Avanzar al siguiente punto de muestreo
                current_date += sampling_interval
            else:
                break
    
    # Para cuadraturas, añadir muestreo adicional para Mercurio
    if aspect_angle == 90 and planet_id == chart.MERCURY:
        extra_dates = []
        current = start_date
        # Para Mercurio, usar muestreo cada 30 minutos
        mercury_interval = timedelta(minutes=30)
        
        while current <= end_date:
            for target_pos in target_positions:
                extra_dates.append((current, target_pos))
            current += mercury_interval
        
        # Combinar con fechas estimadas
        estimated_dates.extend(extra_dates)
    
    return estimated_dates
