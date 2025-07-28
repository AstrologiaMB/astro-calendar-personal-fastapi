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
