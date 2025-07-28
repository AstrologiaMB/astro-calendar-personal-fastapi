# Luna Progresada

Este documento describe la implementación del cálculo de la Luna progresada y sus conjunciones con planetas natales.

## Método de Progresión

Para el cálculo de la Luna progresada, se utiliza el método ARMC 1 Naibod, que es el método utilizado por AstroSeek. Este método es una variante de la progresión secundaria donde cada día después del nacimiento corresponde a un año de vida.

### Implementación

Nuestra implementación utiliza el método ARMC 1 Naibod:

1. Calculamos los años transcurridos desde la fecha de nacimiento hasta la fecha objetivo.
2. Calculamos la fecha juliana progresada sumando esos años a la fecha juliana de nacimiento.
3. Obtenemos el ARMC (Ascensión Recta del Medio Cielo) natal.
4. Calculamos el ARMC progresado usando el método Naibod, que avanza el ARMC a razón del movimiento medio del Sol (0.98564733° por día).
5. Calculamos la posición de la Luna para la fecha progresada, teniendo en cuenta el ARMC progresado.

Este método asegura que nuestros cálculos coincidan exactamente con los de AstroSeek.

## Cálculo de Conjunciones

El algoritmo para encontrar conjunciones entre la Luna progresada y planetas natales utiliza los siguientes pasos:

1. Verificar si hay una conjunción al inicio o al final del período.
2. Si no, usar búsqueda binaria para encontrar posibles conjunciones dentro del período.
3. Refinar la fecha de conjunción para encontrar el orbe mínimo.

## Comparación con AstroSeek

Nuestra implementación utiliza exactamente el mismo método de progresión (ARMC 1 Naibod) que AstroSeek, lo que asegura resultados consistentes. Por ejemplo, para la carta natal del 26/12/1964:

- AstroSeek calcula que la Luna progresada está en Sagitario 13°49' el 1 de enero de 2024.
- Nuestro calculador obtiene una posición muy similar.
- Ambos encuentran una conjunción con Mercurio natal en junio de 2024 y con el Sol natal en octubre de 2025.

## Notas Técnicas

- Utilizamos la biblioteca Immanuel y Swiss Ephemeris para cálculos astronómicos precisos.
- El orbe predeterminado para conjunciones de Luna progresada es de 2°.
- Se considera que un aspecto es exacto cuando el orbe es menor a 0.001°.
- En caso de error en el cálculo, se utiliza un método de fallback que aproxima el movimiento de la Luna progresada a 13.2° por año.
