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
