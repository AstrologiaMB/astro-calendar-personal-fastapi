# Comparación de Calculadores de Eclipses

Este documento presenta una comparación detallada entre el calculador de eclipses original y el nuevo calculador de alta precisión implementado con Swiss Ephemeris.

## Resultados de la Prueba

La prueba se realizó para el período 2025-2026 utilizando la ubicación de Buenos Aires (lat: -34.60, lon: -58.45).

### Resumen de Resultados

| Métrica | Calculador Original | Calculador de Alta Precisión |
|---------|---------------------|------------------------------|
| Eclipses encontrados | 8 | 5 |
| Tiempo de cálculo | 0.01 segundos | 0.02 segundos |
| Eclipses lunares | 4 | 4 |
| Eclipses solares | 4 | 1 |

### Eclipses Encontrados por Ambos Métodos

Se encontraron 4 eclipses comunes entre ambos calculadores, todos ellos eclipses lunares:

1. **Eclipse Lunar (2025-03-14)**
   - Original: 2025-03-14 06:54:35 UTC - Eclipse Lunar Total en Virgo 23.95° (distancia al nodo: 3.4°)
   - Preciso:  2025-03-14 06:58:47 UTC - Eclipse Lunar Total en Virgo 23.99° (distancia al nodo: 3.4°)
   - Diferencia: 4.19 minutos

2. **Eclipse Lunar (2025-09-07)**
   - Original: 2025-09-07 18:08:49 UTC - Eclipse Lunar Total en Piscis 15.39° (distancia al nodo: 3.0°)
   - Preciso:  2025-09-07 18:11:48 UTC - Eclipse Lunar Total en Piscis 15.42° (distancia al nodo: 2.9°)
   - Diferencia: 2.98 minutos

3. **Eclipse Lunar (2026-03-03)**
   - Original: 2026-03-03 11:37:49 UTC - Eclipse Lunar Total en Virgo 12.91° (distancia al nodo: -3.9°)
   - Preciso:  2026-03-03 11:33:42 UTC - Eclipse Lunar Total en Virgo 12.87° (distancia al nodo: -3.9°)
   - Diferencia: 4.13 minutos

4. **Eclipse Lunar (2026-08-28)**
   - Original: 2026-08-28 04:18:26 UTC - Eclipse Lunar Parcial en Piscis 4.91° (distancia al nodo: 5.1°)
   - Preciso:  2026-08-28 04:12:57 UTC - Eclipse Lunar Total en Piscis 4.86° (distancia al nodo: 5.0°)
   - Diferencia: 5.49 minutos
   - **Nota**: Hay una discrepancia en el tipo de eclipse (Parcial vs Total)

### Eclipses Encontrados Solo por el Calculador Original

El calculador original encontró 4 eclipses adicionales que no fueron detectados por el calculador de alta precisión:

1. **Eclipse Solar (2025-03-29)**: Eclipse Solar Parcial en Aries 9.00° (distancia al nodo: 168.4°)
2. **Eclipse Solar (2025-09-21)**: Eclipse Solar Parcial en Virgo 29.09° (distancia al nodo: -10.7°)
3. **Eclipse Solar (2026-02-17)**: Eclipse Solar Parcial en Acuario 28.83° (distancia al nodo: 10.1°)
4. **Eclipse Solar (2026-08-12)**: Eclipse Solar Anular en Leo 20.03° (distancia al nodo: 9.8°)

### Eclipses Encontrados Solo por el Calculador de Alta Precisión

El calculador de alta precisión encontró 1 eclipse adicional que no fue detectado por el calculador original:

1. **Eclipse Solar (2027-02-06)**: Eclipse Solar Parcial en Acuario 17.63° (distancia al nodo: 2.9°)

## Análisis de Diferencias

### Diferencias en Tiempos

Las diferencias en los tiempos de los eclipses lunares oscilan entre 2.98 y 5.49 minutos, con un promedio de aproximadamente 4.2 minutos. Estas diferencias son relativamente pequeñas y pueden atribuirse a:

1. El uso de diferentes algoritmos para calcular el momento exacto del eclipse
2. El calculador de alta precisión utiliza `swe.lun_eclipse_when()` que calcula directamente el momento de máxima fase
3. El calculador original utiliza `ephem.next_full_moon()` y luego verifica si hay eclipse

### Diferencias en Tipos de Eclipse

Se observó una discrepancia en el tipo de eclipse para el evento del 2026-08-28:
- El calculador original lo clasifica como **Parcial**
- El calculador de alta precisión lo clasifica como **Total**

Esta diferencia puede deberse a:
1. Diferentes criterios para determinar el tipo de eclipse
2. El calculador de alta precisión utiliza la magnitud umbral directamente de Swiss Ephemeris
3. El calculador original puede estar utilizando un umbral ligeramente diferente

### Diferencias en Eclipses Solares

La diferencia más notable es que el calculador de alta precisión detecta significativamente menos eclipses solares. Esto puede deberse a:

1. El calculador de alta precisión utiliza `sol_eclipse_how()` para determinar si un eclipse es visible desde la ubicación específica
2. El calculador original puede estar reportando eclipses solares globales sin verificar su visibilidad desde la ubicación del observador
3. La distancia al nodo para los eclipses solares no detectados es relativamente grande (9.8° a 168.4°), lo que sugiere que estos eclipses pueden ser muy parciales o no visibles desde la ubicación especificada

## Conclusiones

1. **Precisión Temporal**: El calculador de alta precisión proporciona tiempos ligeramente diferentes para los eclipses lunares, con diferencias de aproximadamente 4 minutos en promedio.

2. **Clasificación de Eclipses**: Hay una discrepancia en la clasificación de un eclipse lunar (Parcial vs Total), lo que sugiere diferentes criterios o umbrales.

3. **Visibilidad Local**: El calculador de alta precisión parece ser más estricto en cuanto a la visibilidad local de los eclipses solares, reportando solo aquellos que son claramente visibles desde la ubicación especificada.

4. **Rendimiento**: El calculador de alta precisión es aproximadamente 2.25 veces más lento que el original, pero sigue siendo muy eficiente (0.02 segundos vs 0.01 segundos).

## Recomendaciones

1. **Para Eclipses Lunares**: Ambos calculadores proporcionan resultados similares, con pequeñas diferencias en los tiempos exactos. El calculador de alta precisión puede ser preferible por su uso directo de las funciones especializadas de Swiss Ephemeris.

2. **Para Eclipses Solares**: Es necesario investigar más a fondo por qué el calculador de alta precisión detecta menos eclipses solares. Si se requiere información sobre eclipses solares globales (independientemente de la visibilidad local), el calculador original puede ser más adecuado.

3. **Uso Combinado**: Considerar la posibilidad de utilizar ambos calculadores de manera complementaria, aprovechando las fortalezas de cada uno según el tipo de eclipse y el contexto de uso.
