# 📡 API Documentation - Calendario Astrológico Personal

Documentación completa de la API REST del microservicio de calendario astrológico personal.

## 🌐 Información General

- **Base URL**: `http://localhost:8004`
- **Protocolo**: HTTP/HTTPS
- **Formato**: JSON
- **Autenticación**: No requerida (desarrollo)
- **CORS**: Habilitado para desarrollo

## 📊 Endpoints Principales

### 1. Cálculo Dinámico de Calendario Personal

#### `POST /calculate-personal-calendar-dynamic`

**Descripción**: Genera carta natal automáticamente y calcula todos los eventos astrológicos para el año especificado.

**Request Body**:
```json
{
  "name": "string",
  "birth_date": "YYYY-MM-DD",
  "birth_time": "HH:MM",
  "location": {
    "latitude": "number",
    "longitude": "number", 
    "name": "string",
    "timezone": "string"
  },
  "year": "number"
}
```

**Ejemplo de Request**:
```json
{
  "name": "María García",
  "birth_date": "1990-03-15",
  "birth_time": "14:30",
  "location": {
    "latitude": -34.6037,
    "longitude": -58.3816,
    "name": "Buenos Aires, Argentina",
    "timezone": "America/Argentina/Buenos_Aires"
  },
  "year": 2025
}
```

**Response**:
```json
{
  "events": [
    {
      "fecha_utc": "2025-01-15",
      "hora_utc": "18:30",
      "tipo_evento": "Aspecto",
      "descripcion": "Venus (directo) por tránsito esta en Conjunción a tu Sol Natal",
      "planeta1": "Venus",
      "planeta2": "Sol",
      "posicion1": "25°14'32\" Capricornio",
      "posicion2": "25°14'30\" Capricornio",
      "tipo_aspecto": "Conjunción",
      "orbe": "0°00'02\"",
      "es_aplicativo": "No",
      "harmony": "Neutro"
    }
  ],
  "total_events": 215,
  "calculation_time": 12.45,
  "year": 2025,
  "name": "María García"
}
```

**Códigos de Estado**:
- `200`: Cálculo exitoso
- `400`: Datos de entrada inválidos
- `500`: Error interno del servidor

---

### 2. Cálculo con Carta Natal Previa (Legacy)

#### `POST /calculate-personal-calendar`

**Descripción**: Calcula eventos usando una carta natal pre-calculada.

**Request Body**:
```json
{
  "points": {
    "Sun": {
      "sign": "Capricornio",
      "position": "25°14'30\"",
      "longitude": 295.2417,
      "latitude": 0.0,
      "distance": 0.0,
      "speed": 0.0,
      "retrograde": false
    }
  },
  "houses": {
    "1": {
      "sign": "Aries",
      "position": "15°30'45\"",
      "longitude": 15.5125
    }
  },
  "location": {
    "latitude": -34.6037,
    "longitude": -58.3816,
    "name": "Buenos Aires",
    "timezone": "America/Argentina/Buenos_Aires"
  },
  "hora_local": "1990-03-15T14:30:00",
  "name": "María García",
  "year": 2025
}
```

**Response**: Mismo formato que el endpoint dinámico.

---

### 3. Health Check

#### `GET /health`

