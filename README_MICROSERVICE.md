# 🚀 Microservicio Personal Calendar - Guía Esencial

**Estado**: ✅ **FUNCIONANDO COMPLETAMENTE** (Diciembre 2025)  
**Puerto**: 8004  
**Versión**: 2.0.0 con Tránsitos por Casas

## 🎯 Inicio Rápido

### Comando Recomendado
```bash
./start_robust.sh
```

Este script automáticamente:
- ✅ Verifica el entorno virtual
- ✅ Instala dependencias
- ✅ Valida configuración crítica
- ✅ Inicia el microservicio en puerto 8004

### Verificación
```bash
curl http://localhost:8004/health
# Respuesta esperada: {"status":"healthy",...}
```

## 📊 Características Implementadas

### ✨ **NUEVO: Tránsitos por Casas**
- **Estado actual** de Júpiter, Saturno, Urano, Neptuno, Plutón
- **Tiempo real** usando `datetime.now()`
- **Casas natales** con significados incluidos
- **Visualización** en tarjeta especial del frontend

### 🔮 Eventos Calculados
- **Tránsitos**: ~150-180 eventos (aspectos exactos/estacionarios)
- **Luna Progresada**: ~12 eventos (conjunciones)
- **Profecciones**: 1 evento (casa anual)
- **Fases Lunares**: ~24 eventos (nuevas/llenas)
- **Eclipses**: ~4-6 eventos (solares/lunares)
- **Aspectos Lunares**: ~20-30 eventos
- **Tránsitos por Casas**: 1 evento (estado actual)

## 🔧 Configuración Técnica

### Dependencias Críticas Verificadas
```
Python: 3.13
FastAPI: 0.115.12
Immanuel: 1.4.3 (con ephemeris.planet)
Swiss Ephemeris: 2.10.3.2
```

### Calculador Principal
- **V4 con Caching**: ~20% más rápido que versiones anteriores
- **Precisión**: Swiss Ephemeris para máxima exactitud
- **Filtrado**: Solo aspectos exactos o estacionarios
- **Paralelización**: Múltiples planetas simultáneamente

## 📡 Endpoints Principales

### Cálculo Dinámico (Recomendado)
```bash
POST /calculate-personal-calendar-dynamic
```
Genera carta natal automáticamente desde datos básicos.

### Monitoreo
```bash
GET /health          # Estado del servicio
GET /info            # Información detallada  
GET /docs            # Documentación interactiva
```

## 🧪 Prueba Completa

```bash
curl -X POST http://localhost:8004/calculate-personal-calendar-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "birth_date": "1990-01-15",
    "birth_time": "14:30",
    "location": {
      "latitude": -34.6037,
      "longitude": -58.3816,
      "name": "Buenos Aires",
      "timezone": "America/Argentina/Buenos_Aires"
    },
    "year": 2025
  }'
```

**Resultado esperado**: ~200+ eventos calculados en 10-15 segundos

## 🔍 Solución de Problemas

### Error: "No module named 'fastapi'"
```bash
# El entorno virtual no está activado
./start_robust.sh  # Usa el script robusto
```

### Error: Puerto 8004 en uso
```bash
# El script robusto lo maneja automáticamente
./start_robust.sh
```

### Error: No aparecen tránsitos por casas
1. Verificar que los datos natales incluyan casas
2. Comprobar que se use el calculador V4
3. Revisar logs para mensajes de debug

## 📈 Rendimiento

### Tiempos Típicos
- **Cálculo completo**: 10-15 segundos
- **Tránsitos V4**: 8-12 segundos  
- **Otros eventos**: 2-3 segundos
- **Health check**: <100ms

### Optimizaciones V4
- **Caching de efemérides**: Reduce cálculos redundantes
- **Búsqueda binaria**: Aspectos exactos precisos
- **Muestreo adaptativo**: Densidad variable por planeta
- **Filtrado inteligente**: Solo eventos relevantes

## 📚 Documentación Completa

Para información detallada, consultar:

- **[README.md](README.md)** - Visión general del proyecto
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Instalación paso a paso
- **[FEATURES.md](FEATURES.md)** - Características completas
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Referencia de API
- **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios

## 🎯 Estado Actual (Diciembre 2025)

### ✅ Funcionando Completamente
- Microservicio FastAPI estable
- Calculador V4 optimizado
- Tránsitos por casas implementados
- Frontend React integrado
- Documentación actualizada

### 📊 Estadísticas de Uso
- **Eventos por año**: 200-250 típicamente
- **Precisión**: ±1 minuto para aspectos exactos
- **Memoria**: <100MB durante cálculo
- **Uptime**: 99%+ en desarrollo

---

**Para soporte detallado**: Consultar la documentación completa en los archivos README_*.md  
**Última actualización**: Diciembre 2025  
**Próxima revisión**: Enero 2026
