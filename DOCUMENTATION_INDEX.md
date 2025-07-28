# 📚 Índice de Documentación - Calendario Astrológico Personal

**Guía completa para navegar toda la documentación del proyecto**

## 🎯 ¿Qué necesitas?

### 🚀 **Empezar a usar el sistema**
1. **[README.md](README.md)** - Visión general y inicio rápido
2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Instalación paso a paso
3. **[README_MICROSERVICE.md](README_MICROSERVICE.md)** - Guía esencial del backend

### 🔍 **Entender las características**
- **[FEATURES.md](FEATURES.md)** - Lista completa de funcionalidades
- **[CHANGELOG.md](CHANGELOG.md)** - Qué hay de nuevo

### 🛠️ **Desarrollar o integrar**
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Referencia completa de la API
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Configuración técnica detallada
- **[DEPRECATED_FILES.md](DEPRECATED_FILES.md)** - Archivos obsoletos y legacy

### 🐛 **Solucionar problemas**
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Sección "Solución de Problemas"
- **[README_MICROSERVICE.md](README_MICROSERVICE.md)** - Troubleshooting del backend

## 📋 Documentación por Archivo

### 📖 [README.md](README.md)
**Propósito**: Punto de entrada principal del proyecto
**Contiene**:
- Descripción general del sistema
- Características principales (incluyendo tránsitos por casas)
- Arquitectura del sistema
- Comandos de inicio rápido
- Enlaces a documentación específica

**Ideal para**: Primera visita al proyecto, overview general

---

### 🚀 [SETUP_GUIDE.md](SETUP_GUIDE.md)
**Propósito**: Guía completa de instalación y configuración
**Contiene**:
- Requisitos del sistema
- Instalación paso a paso (backend + frontend)
- Verificación de la instalación
- Configuración avanzada
- Solución de problemas comunes

**Ideal para**: Configurar el sistema desde cero, resolver problemas de instalación

---

### 🌟 [FEATURES.md](FEATURES.md)
**Propósito**: Documentación detallada de todas las características
**Contiene**:
- Tránsitos por casas (nueva característica)
- Todos los tipos de eventos astrológicos
- Interfaz de usuario
- Tecnología y rendimiento
- Configuración y personalización

**Ideal para**: Entender qué puede hacer el sistema, planificar uso

---

### 📡 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
**Propósito**: Referencia completa de la API REST
**Contiene**:
- Todos los endpoints disponibles
- Formatos de request/response
- Ejemplos de uso (cURL, JavaScript, Python)
- Códigos de error
- Parámetros de configuración

**Ideal para**: Desarrolladores, integración con otros sistemas

---

### 🚀 [README_MICROSERVICE.md](README_MICROSERVICE.md)
**Propósito**: Guía esencial y rápida del microservicio
**Contiene**:
- Comando de inicio recomendado
- Características implementadas
- Configuración técnica
- Pruebas rápidas
- Troubleshooting específico del backend

**Ideal para**: Administrar el microservicio, diagnóstico rápido

---

### 📝 [CHANGELOG.md](CHANGELOG.md)
**Propósito**: Historial completo de cambios y versiones
**Contiene**:
- Nuevas características por versión
- Correcciones de bugs
- Mejoras técnicas
- Estadísticas de desarrollo
- Roadmap futuro

**Ideal para**: Entender la evolución del proyecto, qué hay de nuevo

---

### 📚 [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) (este archivo)
**Propósito**: Navegación y guía de toda la documentación
**Contiene**:
- Índice por necesidad
- Descripción de cada archivo
- Flujos de lectura recomendados

**Ideal para**: Encontrar la documentación correcta rápidamente

## 🔄 Flujos de Lectura Recomendados

### 👤 **Usuario Nuevo**
1. **[README.md](README.md)** - Entender qué es el proyecto
2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Instalar y configurar
3. **[FEATURES.md](FEATURES.md)** - Explorar características
4. **[README_MICROSERVICE.md](README_MICROSERVICE.md)** - Usar el microservicio

### 👨‍💻 **Desarrollador**
1. **[README.md](README.md)** - Arquitectura general
2. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Endpoints y formatos
3. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Configuración de desarrollo
4. **[CHANGELOG.md](CHANGELOG.md)** - Historial técnico

### 🔧 **Administrador de Sistema**
1. **[README_MICROSERVICE.md](README_MICROSERVICE.md)** - Operación del servicio
2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Instalación y troubleshooting
3. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Monitoreo y health checks

### 📊 **Product Manager / Stakeholder**
1. **[README.md](README.md)** - Visión general del producto
2. **[FEATURES.md](FEATURES.md)** - Características completas
3. **[CHANGELOG.md](CHANGELOG.md)** - Progreso y roadmap

## 🎯 Información Rápida por Tema

### ✨ **Tránsitos por Casas** (Nueva Característica)
- **Descripción**: [FEATURES.md](FEATURES.md) - Sección "Tránsitos por Casas en Tiempo Real"
- **Implementación**: [CHANGELOG.md](CHANGELOG.md) - Versión 3.0.0
- **API**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Tipo "Tránsito Casa Estado"
- **Uso**: [README.md](README.md) - Sección "Ver Tránsitos por Casas"

### 🚀 **Inicio Rápido**
- **Comando principal**: `./start_robust.sh` ([README_MICROSERVICE.md](README_MICROSERVICE.md))
- **Verificación**: `curl http://localhost:8004/health`
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8004/docs

### 🔧 **Configuración Técnica**
- **Dependencias**: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Sección "Requisitos Previos"
- **Puertos**: 8004 (backend), 3000 (frontend)
- **Tecnologías**: Python 3.13, FastAPI, React, TypeScript

### 🐛 **Problemas Comunes**
- **"No module named 'fastapi'"**: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Solución de Problemas
- **Puerto en uso**: [README_MICROSERVICE.md](README_MICROSERVICE.md) - Troubleshooting
- **Frontend no conecta**: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Configuración Frontend

### 📊 **Rendimiento**
- **Tiempo de cálculo**: 10-15 segundos ([FEATURES.md](FEATURES.md))
- **Eventos típicos**: 200-250 por año
- **Optimizaciones V4**: ~20% más rápido ([CHANGELOG.md](CHANGELOG.md))

## 📞 Soporte y Contribución

### 🆘 **Necesitas Ayuda**
1. Buscar en la documentación usando este índice
2. Revisar [SETUP_GUIDE.md](SETUP_GUIDE.md) - Solución de Problemas
3. Verificar [CHANGELOG.md](CHANGELOG.md) para cambios recientes
4. Consultar logs del sistema

### 🤝 **Quieres Contribuir**
1. Leer [README.md](README.md) - Sección "Contribución"
2. Revisar [CHANGELOG.md](CHANGELOG.md) - Roadmap futuro
3. Consultar [API_DOCUMENTATION.md](API_DOCUMENTATION.md) para integraciones
4. Seguir patrones establecidos en [FEATURES.md](FEATURES.md)

---

**Última actualización**: Junio 2025  
**Documentos totales**: 7 archivos principales  
**Estado**: Documentación completa y actualizada
