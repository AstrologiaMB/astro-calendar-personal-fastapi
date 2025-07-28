# 🚀 Guía de Instalación - Calendario Astrológico Personal

Esta guía te llevará paso a paso para configurar el sistema completo de calendario astrológico personal.

## 📋 Requisitos Previos

### Sistema Operativo
- **macOS** (recomendado)
- **Linux** (compatible)
- **Windows** (con WSL recomendado)

### Software Requerido
- **Python 3.13** (verificado y funcionando)
- **Node.js 18+** (para el frontend)
- **Git** (para clonar repositorios)

## 🔧 Instalación del Backend (Microservicio)

### 1. Clonar el Repositorio
```bash
git clone [URL_DEL_REPOSITORIO]
cd astro-calendar-personal-fastapi
```

### 2. Configurar Entorno Virtual
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependencias
```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# Verificar instalación crítica
python -c "import immanuel.tools.ephemeris as ephemeris; print('✓ ephemeris.planet disponible' if hasattr(ephemeris, 'planet') else '✗ ERROR')"
```

### 4. Iniciar el Microservicio
```bash
# Opción A: Script automático (recomendado)
./start_robust.sh

# Opción B: Manual
source venv/bin/activate
python app.py
```

### 5. Verificar Funcionamiento
```bash
# Health check
curl -X GET http://localhost:8004/health

# Debería responder:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

## 🎨 Instalación del Frontend

### 1. Navegar al Directorio del Frontend
```bash
cd ../sidebar-fastapi
```

### 2. Instalar Dependencias de Node.js
```bash
# Usando npm
npm install

# O usando yarn
yarn install

# O usando pnpm
pnpm install
```

### 3. Configurar Variables de Entorno
```bash
# Crear archivo .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8004" > .env.local
```

### 4. Iniciar el Frontend
```bash
# Desarrollo
npm run dev

# O con yarn
yarn dev

# O con pnpm
pnpm dev
```

### 5. Acceder a la Aplicación
- **URL**: http://localhost:3000
- **Calendario Personal**: http://localhost:3000/calendario-personal

## 🧪 Verificación de la Instalación

### 1. Verificar Backend
```bash
# Desde astro-calendar-personal-fastapi/
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

**Resultado esperado**: JSON con ~200+ eventos calculados

### 2. Verificar Frontend
1. Abrir http://localhost:3000
2. Navegar a "Calendario Personal"
3. Verificar que aparezca la tarjeta "Estado Actual de Tránsitos por Casas"
4. Confirmar que se muestran los 5 planetas lentos con sus casas

### 3. Verificar Tránsitos por Casas
Deberías ver algo como:
```
Estado Actual de Tránsitos por Casas
♃ Júpiter
Casa 12 - Espiritualidad y Subconsciente

♄ Saturno  
Casa 8 - Transformación y Recursos Compartidos

♅ Urano
Casa 10 - Carrera y Reputación

♆ Neptuno
Casa 8 - Transformación y Recursos Compartidos

♇ Plutón
Casa 7 - Relaciones y Socios
```

## 🔧 Configuración Avanzada

### Configurar Datos Natales del Usuario
1. En el frontend, navegar a la configuración de usuario
2. Ingresar datos natales completos:
   - Fecha de nacimiento
   - Hora exacta de nacimiento
   - Lugar de nacimiento (ciudad)
3. Guardar configuración

### Personalizar Cálculos
El sistema usa configuraciones optimizadas por defecto, pero puedes ajustar:

**En `src/core/config.py`**:
- Orbes de aspectos
- Planetas a incluir
- Tipos de aspectos

**En `app.py`**:
- Puerto del microservicio
- Configuración de CORS
- Timeouts de cálculo

## 🔍 Solución de Problemas Comunes

### Error: "No module named 'fastapi'"
```bash
# Verificar que el entorno virtual esté activado
which python  # Debe mostrar la ruta del venv

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Port 8004 already in use"
```bash
# Encontrar y matar el proceso
lsof -ti:8004 | xargs kill -9

# O usar el script robusto que lo hace automáticamente
./start_robust.sh
```

### Error: Frontend no conecta con Backend
1. Verificar que el backend esté ejecutándose en puerto 8004
2. Comprobar la configuración de CORS en `app.py`
3. Verificar la variable de entorno `NEXT_PUBLIC_API_URL`

### Error: No aparecen tránsitos por casas
1. Verificar que los datos natales incluyan información de casas
2. Comprobar la consola del navegador para errores JavaScript
3. Verificar que el microservicio esté usando el calculador V4

### Error: Cálculos muy lentos
1. Verificar que se esté usando el calculador V4 con caching
2. Comprobar la configuración de paralelización
3. Revisar los logs para identificar cuellos de botella

## 📊 Estructura de Archivos Importantes

```
astro-calendar-personal-fastapi/
├── app.py                          # ⭐ Aplicación principal FastAPI
├── start_robust.sh                 # ⭐ Script de inicio automático
├── requirements.txt                # ⭐ Dependencias Python
├── src/calculators/
│   ├── astronomical_transits_calculator_v4.py  # ⭐ Motor principal
│   └── natal_chart.py              # ⭐ Generación de cartas natales
└── venv/                          # Entorno virtual Python

sidebar-fastapi/
├── components/
│   ├── calendario-personal.tsx     # ⭐ Componente principal
│   └── evento-astrologico.tsx      # ⭐ Renderizado de eventos
├── package.json                    # ⭐ Dependencias Node.js
└── .env.local                     # ⭐ Variables de entorno
```

## 🚀 Comandos de Inicio Rápido

### Iniciar Todo el Sistema
```bash
# Terminal 1: Backend
cd astro-calendar-personal-fastapi
./start_robust.sh

# Terminal 2: Frontend  
cd sidebar-fastapi
npm run dev
```

### Verificar Estado
```bash
# Backend health
curl http://localhost:8004/health

# Frontend
open http://localhost:3000
```

## 📞 Soporte Adicional

Si encuentras problemas no cubiertos en esta guía:

1. **Revisar logs**: Tanto del backend como del frontend
2. **Verificar versiones**: Python 3.13, Node.js 18+
3. **Comprobar puertos**: 8004 (backend) y 3000 (frontend)
4. **Consultar documentación**: README.md y archivos específicos

---

**Última actualización**: Diciembre 2025  
**Tiempo estimado de instalación**: 15-30 minutos
