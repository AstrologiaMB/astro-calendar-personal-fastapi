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
