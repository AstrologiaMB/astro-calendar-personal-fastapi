"""
Factory para crear calculadores de tránsitos según el método requerido.
"""

class TransitsCalculatorFactory:
    @staticmethod
    def create_calculator(natal_data, calculator_type="standard", use_parallel=False, timezone_str="UTC"):
        """
        Crea un calculador de tránsitos según el método requerido.
        
        Args:
            natal_data: Diccionario con los datos natales del usuario
            calculator_type: Tipo de calculador ("standard", "astronomical_v3", "astronomical_v4", "progressed_moon", o "immanuel")
            use_parallel: Si es True, usa procesamiento paralelo (solo para standard)
            timezone_str: La zona horaria a usar para los eventos generados (para Standard/Parallel).
            
        Returns:
            Un calculador de tránsitos
        """
        # Nota: Se eliminaron las opciones "optimized", "astronomical", "astronomical_v2"
        if calculator_type == "astronomical_v3":
            from .astronomical_transits_calculator_v3 import AstronomicalTransitsCalculatorV3
            # V3 maneja su propia zona horaria internamente desde natal_data
            return AstronomicalTransitsCalculatorV3(natal_data)
        elif calculator_type == "astronomical_v4":
            from .astronomical_transits_calculator_v4 import AstronomicalTransitsCalculatorV4
            # V4 también maneja su propia zona horaria internamente
            return AstronomicalTransitsCalculatorV4(natal_data)
        elif calculator_type == "progressed_moon":
            from .progressed_moon_transits import ProgressedMoonTransitsCalculator
            # Este calculador obtiene la zona horaria desde natal_data internamente
            return ProgressedMoonTransitsCalculator(natal_data)
        elif calculator_type == "immanuel":
            from .transits_immanuel import ImmanuelTransitsCalculator
            # Asumimos que este también necesita la zona horaria
            return ImmanuelTransitsCalculator(natal_data, timezone_str=timezone_str)
        elif calculator_type == "vectorized":
            from .vectorized_transits_calculator import VectorizedTransitsCalculator
            # Vectorized v1 es "stateless" respecto a timezone (devuelve UTC), 
            # pero acepta natal_data estándar.
            return VectorizedTransitsCalculator(natal_data)
        else:  # standard (incluye paralelo)
            if use_parallel:
                from .all_transits_parallel import ParallelTransitsCalculator
                return ParallelTransitsCalculator(natal_data, timezone_str=timezone_str)
            else:
                from .all_transits import AllTransitsCalculator
                return AllTransitsCalculator(natal_data, timezone_str=timezone_str)