**Descripción**: Verifica el estado del microservicio.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-19T16:22:30.123456",
  "version": "1.0.0"
}
```

---

### 4. Información del Servicio

#### `GET /info`

**Descripción**: Información detallada sobre el microservicio y sus capacidades.

**Response**:
```json
{
  "service": "Personal Astrology Calendar API",
  "version": "2.0.0",
  "description": "Complete microservice for calculating personal astrological events",
  "endpoints": [
    "/calculate-personal-calendar-dynamic",
    "/calculate-personal-calendar",
    "/health",
    "/info"
  ],
  "features": [
    "Astronomical transits (V4 calculator)",
    "Progressed moon conjunctions",
    "Annual profections",
    "Lunar phases (new moon, full moon)",
    "Solar and lunar eclipses",
    "House transits state",
    "High-precision ephemeris calculations",
    "Spanish language descriptions"
  ]
}
```

---

### 5. Documentación Interactiva

#### `GET /docs`

**Descripción**: Interfaz Swagger/OpenAPI para explorar la API interactivamente.

**URL**: http://localhost:8004/docs

---

### 6. Esquema OpenAPI

#### `GET /openapi.json`

**Descripción**: Esquema OpenAPI en formato JSON.

## 🎯 Tipos de Eventos Retornados

### 1. Aspecto
```json
{
  "tipo_evento": "Aspecto",
  "descripcion": "Marte (directo) por tránsito esta en Cuadratura a tu Luna Natal",
  "planeta1": "Marte",
  "planeta2": "Luna",
  "tipo_aspecto": "Cuadratura",
  "orbe": "1°15'30\"",
  "harmony": "Tensión"
}
```

### 2. Luna Progresada
```json
{
  "tipo_evento": "Luna Progresada",
  "descripcion": "Luna progresada en conjunción con Mercurio natal",
  "planeta1": "Luna",
  "planeta2": "Mercurio"
}
```

### 3. Profección
```json
{
  "tipo_evento": "Profección",
  "descripcion": "Año de profección de Casa 5: Creatividad y Romance",
  "casa_natal": 5
}
```

### 4. Luna Nueva/Llena
```json
{
  "tipo_evento": "Luna Nueva",
  "descripcion": "Luna Nueva en Acuario en Casa 11",
  "signo": "Acuario",
  "casa_natal": 11
}
```

### 5. Eclipse
```json
{
  "tipo_evento": "Eclipse Solar",
  "descripcion": "Eclipse Solar en Géminis en Casa 3",
  "signo": "Géminis",
  "casa_natal": 3
}
```

### 6. Tránsito Casa Estado (NUEVO)
```json
{
  "tipo_evento": "Tránsito Casa Estado",
  "descripcion": "Estado actual de tránsitos por casas natales",
  "metadata": {
    "house_transits": [
      {
        "planeta": "Júpiter",
        "simbolo": "♃",
        "casa": 12,
        "casa_significado": "Espiritualidad y Subconsciente"
      }
    ]
  }
}
```

## 🔧 Parámetros de Configuración

### Zonas Horarias Soportadas
- Formato: IANA timezone (ej: "America/Argentina/Buenos_Aires")
- Ejemplos válidos:
  - `America/New_York`
  - `Europe/Madrid`
  - `Asia/Tokyo`
  - `America/Mexico_City`
  - `Australia/Sydney`

### Rangos de Fechas
- **Años soportados**: 1900-2100
- **Precisión temporal**: Minutos
- **Formato de fecha**: ISO 8601 (YYYY-MM-DD)
- **Formato de hora**: 24 horas (HH:MM)

### Coordenadas Geográficas
- **Latitud**: -90.0 a 90.0 (grados decimales)
- **Longitud**: -180.0 a 180.0 (grados decimales)
- **Precisión**: 4 decimales recomendados

## ⚠️ Códigos de Error

### 400 - Bad Request
```json
{
  "detail": "Invalid timezone 'Invalid/Timezone': [error details]"
}
```

### 500 - Internal Server Error
```json
{
  "detail": "Error calculating personal calendar: [error details]"
}
```

### Errores Comunes

#### Timezone Inválido
```json
{
  "detail": "Invalid timezone 'America/Invalid': No such timezone"
}
```

#### Fecha Inválida
```json
{
  "detail": "Invalid birth_date format. Use YYYY-MM-DD"
}
```

#### Coordenadas Inválidas
```json
{
  "detail": "Latitude must be between -90 and 90 degrees"
}
```

## 🚀 Ejemplos de Uso

### cURL
```bash
curl -X POST "http://localhost:8004/calculate-personal-calendar-dynamic" \
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

### JavaScript/Fetch
```javascript
const response = await fetch('http://localhost:8004/calculate-personal-calendar-dynamic', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: "Test User",
    birth_date: "1990-01-15",
    birth_time: "14:30",
    location: {
      latitude: -34.6037,
      longitude: -58.3816,
      name: "Buenos Aires",
      timezone: "America/Argentina/Buenos_Aires"
    },
    year: 2025
  })
});

const data = await response.json();
console.log(`Calculated ${data.total_events} events`);
```

### Python/Requests
```python
import requests

data = {
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
}

response = requests.post(
    'http://localhost:8004/calculate-personal-calendar-dynamic',
    json=data
)

result = response.json()
print(f"Calculated {result['total_events']} events")
```

## 📈 Rendimiento y Límites

### Tiempos de Respuesta Típicos
- **Cálculo completo**: 10-15 segundos
- **Health check**: <100ms
- **Info endpoint**: <50ms

### Límites de Uso
- **Timeout**: 60 segundos por request
- **Tamaño máximo**: 10MB por request
- **Rate limiting**: No implementado (desarrollo)

### Optimizaciones
- **Caching**: Efemérides en memoria durante cálculo
- **Paralelización**: Múltiples planetas simultáneamente
- **Filtrado**: Solo eventos exactos o estacionarios

## 🔍 Debugging y Logs

### Headers de Debug
```bash
# Agregar header para logs detallados
curl -H "X-Debug: true" http://localhost:8004/calculate-personal-calendar-dynamic
```

### Logs del Servidor
Los logs incluyen:
- Tiempo de cálculo por componente
- Número de eventos por tipo
- Errores y warnings
- Información de debug del calculador V4

### Monitoreo
- **Health endpoint**: Estado general
- **Logs de aplicación**: Detalles de ejecución
- **Métricas de rendimiento**: Tiempo por cálculo

---

**Última actualización**: Diciembre 2025  
**Versión de API**: 2.0.0  
**Estado**: Completamente funcional con tránsitos por casas
