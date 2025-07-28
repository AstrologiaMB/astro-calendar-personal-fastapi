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

def find_transits_for_planet(self, planet_id, year, start_date=None, end_date=None):
    """
    Encuentra todos los tránsitos de un planeta para un año específico.
    Versión mejorada con detección avanzada de cambios de dirección.
    
    Args:
        planet_id: ID del planeta transitante
        year: Año para el cálculo
        start_date: Fecha de inicio (opcional)
        end_date: Fecha de fin (opcional)
        
    Returns:
        Lista de tránsitos encontrados
    """
    # Usar la zona horaria del usuario para las fechas por defecto
    if start_date is None:
        start_date = datetime(year, 1, 1, tzinfo=self.user_timezone)
    if end_date is None:
        end_date = datetime(year, 12, 31, 23, 59, tzinfo=self.user_timezone)
    
    transits = []
    
    # Detectar cambios de dirección para este planeta
    direction_changes = self.detect_direction_changes(planet_id, start_date, end_date)
    print(f"Detectados {len(direction_changes)} cambios de dirección para {PLANET_NAMES.get(planet_id, planet_id)}")
    
    # Para cada planeta/punto natal
    for natal_id, natal_position in self.natal_positions.items():
        # Para cada tipo de aspecto
        for aspect_type, aspect_angle in ASPECT_ANGLES.items():
            # Verificar si esta es una combinación potencialmente problemática
            needs_extra_verification = self.is_challenging_combination(planet_id, natal_id, aspect_type)
            
            # Estimar fechas de tránsito
            estimated_dates = self.estimate_transit_dates(
                planet_id, natal_position, aspect_angle, year, start_date, end_date
            )
            
            # Calcular la posición objetivo para este aspecto
            target_position = (natal_position + aspect_angle) % 360
            
            # Para combinaciones potencialmente problemáticas, añadir verificación adicional
            if needs_extra_verification:
                # Determinar la frecuencia de verificación basada en la velocidad del planeta
                if planet_id == chart.MERCURY:
                    # Para Mercurio, verificar cada 6 horas
                    check_interval = timedelta(hours=6)
                elif planet_id == chart.VENUS:
                    # Para Venus, verificar cada 12 horas
                    check_interval = timedelta(hours=12)
                elif planet_id in [chart.MARS, chart.JUPITER]:
                    # Para Marte y Júpiter, verificar cada día
                    check_interval = timedelta(days=1)
                else:
                    # Para planetas lentos, verificar cada 3 días
                    check_interval = timedelta(days=3)
                
                # Añadir verificaciones adicionales
                extra_dates = []
                current = start_date
                while current <= end_date:
                    extra_dates.append((current, target_position))
                    current += check_interval
                
                # Combinar con fechas estimadas
                estimated_dates.extend(extra_dates)
            
            # Añadir muestreo ultra-denso alrededor de cambios de dirección
            all_dates = self.add_critical_period_sampling(
                planet_id, direction_changes, estimated_dates, target_position
            )
            
            # Verificar cada fecha estimada
            for date, target_position in all_dates:
                is_aspect, exact_date, position, speed, orb, movement, aspect_state = self.check_aspect_at_date(
                    planet_id, date, target_position, natal_id, aspect_type
                )
                
                if is_aspect:
                    # Añadir el tránsito a la lista
                    transits.append((
                        exact_date,
                        planet_id,
                        aspect_type,
                        natal_id,
                        movement,
                        aspect_state,
                        orb,
                        position
                    ))
    
    return transits

