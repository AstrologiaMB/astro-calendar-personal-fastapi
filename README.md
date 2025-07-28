# 🌟 Calendario Astrológico Personal - Sistema Completo

**Estado**: ✅ **FUNCIONANDO COMPLETAMENTE** (Junio 2025)  
**Versión**: 3.2 con Microservicio FastAPI + Frontend React

Un sistema completo de astrología personal que calcula y presenta eventos astrológicos en tiempo real a través de una interfaz web moderna.

## 🎯 Características Principales

### ✨ **NUEVO: Tránsitos de Largo Plazo en Tiempo Real**
- **Estado actual de planetas lentos**: Júpiter, Saturno, Urano, Neptuno, Plutón
- **Luna progresada**: Signo, grado y casa natal actual (permanece ~2.5 años por signo)
- **Visualización en tiempo real** de qué casa natal están transitando
- **Significados de casas** incluidos para interpretación inmediata
- **Tarjeta especial** en el frontend con diseño distintivo

### 🔮 Eventos Astrológicos Calculados
- **Tránsitos Planetarios**: Conjunciones, oposiciones, cuadraturas exactas
- **Luna Progresada**: Conjunciones con planetas natales
- **Profecciones Anuales**: Sistema de casas por edad
- **Fases Lunares**: Lunas nuevas y llenas con aspectos natales
- **Eclipses**: Solares y lunares con análisis de casas
- **Aspectos Lunares**: Conjunciones de fases lunares con planetas natales

### 🚀 Tecnología
- **Backend**: FastAPI + Swiss Ephemeris + Immanuel
- **Frontend**: React/TypeScript + Tailwind CSS
- **Cálculos**: Precisión astronómica con caching optimizado
- **Tiempo Real**: Datos actualizados automáticamente

## 📋 Inicio Rápido

### 1. Iniciar el Microservicio
```bash
# Opción recomendada (script automático)
./start_robust.sh

# O manualmente
source venv/bin/activate
python app.py
```

### 2. Acceder al Frontend
- **URL Principal**: http://localhost:3000 (sidebar-fastapi)
- **API Docs**: http://localhost:8004/docs
- **Health Check**: http://localhost:8004/health

### 3. Ver Tránsitos por Casas
1. Navega al **Calendario Personal** en el frontend
2. La tarjeta **"Estado Actual de Tránsitos por Casas"** aparece automáticamente
3. Muestra los 5 planetas lentos con sus casas actuales y significados

## 🏗️ Arquitectura del Sistema

```
astro-calendar-personal-fastapi/     # Microservicio Backend
├── app.py                          # FastAPI application
├── src/calculators/                # Motores de cálculo
│   ├── astronomical_transits_calculator_v4.py  # ⭐ Calculador principal
│   ├── natal_chart.py              # Generación de cartas natales
│   ├── profections_calculator.py   # Profecciones anuales
│   └── ...
├── start_robust.sh                 # Script de inicio automático
└── requirements.txt                # Dependencias Python

sidebar-fastapi/                    # Frontend React
├── components/
│   ├── calendario-personal.tsx     # ⭐ Componente principal
│   └── evento-astrologico.tsx      # ⭐ Renderizado de eventos
└── ...
```

## 🔧 Configuración Técnica

### Dependencias Críticas Verificadas
- **Python**: 3.13
- **FastAPI**: 0.115.12
- **Immanuel**: 1.4.3 (con ephemeris.planet)
- **Swiss Ephemeris**: 2.10.3.2
- **React**: 18+ con TypeScript

### Puertos y Servicios
- **Microservicio**: Puerto 8004
- **Frontend**: Puerto 3000
- **Base de datos**: No requerida (cálculos en tiempo real)

## 📊 Endpoints API Principales

### Cálculo Dinámico (Recomendado)
```bash
POST /calculate-personal-calendar-dynamic
```
Genera carta natal automáticamente desde datos básicos de nacimiento.

### Cálculo con Carta Previa (Legacy)
```bash
POST /calculate-personal-calendar
```
Usa carta natal pre-calculada.

### Monitoreo
```bash
GET /health          # Estado del servicio
GET /info            # Información detallada
GET /docs            # Documentación interactiva
```

## 🎨 Interfaz de Usuario

### Calendario Personal
- **Vista semanal** con eventos diarios
- **Tarjeta especial** para tránsitos por casas (arriba)
- **Navegación** por fechas con selector de mes/semana
- **Filtros automáticos** por tipo de evento

### Tránsitos por Casas
- **Diseño distintivo** con gradiente púrpura/índigo
- **Símbolos planetarios** (♃ ♄ ♅ ♆ ♇)
- **Información completa**: Casa + Significado
- **Actualización en tiempo real**

## 🧪 Prueba Rápida

```bash
# Verificar que el microservicio funciona
curl -X GET http://localhost:8004/health

# Calcular eventos para datos de prueba
curl -X POST http://localhost:8004/calculate-personal-calendar-dynamic \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Usuario Prueba",
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

**Respuesta esperada**: ~200+ eventos calculados exitosamente

## 📚 Documentación Adicional

- **[📚 Índice de Documentación](DOCUMENTATION_INDEX.md)** - Guía para navegar toda la documentación
- **[Guía de Instalación](SETUP_GUIDE.md)** - Configuración paso a paso
- **[Características Completas](FEATURES.md)** - Lista detallada de funcionalidades
- **[API Documentation](API_DOCUMENTATION.md)** - Referencia completa de endpoints
- **[Microservicio](README_MICROSERVICE.md)** - Guía específica del backend
- **[Changelog](CHANGELOG.md)** - Historial de cambios recientes

## 🔍 Solución de Problemas

### Error: "No module named 'fastapi'"
```bash
# Activar entorno virtual
source venv/bin/activate
pip install -r requirements.txt
```

### Error: Puerto 8004 en uso
```bash
# Liberar puerto
kill $(lsof -ti:8004)
./start_robust.sh
```

### Frontend no muestra tránsitos por casas
1. Verificar que el microservicio esté ejecutándose
2. Comprobar que los datos natales incluyan información de casas
3. Revisar la consola del navegador para errores

## 🤝 Contribución

Este proyecto está en desarrollo activo. Las características principales están implementadas y funcionando:

- ✅ Microservicio FastAPI completo
- ✅ Frontend React integrado
- ✅ Tránsitos por casas en tiempo real
- ✅ Múltiples tipos de eventos astrológicos
- ✅ Interfaz de usuario moderna

## 📞 Soporte

Para problemas o preguntas:
1. Revisar la documentación específica en los archivos README_*.md
2. Verificar el estado del microservicio con `/health`
3. Consultar los logs del sistema para errores específicos

---

**Última actualización**: Junio 2025  
**Estado**: Sistema completamente funcional con tránsitos por casas implementados
