"""
Factory para crear calculadores de eclipses según las preferencias del usuario.
"""

class EclipseCalculatorFactory:
    @staticmethod
    def create_calculator(observer, use_precise=False, use_immanuel=False, timezone_str="UTC"):
        """
        Crea un calculador de eclipses según las preferencias del usuario.
        
        Args:
            observer: Objeto observer de PyEphem
            use_precise: Si es True, usa el calculador de alta precisión
            use_immanuel: Si es True, usa el calculador basado en Immanuel
            timezone_str: Zona horaria para conversión a hora local
            
        Returns:
            Un calculador de eclipses
        """
        if use_immanuel:
            from .eclipses_immanuel import ImmanuelEclipseCalculator
            return ImmanuelEclipseCalculator(observer, timezone_str)
        elif use_precise:
            from .eclipses_precise import PreciseEclipseCalculator
            return PreciseEclipseCalculator(observer, timezone_str)
        else:
            from .eclipses import EclipseCalculator
            return EclipseCalculator(observer, timezone_str)
