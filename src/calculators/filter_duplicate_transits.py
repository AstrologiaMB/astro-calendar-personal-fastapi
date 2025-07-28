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
