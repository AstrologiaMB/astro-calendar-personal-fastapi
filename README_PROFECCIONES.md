# Profecciones Anuales

Este documento describe la implementación del cálculo de profecciones anuales en astrología.

## Método de Profección

Las profecciones anuales son una técnica de predicción astrológica tradicional donde cada signo representa un año de vida. El método consiste en:

1. Calcular la edad de la persona (años cumplidos)
2. Avanzar el Ascendente natal 30° por cada año de vida (1 signo = 1 año)
3. Determinar el signo profectado y el señor del año (regente del signo)

Por ejemplo, si una persona nació con Ascendente en Cáncer:
- Año 1: Ascendente en Cáncer (señor del año: Luna)
- Año 2: Ascendente en Leo (señor del año: Sol)
- Año 3: Ascendente en Virgo (señor del año: Mercurio)
- Y así sucesivamente...

## Implementación

Nuestra implementación calcula:

1. El señor del año actual y la casa profectada
2. La fecha exacta en que comenzó (último cumpleaños)
3. La fecha exacta en que terminará (próximo cumpleaños)
4. Cuántos días faltan para el cambio
5. Quién será el próximo señor del año

## Formatos de Salida

La información de profecciones se presenta de dos formas:

1. **Salida en Consola**: Muestra información detallada sobre la profección actual en un formato visualmente atractivo con bordes.

```
╔══════════════════════════════════════════════════════════╗
║                   PROFECCIONES ANUALES                   ║
╠══════════════════════════════════════════════════════════╣
║ Fecha de nacimiento: 26/12/1964 21:12 (Buenos Aires)     ║
║ Fecha de consulta:   01/01/2025                          ║
╠══════════════════════════════════════════════════════════╣
║ Edad actual:         60 años                             ║
║ Casa profectada:     Casa 1 en CÁNCER                    ║
║ SEÑOR DEL AÑO:       LUNA                                ║
╠══════════════════════════════════════════════════════════╣
║ Período activo:      26/12/2024 - 26/12/2025             ║
║ Días restantes:      359 días                            ║
║ Próximo señor:       SOL (Leo)                           ║
╚══════════════════════════════════════════════════════════╝
```

2. **Eventos en CSV**: Los cambios de señor del año se incluyen en el archivo CSV de eventos personales, con detalles sobre la casa profectada, la edad y el período de validez.

```csv
Fecha,Tipo,Descripción,Detalles
2024-12-26,PROFECCION,Cambio de Señor del Año: LUNA,"Casa 1 en Cáncer, Edad: 60 años, Período: 26/12/2024-26/12/2025"
2025-12-26,PROFECCION,Cambio de Señor del Año: SOL,"Casa 1 en Leo, Edad: 61 años, Período: 26/12/2025-26/12/2026"
```

## Comparación con AstroSeek

Nuestra implementación produce resultados consistentes con AstroSeek. Por ejemplo, para la carta natal del 26/12/1964:

- El 1 de enero de 2025 (a los 60 años), el señor del año es la Luna (regente de Cáncer)
- El señor del año cambia el 26 de diciembre de 2025 (cumpleaños 61)
- A partir de esa fecha, el señor del año será el Sol (regente de Leo)

## Notas Técnicas

- Utilizamos el sistema de casas de Signo Entero (Whole Sign), que es el sistema tradicional para profecciones
- Utilizamos los regentes tradicionales de los signos
- El cambio de señor del año ocurre exactamente en el cumpleaños
- El cálculo tiene en cuenta el año bisiesto y la zona horaria

## Uso en el Programa Principal

Para utilizar el calculador de profecciones en el programa principal:

1. Al ejecutar `main.py`, se preguntará si desea calcular profecciones anuales
2. Si responde afirmativamente, se mostrarán las profecciones para el año actual
3. Los eventos de cambio de señor del año se incluirán en el archivo CSV de eventos personales

## Consulta Directa

También puede ejecutar el script `test_profections.py` para consultar directamente las profecciones para fechas específicas:

```bash
python test_profections.py
```

Este script mostrará las profecciones para varias fechas de prueba, permitiendo verificar el funcionamiento del calculador.