def filter_duplicate_transits(self, transit_dates):
    """
    Filtra tránsitos duplicados de manera inteligente.
    Versión mejorada que mantiene aspectos legítimos y elimina duplicados cercanos.
    
    Args:
        transit_dates: Lista de tuplas (fecha, planeta_id, aspecto, natal_id, movimiento, estado, orbe, posicion)
        
    Returns:
        Lista filtrada de tránsitos sin duplicados
    """
    # Paso 1: Filtrar aspectos a puntos que no son planetas o ángulos principales
    valid_transits = []
    for transit in transit_dates:
        date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position = transit
        
        # Incluir planetas y ángulos principales (ASC, MC)
        if isinstance(natal_id, int) or natal_id in ['ASC', 'MC']:
            valid_transits.append(transit)
    
    # Paso 2: Agrupar por combinación planeta-aspecto-natal
    transit_groups = {}
    
    # Ordenar por fecha para procesar cronológicamente
    sorted_transits = sorted(valid_transits, key=lambda x: x[0])
    
    for transit in sorted_transits:
        date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, position = transit
        
        # Clave base
        base_key = (planet_id, natal_id, aspect_type)
        
        # Determinar umbral de días según velocidad del planeta
        if planet_id in [chart.MERCURY, chart.VENUS]:
            day_threshold = 2.0  # 2 días para planetas rápidos (reducido de 3.0)
        elif planet_id in [chart.MARS, chart.JUPITER]:
            day_threshold = 3.0  # 3 días para planetas medios (reducido de 5.0)
        else:
            day_threshold = 5.0  # 5 días para planetas lentos (reducido de 10.0)
        
        # Reducir umbral si los movimientos son diferentes
        if movement == calc.RETROGRADE:
            day_threshold *= 0.5  # Reducir a la mitad para retrógrados
        
        # Buscar duplicados temporales
        found_match = False
        
        for key in list(transit_groups.keys()):
            existing_transit = transit_groups[key]
            existing_date = existing_transit[0]
            existing_planet_id, existing_natal_id, existing_aspect_type = key[:3]
            existing_movement = existing_transit[4]
            
            # Si es la misma combinación
            if (existing_planet_id == planet_id and 
                existing_natal_id == natal_id and 
                existing_aspect_type == aspect_type):
                
                # Verificar proximidad temporal
                date_diff = abs((date - existing_date).total_seconds()) / 86400.0  # Diferencia en días
                
                if date_diff <= day_threshold:
                    found_match = True
                    
                    # Si los movimientos son diferentes, mantener ambos
                    # Esto es importante para capturar aspectos cerca de cambios de dirección
                    if movement != existing_movement:
                        unique_key = base_key + (date.strftime('%Y-%m-%d-%H'), movement)
                        transit_groups[unique_key] = transit
                        found_match = False  # Seguir procesando
                        break
                    
                    # Mantener el de menor orbe
                    existing_orb = existing_transit[6]
                    if orb < existing_orb:
                        transit_groups[key] = transit
                    
                    break
        
        # Si no se encontró duplicado, añadir este tránsito
        if not found_match:
            unique_key = base_key + (date.strftime('%Y-%m-%d-%H'),)
            transit_groups[unique_key] = transit
    
    # Recopilar resultados filtrados
    filtered_transits = list(transit_groups.values())
    filtered_transits.sort(key=lambda x: x[0])  # Ordenar por fecha
    
    return filtered_transits

def convert_to_astro_events(self, transit_dates):
    """
    Convierte los datos de tránsitos a objetos AstroEvent.
    
    Args:
        transit_dates: Lista de tuplas (fecha, planeta_id, aspecto, natal_id, movimiento, estado, orbe, posicion)
        
    Returns:
        Lista de objetos AstroEvent
    """
    events = []
    
    for date, planet_id, aspect_type, natal_id, movement, aspect_state, orb, planet_position in transit_dates:
        # Obtener nombres para la descripción
        planet_name = PLANET_NAMES.get(planet_id, str(planet_id))
        
        # Manejar tanto planetas como ángulos natales
        if natal_id in PLANET_NAMES:
            natal_name = PLANET_NAMES[natal_id]
        else:
            natal_name = str(natal_id)  # Para ángulos como 'ASC', 'MC', etc.
            
        aspect_name = ASPECT_NAMES[aspect_type]
        movement_name = MOVEMENT_NAMES[movement]
        aspect_state_name = ASPECT_STATE[aspect_state]
        
        # Crear descripción del evento en el mismo formato que all_transits_parallel.py
        descripcion = f"{planet_name} por tránsito esta en {aspect_name} a tu {natal_name} Natal"
        
        # Obtener signo y grado para la posición del planeta
        planet_sign = AstronomicalConstants.get_sign_name(planet_position)
        planet_degree = planet_position % 30
        
        # Obtener signo y grado para la posición natal
        natal_position = self.natal_positions[natal_id]
        natal_sign = AstronomicalConstants.get_sign_name(natal_position)
        natal_degree = natal_position % 30
        
        # Formatear posiciones en formato de grados
        def format_position(degrees):
            whole_degrees = int(degrees)
            minutes_decimal = (degrees - whole_degrees) * 60
            minutes = int(minutes_decimal)
            seconds = int((minutes_decimal - minutes) * 60)
            return f"{whole_degrees}°{minutes}'{seconds}\""
        
        planet_position_str = f"{format_position(planet_degree)} {planet_sign}"
        natal_position_str = f"{format_position(natal_degree)} {natal_sign}"
        
        # Crear objeto AstroEvent
        event = AstroEvent(
            fecha_utc=date,
            tipo_evento=EventType.ASPECTO,
            descripcion=descripcion,
            planeta1=planet_name,
            planeta2=natal_name,
            longitud1=planet_position,  # Usar la posición exacta del planeta
            longitud2=natal_position,
            tipo_aspecto=aspect_name,
            orbe=orb,
            es_aplicativo=(aspect_state == calc.APPLICATIVE),
            metadata={
                'movimiento': movement_name,
                'estado': aspect_state_name,
                'posicion1': planet_position_str,
                'posicion2': natal_position_str
            }
        )
        events.append(event)
    
    return events

