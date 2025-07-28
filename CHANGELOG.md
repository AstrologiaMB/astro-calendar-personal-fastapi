# Changelog - Calendario Astrológico Personal

Todas las mejoras y cambios importantes del proyecto.

## [Unreleased]

### Added
- Pendiente: Documentación completa de la API
- Pendiente: Tests automatizados para todos los calculadores

## [3.2.0] - 2025-06-27

### Added
- **Documentación de Archivos Deprecated**: Nuevo archivo `DEPRECATED_FILES.md` con clasificación completa
  - Identificación de 6 archivos completamente deprecated
  - Documentación de 4 calculadores legacy (V1-V3)
  - Guía para identificar archivos obsoletos
  - Recomendaciones de limpieza del proyecto

### Changed
- **Documentación Actualizada**: Fechas corregidas de "Diciembre 2025" a "Junio 2025"
- **DOCUMENTATION_INDEX.md**: Agregada referencia al nuevo archivo de deprecated
- **Estado del Proyecto**: Documentación sincronizada con branch `feature/house-transits`

### Technical
- Análisis completo del historial Git para identificar archivos obsoletos
- Clasificación por estado: DEPRECATED, LEGACY, MARKED DEPRECATED, TESTING
- Verificación de integración con microservicio FastAPI

## [3.1.0] - 2025-06-19

### Added
- **Luna Progresada en Tránsitos de Largo Plazo**: Integrada en la tarjeta de planetas lentos
  - Muestra signo actual, grado y casa natal donde está transitando
  - Cálculo usando método ARMC 1 Naibod (compatible con AstroSeek)
  - Actualización automática semana a semana
  - Visualización integrada con planetas lentos en una sola tarjeta

### Changed
- **Tarjeta de Tránsitos**: Renombrada de "Tránsitos por Casas" a "Tránsitos de Largo Plazo"
- **Datos Estructurados**: API ahora envía `house_transits` con información estructurada
- **Frontend**: Componente `evento-astrologico.tsx` actualizado para manejar luna progresada

### Technical
- Agregado método `_calculate_progressed_moon_position()` en AstronomicalTransitsCalculatorV4
- Agregado método `get_current_house_for_planet_position()` para cálculo de casas por posición
- Modificado `calculate_house_transits_state()` para incluir luna progresada
- Actualizado modelo de respuesta API con campo `house_transits`
