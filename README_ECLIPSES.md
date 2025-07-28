# Calculador de Eclipses de Alta Precisión

Este módulo proporciona un calculador de eclipses de alta precisión que utiliza exclusivamente Swiss Ephemeris para determinar con exactitud los tiempos y características de eclipses solares y lunares.

## Características

- Cálculo preciso de eclipses solares y lunares utilizando las funciones especializadas de Swiss Ephemeris
- Determinación exacta del momento de máxima fase del eclipse
- Clasificación precisa de tipos de eclipses basada en magnitud y flags de Swiss Ephemeris
- Cálculo de distancia al nodo lunar para cada eclipse
- Integración con el sistema existente a través de un patrón Factory

## Mejoras respecto al calculador original

El nuevo calculador de eclipses ofrece varias mejoras respecto al calculador original:

1. **Mayor precisión temporal**: Utiliza las funciones especializadas de Swiss Ephemeris (`swe.lun_eclipse_when()` y `swe.sol_eclipse_when_loc()`) que calculan directamente el momento de máxima fase del eclipse, en lugar de verificar si hay eclipses en momentos de luna llena/nueva.

2. **Determinación más precisa del tipo de eclipse**:
   - Para eclipses lunares: Basada en la magnitud real del eclipse (fracción del diámetro lunar cubierta por la umbra)
   - Para eclipses solares: Basada en los flags específicos de Swiss Ephemeris que indican el tipo exacto de eclipse

3. **Cálculo directo**: Elimina pasos intermedios y aproximaciones, utilizando directamente las funciones especializadas de Swiss Ephemeris.

## Uso

Para utilizar el nuevo calculador de eclipses, se puede usar la clase `EclipseCalculatorFactory`:

```python
from src.calculators.eclipse_calculator_factory import EclipseCalculatorFactory

# Crear un calculador de eclipses de alta precisión
calculator = EclipseCalculatorFactory.create_calculator(observer, use_precise=True)

# Calcular eclipses
eclipses = calculator.calculate_eclipses(start_date, end_date)
```

## Comparación con el calculador original

Se incluye un script de prueba (`test_precise_eclipses.py`) que compara los resultados del calculador original con el calculador de alta precisión. Este script:

1. Calcula los eclipses para un período específico usando ambos calculadores
2. Muestra los resultados de ambos calculadores
3. Compara el número de eclipses encontrados
4. Compara los tiempos de cálculo
5. Analiza las diferencias en las fechas y tipos de eclipses

Para ejecutar la comparación:

```bash
python test_precise_eclipses.py
```

## Implementación

El nuevo calculador está implementado en el archivo `src/calculators/eclipses_precise.py` y sigue la misma interfaz que el calculador original, lo que permite intercambiarlos fácilmente.

La clase `EclipseCalculatorFactory` en `src/calculators/eclipse_calculator_factory.py` proporciona un método para crear el calculador adecuado según la precisión requerida.

## Notas técnicas

- El calculador de alta precisión utiliza exclusivamente Swiss Ephemeris para los cálculos críticos, aunque sigue utilizando PyEphem para calcular elevación y azimut.
- La conversión de tiempo juliano a datetime se realiza utilizando `swe.jdut1_to_utc()` para mayor precisión.
- El cálculo de la distancia al nodo lunar se realiza de manera similar al calculador original para mantener la compatibilidad en la presentación de resultados.