def calculate_all(self, start_date: datetime = None, end_date: datetime = None, planets_to_check=None) -> list:
    """
    Calcula todos los tránsitos para el período especificado usando el enfoque astronómico mejorado.
    Versión 2.0 con todas las mejoras implementadas.
    
    Args:
        start_date: Fecha inicial (default: 1 enero del año actual)
        end_date: Fecha final (default: 31 diciembre del año actual)
        planets_to_check: Lista de planetas a verificar (default: todos excepto Luna)
        
    Returns:
        Lista de eventos de tránsitos
    """
    # Si no se especifican fechas, usar el año actual completo con la zona horaria del usuario
    if not start_date:
        start_date = datetime(datetime.now().year, 1, 1, tzinfo=self.user_timezone)
    if not end_date:
        end_date = datetime(datetime.now().year, 12, 31, 23, 59, tzinfo=self.user_timezone)
    
    # Si no se especifican planetas, usar todos excepto Luna (que requiere un enfoque diferente)
    if not planets_to_check:
        planets_to_check = [
            chart.SUN,
            chart.MERCURY,
            chart.VENUS,
            chart.MARS,
            chart.JUPITER,
            chart.SATURN,
            chart.URANUS,
            chart.NEPTUNE,
            chart.PLUTO
        ]
    
    year = start_date.year
    
    # Iniciar el cálculo
    start_time = time.time()
    print("\nCalculando tránsitos con método astronómico v2.0...")
    
    # Para cada planeta, detectar cambios de dirección primero
    direction_changes = {}
    for planet_id in planets_to_check:
        direction_changes[planet_id] = self.detect_direction_changes(planet_id, start_date, end_date)
        print(f"Detectados {len(direction_changes[planet_id])} cambios de dirección para {PLANET_NAMES.get(planet_id, planet_id)}")
    
    # Procesar cada planeta en paralelo
    all_transits = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(self.find_transits_for_planet, planet, year, start_date, end_date) 
                  for planet in planets_to_check]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                planet_transits = future.result()
                all_transits.extend(planet_transits)
                print(f"Encontrados {len(planet_transits)} tránsitos para un planeta")
            except Exception as e:
                print(f"Error procesando planeta: {e}")
    
    # Ordenar por fecha
    all_transits.sort(key=lambda x: x[0])
    
    # Filtrar por rango de fechas si es necesario
    filtered_transits = [t for t in all_transits if start_date <= t[0] <= end_date]
    
    # Eliminar duplicados, manteniendo solo el más exacto para cada combinación
    filtered_transits = self.filter_duplicate_transits(filtered_transits)
    
    # Convertir a objetos AstroEvent
    all_events = self.convert_to_astro_events(filtered_transits)
    
    # Mostrar resumen
    elapsed = time.time() - start_time
    print(f"\nCálculo astronómico v2.0 completado en {elapsed:.2f} segundos")
    print(f"Total de eventos encontrados: {len(all_events)}")
    
    return all_events
