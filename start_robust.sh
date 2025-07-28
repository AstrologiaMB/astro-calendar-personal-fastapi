#!/bin/bash

# Microservicio Personal Calendar - Script de Inicio Robusto
# Versión: 2.0
# Fecha: 16/06/2025

set -e  # Salir si hay algún error

echo "🚀 Iniciando Microservicio Personal Calendar..."
echo "📅 $(date)"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    log_error "No se encuentra app.py. Ejecuta este script desde el directorio del proyecto."
    exit 1
fi

log_info "Directorio del proyecto verificado ✓"

# Verificar Python 3.13
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$PYTHON_VERSION" != "3.13" ]; then
    log_warning "Python 3.13 no encontrado. Intentando con python3..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 no está instalado"
        exit 1
    fi
fi

log_info "Python verificado ✓"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    log_info "Creando entorno virtual..."
    python3 -m venv venv
    log_success "Entorno virtual creado ✓"
else
    log_info "Entorno virtual existente encontrado ✓"
fi

# Activar entorno virtual
log_info "Activando entorno virtual..."
source venv/bin/activate

# Verificar que pip está actualizado
log_info "Verificando pip..."
pip install --upgrade pip > /dev/null 2>&1

# Instalar dependencias
log_info "Instalando dependencias..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    log_success "Dependencias instaladas ✓"
else
    log_error "requirements.txt no encontrado"
    exit 1
fi

# Verificar dependencias críticas
log_info "Verificando dependencias críticas..."

# Verificar Immanuel
python3 -c "
import immanuel
import immanuel.tools.ephemeris as ephemeris
print('✓ Immanuel:', getattr(immanuel, '__version__', 'version unknown'))
if hasattr(ephemeris, 'planet'):
    print('✓ ephemeris.planet: disponible')
else:
    print('✗ ephemeris.planet: NO disponible')
    exit(1)
" || {
    log_error "Immanuel no está correctamente instalado"
    exit 1
}

# Verificar FastAPI
python3 -c "import fastapi; print('✓ FastAPI:', fastapi.__version__)" || {
    log_error "FastAPI no está correctamente instalado"
    exit 1
}

log_success "Todas las dependencias críticas verificadas ✓"

# Verificar puerto 8004
if lsof -Pi :8004 -sTCP:LISTEN -t >/dev/null ; then
    log_warning "Puerto 8004 ya está en uso. Intentando detener proceso..."
    kill $(lsof -ti:8004) 2>/dev/null || true
    sleep 2
fi

log_info "Puerto 8004 disponible ✓"

# Iniciar microservicio
log_success "🎯 Iniciando microservicio en puerto 8004..."
echo ""
echo "📊 Información del servicio:"
echo "   • URL: http://localhost:8004"
echo "   • Documentación: http://localhost:8004/docs"
echo "   • Health check: http://localhost:8004/health"
echo ""
echo "🔄 Para detener: Ctrl+C"
echo ""

# Ejecutar con el Python del venv
exec python app.py
