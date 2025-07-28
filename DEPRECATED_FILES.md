# 🗑️ Archivos Deprecated - Calendario Astrológico Personal

**Fecha de creación**: 27 de junio de 2025  
**Propósito**: Documentar archivos que ya no se utilizan en el sistema actual

## ❌ Archivos Completamente Deprecated

### Scripts y Archivos Legacy

#### `main.py`
- **Estado**: ❌ **DEPRECATED**
- **Reemplazado por**: `app.py` (microservicio FastAPI)
- **Razón**: El proyecto se transformó de script interactivo a microservicio REST API
- **Fecha de deprecación**: Junio 2025
- **Acción recomendada**: Mantener solo como referencia histórica

#### `LM`
- **Estado**: ❌ **DEPRECATED**
- **Razón**: Archivo legacy sin función aparente en el sistema actual
- **Fecha de deprecación**: Junio 2025
- **Acción recomendada**: Eliminar en futuras versiones

#### `start_with_original_env.sh`
- **Estado**: ❌ **DEPRECATED**
- **Reemplazado por**: `start_robust.sh`
- **Razón**: Script de inicio mejorado con mejor manejo de errores
- **Fecha de deprecación**: Junio 2025
- **Acción recomendada**: Usar `start_robust.sh`

#### `start.sh`
- **Estado**: ⚠️ **LEGACY** (funcional pero no recomendado)
- **Reemplazado por**: `start_robust.sh`
- **Razón**: Versión básica sin manejo robusto de errores
- **Acción recomendada**: Usar `start_robust.sh` para producción

### Archivos de Debug y Logs Temporales

#### `debug_natal_data.py`
- **Estado**: ❌ **DEPRECATED**
- **Razón**: Script temporal de debug, ya no necesario
- **Fecha de deprecación**: Junio 2025
- **Acción recomendada**: Eliminar

#### `output.txt`
- **Estado**: ❌ **DEPRECATED**
- **Razón**: Output temporal de debug
- **Fecha de deprecación**: Junio 2025
- **Acción recomendada**: Eliminar

#### `microservice.log`
- **Estado**: ❌ **DEPRECATED**
- **Razón**: Log temporal del desarrollo del microservicio
- **Fecha de deprecación**: Junio 2025
- **Acción recomendada**: Eliminar

## 🔄 Calculadores Legacy (Mantener por Compatibilidad)

### Versiones Anteriores del Calculador Principal

#### `src/calculators/astronomical_transits_calculator.py` (V1)
- **Estado**: 🔄 **LEGACY**
- **Reemplazado por**: `astronomical_transits_calculator_v4.py`
- **Razón**: V4 incluye cache de ephemeris (20% más rápido)
- **Acción recomendada**: Mantener por compatibilidad, usar V4 por defecto

#### `src/calculators/astronomical_transits_calculator_v2.py` (V2)
- **Estado**: 🔄 **LEGACY**
- **Reemplazado por**: `astronomical_transits_calculator_v4.py`
- **Razón**: V4 incluye mejoras de rendimiento y cache
- **Acción recomendada**: Mantener por compatibilidad, usar V4 por defecto

#### `src/calculators/astronomical_transits_calculator_v3.py` (V3)
- **Estado**: 🔄 **LEGACY**
- **Reemplazado por**: `astronomical_transits_calculator_v4.py`
- **Razón**: V4 es la versión actual con todas las optimizaciones
- **Acción recomendada**: Mantener por compatibilidad, usar V4 por defecto

### ✅ **Calculador Actual**
- **`src/calculators/astronomical_transits_calculator_v4.py`** - ✅ **VERSIÓN ACTUAL**

## ⚠️ Archivos Explícitamente Marcados como Deprecated

### Calculadores de Conjunciones Lunares

#### `src/calculators/sun_fullmoon_conjunctions_deprecated.py`
- **Estado**: ⚠️ **DEPRECATED** (marcado en el nombre)
- **Razón**: Funcionalidad integrada en otros calculadores
- **Fecha de deprecación**: Anterior a junio 2025
- **Acción recomendada**: Mantener solo como referencia

#### `src/calculators/sun_newmoon_conjunctions_deprecated.py`
- **Estado**: ⚠️ **DEPRECATED** (marcado en el nombre)
- **Razón**: Funcionalidad integrada en otros calculadores
- **Fecha de deprecación**: Anterior a junio 2025
- **Acción recomendada**: Mantener solo como referencia

## 🧪 Archivos de Testing y Desarrollo

### Scripts de Prueba Múltiples
Los siguientes archivos de test pueden ser consolidados en el futuro:

- `test_adaptive.py`
- `test_compare_standard_parallel.py`
- `test_compare_standard_progressed.py`
- `test_dynamic_endpoint.py`
- `test_eclipse_calculators.py`
- `test_house_transits.py`
- `test_parallel_only.py`
- `test_precise_eclipses.py`
- `test_profections.py`
- `test_progressed_moon_position.py`
- `test_progressed_moon.py`
- `test_transits_calculators.py`
- `test_transits_performance.py`

**Estado**: 🧪 **TESTING** (funcionales pero pueden ser consolidados)  
**Acción recomendada**: Revisar y consolidar en una suite de tests unificada

### Archivos de Datos de Prueba

- `test_events.csv`
- `test_natal_data_COMPLETO.json`
- `test_natal_data_CORREGIDO.json`
- `test_natal_data.json`

**Estado**: 🧪 **TESTING** (necesarios para pruebas)  
**Acción recomendada**: Mantener organizados en directorio `tests/data/`

## 📊 Resumen por Estado

| Estado | Cantidad | Acción Recomendada |
|--------|----------|-------------------|
| ❌ **DEPRECATED** | 6 archivos | Eliminar en futuras versiones |
| 🔄 **LEGACY** | 4 archivos | Mantener por compatibilidad |
| ⚠️ **MARKED DEPRECATED** | 2 archivos | Mantener como referencia |
| 🧪 **TESTING** | 15+ archivos | Consolidar y organizar |

## 🔍 Cómo Identificar Archivos Deprecated

### Indicadores de Archivos Deprecated:
1. **Nombre contiene "deprecated"** - Explícitamente marcado
2. **No se importa en `app.py`** - No usado por el microservicio actual
3. **Reemplazado por versión superior** - V1, V2, V3 → V4
4. **Scripts de debug temporales** - Archivos de desarrollo
5. **Logs y outputs temporales** - Archivos generados durante desarrollo

### Verificación Rápida:
```bash
# Buscar archivos que contienen "deprecated" en el nombre
find . -name "*deprecated*" -type f

# Buscar archivos que no se han modificado en mucho tiempo
find . -type f -name "*.py" -not -path "./venv/*" -mtime +30
```

## 📝 Notas Importantes

1. **No eliminar sin verificar**: Algunos archivos legacy pueden ser necesarios para compatibilidad
2. **Mantener historial Git**: Los archivos deprecated contienen historial valioso del desarrollo
3. **Documentar cambios**: Cualquier eliminación debe documentarse en el CHANGELOG
4. **Testing antes de eliminar**: Verificar que el sistema funciona sin los archivos deprecated

---

**Última actualización**: 27 de junio de 2025  
**Versión del sistema**: 3.2.0 (feature/house-transits)  
**Mantenido por**: Documentación automática del proyecto
