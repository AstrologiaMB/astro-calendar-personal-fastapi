# Comparación con Datos de AstroSeek (Hora Local)

Este documento compara los resultados del calculador de eclipses con los datos proporcionados por AstroSeek para los eclipses de 2025, considerando la hora local de Buenos Aires (UTC-3).

## Eclipses Lunares

### Eclipse Lunar del 14 de marzo de 2025

| Fuente | Fecha y Hora (Local) | Posición | Distancia al Nodo |
|--------|-------------------|----------|-------------------|
| AstroSeek | 2025-03-14 03:59 | Virgo 23°58' | No especificada |
| Calculador Original | 2025-03-14 03:54 | Virgo 23.95° | 3.4° |
| Calculador Preciso | 2025-03-14 03:58 | Virgo 23.99° | 3.4° |

**Análisis**: El calculador de alta precisión proporciona un tiempo local que difiere solo por 1 minuto del dato de AstroSeek, mientras que el calculador original difiere por 5 minutos. La posición zodiacal es prácticamente idéntica en los tres casos.

### Eclipse Lunar del 7 de septiembre de 2025

| Fuente | Fecha y Hora (Local) | Posición | Distancia al Nodo |
|--------|-------------------|----------|-------------------|
| AstroSeek | 2025-09-07 15:12 | Piscis 15°24' | No especificada |
| Calculador Original | 2025-09-07 15:08 | Piscis 15.39° | 3.0° |
| Calculador Preciso | 2025-09-07 15:11 | Piscis 15.42° | 2.9° |

**Análisis**: El calculador de alta precisión proporciona un tiempo local que difiere solo por 1 minuto del dato de AstroSeek, mientras que el calculador original difiere por 4 minutos. La posición zodiacal es muy similar en los tres casos, con una diferencia de menos de 0.2°.

## Eclipses Solares

### Eclipse Solar del 29 de marzo de 2025

| Fuente | Fecha y Hora (Local) | Posición | Distancia al Nodo |
|--------|-------------------|----------|-------------------|
| AstroSeek | 2025-03-29 07:48 | Aries 8°53' | No especificada |
| Calculador Original | 2025-03-29 07:57 | Aries 9.00° | 168.4° |
| Calculador Preciso | No detectado | - | - |

**Análisis**: El calculador original detecta este eclipse con un tiempo local que difiere por 9 minutos del dato de AstroSeek. La posición zodiacal es muy similar. El calculador de alta precisión no detecta este eclipse, probablemente porque está evaluando la visibilidad desde Buenos Aires y este eclipse parcial puede no ser visible desde esa ubicación.

### Eclipse Solar del 21 de septiembre de 2025

| Fuente | Fecha y Hora (Local) | Posición | Distancia al Nodo |
|--------|-------------------|----------|-------------------|
| AstroSeek | 2025-09-21 16:43 | Virgo 28°59' | No especificada |
| Calculador Original | 2025-09-21 16:54 | Virgo 29.09° | -10.7° |
| Calculador Preciso | No detectado | - | - |

**Análisis**: El calculador original detecta este eclipse con un tiempo local que difiere por 11 minutos del dato de AstroSeek. La posición zodiacal es muy similar. El calculador de alta precisión no detecta este eclipse, probablemente porque está evaluando la visibilidad desde Buenos Aires y este eclipse parcial puede no ser visible desde esa ubicación.

## Conclusiones

1. **Eclipses Lunares**: El calculador de alta precisión muestra una excelente concordancia con los datos de AstroSeek, con diferencias de tiempo local de solo 1 minuto. Esto representa una mejora significativa respecto al calculador original, que muestra diferencias de 4-5 minutos.

2. **Eclipses Solares**: El calculador original detecta los eclipses solares reportados por AstroSeek, aunque con diferencias de tiempo local de 9-11 minutos. El calculador de alta precisión no detecta estos eclipses, lo que sugiere que está aplicando criterios más estrictos de visibilidad local.

3. **Precisión General**: Para los eclipses lunares, que son visibles desde un área geográfica mucho más amplia que los eclipses solares, el calculador de alta precisión proporciona resultados más precisos y más cercanos a los datos de referencia de AstroSeek.

## Recomendaciones

1. **Para Eclipses Lunares**: Utilizar el calculador de alta precisión, ya que proporciona tiempos más precisos que concuerdan mejor con los datos de referencia.

2. **Para Eclipses Solares**: Si se requiere información sobre eclipses solares globales (independientemente de la visibilidad local), el calculador original puede ser más adecuado. Sin embargo, si se desea información precisa sobre la visibilidad local de los eclipses solares, sería necesario modificar el calculador de alta precisión para que reporte eclipses solares globales pero con indicadores claros de su visibilidad local.

3. **Mejora Futura**: Considerar la implementación de un modo "global" en el calculador de alta precisión que reporte todos los eclipses solares independientemente de su visibilidad local, similar al comportamiento del calculador original, pero manteniendo la mayor precisión temporal que ofrece el uso directo de Swiss Ephemeris.
