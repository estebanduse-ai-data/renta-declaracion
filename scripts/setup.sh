#!/usr/bin/env bash
# =============================================================================
# setup.sh — Primer arranque completo del proyecto renta-declaracion
#
# Qué hace este script (en orden):
#   1. Busca el intérprete Python 3.11+ disponible (python3.13, python3.12,
#      python3.11, python3, python — en ese orden). Maneja máquinas con varias
#      versiones instaladas donde 'python3' puede ser la versión base del sistema.
#   2. Levanta el contenedor PostgreSQL en Docker (solo la BD).
#   3. Crea el virtualenv de Python e instala las dependencias del backend.
#   4. Copia .env.example → .env y ajusta DATABASE_URL a localhost.
#   5. Corre las 60+ pruebas unitarias del motor de reglas.
#   6. Aplica las migraciones de Alembic.
#   7. Verifica que la migración coincide con los modelos (alembic check).
#   8. Siembra el primer usuario Admin y los parámetros tributarios 2025.
#   9. Instala las dependencias del frontend (npm install).
#  10. Imprime las instrucciones para levantar cada app.
#
# Uso:
#   cd renta-declaracion/
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
#
# Opciones:
#   --admin-email    EMAIL   (default: admin@renta.local)
#   --admin-password PASS    (default: Admin2025!)
#   --admin-nombre   NOMBRE  (default: Administrador)
# =============================================================================

set -euo pipefail

# ── Colores ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✔  ${NC}$*"; }
info() { echo -e "${CYAN}  →  ${NC}$*"; }
warn() { echo -e "${YELLOW}  ⚠  ${NC}$*"; }
err()  { echo -e "${RED}  ✖  ${NC}$*" >&2; }
step() { echo -e "\n${BOLD}${BLUE}══ $* ${NC}"; }

# ── Argumentos opcionales ─────────────────────────────────────────────────────
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@renta.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin2025!}"
ADMIN_NOMBRE="${ADMIN_NOMBRE:-Administrador}"

while [[ $# -gt 0 ]]; do
  case $1 in
    --admin-email)    ADMIN_EMAIL="$2";    shift 2 ;;
    --admin-password) ADMIN_PASSWORD="$2"; shift 2 ;;
    --admin-nombre)   ADMIN_NOMBRE="$2";   shift 2 ;;
    *) err "Argumento desconocido: $1"; exit 1 ;;
  esac
done

# ── Directorio raíz del proyecto ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo -e "\n${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   renta-declaracion — Primer arranque (setup.sh)    ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "  Raíz del proyecto: ${CYAN}$ROOT${NC}"
echo -e "  Admin email:       ${CYAN}$ADMIN_EMAIL${NC}"

# ── PASO 1: Verificar dependencias del sistema ────────────────────────────────
step "PASO 1 — Verificando dependencias del sistema"

if ! command -v docker &>/dev/null; then
  err "Docker no encontrado. Instala Docker Desktop desde https://www.docker.com/products/docker-desktop/"
  exit 1
fi
ok "Docker $(docker --version | awk '{print $3}' | tr -d ',')"

# Buscar un intérprete Python 3.11+ entre todos los disponibles en el sistema.
# En máquinas con múltiples versiones instaladas (ej: python3 = 3.9 del sistema
# y python3.11 / python3.12 instalados aparte), usamos el más nuevo que cumpla
# el requisito mínimo, no necesariamente el que responde a 'python3'.
#
# Orden de búsqueda: python3.13 → python3.12 → python3.11 → python3 → python
PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$candidate" &>/dev/null; then
    _maj=$("$candidate" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo 0)
    _min=$("$candidate" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo 0)
    if [[ $_maj -eq 3 && $_min -ge 11 ]]; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  err "No se encontró Python 3.11+ en el sistema."
  echo ""
  echo -e "  Intérpretes detectados:"
  for candidate in python3.13 python3.12 python3.11 python3.10 python3.9 python3 python; do
    if command -v "$candidate" &>/dev/null; then
      _ver=$("$candidate" --version 2>&1 | awk '{print $2}')
      echo -e "    ${YELLOW}$candidate${NC}  →  $_ver"
    fi
  done
  echo ""
  echo -e "  Instala Python 3.11 o superior:"
  echo -e "  ${CYAN}macOS:${NC}   brew install python@3.11"
  echo -e "  ${CYAN}Ubuntu:${NC}  sudo apt install python3.11 python3.11-venv"
  exit 1
fi

PY_VERSION=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
ok "Python $PY_VERSION  ($(command -v $PYTHON_BIN))"

# Si 'python3' del sistema es una versión anterior, avisarlo para que el
# desarrollador sepa que se está usando un intérprete alternativo.
if [[ "$PYTHON_BIN" != "python3" ]] && command -v python3 &>/dev/null; then
  SYS_VER=$(python3 --version 2>&1 | awk '{print $2}')
  warn "python3 del sistema es $SYS_VER (< 3.11). Usando '$PYTHON_BIN' para este proyecto."
fi

# ── Fix automático macOS/Homebrew: conflicto libexpat ────────────────────────
# python3.11 de Homebrew compila pyexpat.so contra su propia libexpat, pero en
# tiempo de ejecución macOS resuelve el símbolo desde /usr/lib/libexpat.1.dylib
# (versión del sistema, más antigua) causando "Symbol not found".
# Solución: anteponer la libexpat de Homebrew en DYLD_LIBRARY_PATH para que
# el linker dinámico la encuentre primero. Se aplica solo en macOS y solo si
# Homebrew tiene expat instalado.
if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &>/dev/null; then
  BREW_EXPAT="$(brew --prefix expat 2>/dev/null)/lib"
  if [[ -d "$BREW_EXPAT" ]]; then
    if [[ -z "${DYLD_LIBRARY_PATH:-}" ]] || [[ "$DYLD_LIBRARY_PATH" != *"$BREW_EXPAT"* ]]; then
      export DYLD_LIBRARY_PATH="$BREW_EXPAT${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
      info "macOS/Homebrew: DYLD_LIBRARY_PATH ajustado para usar libexpat de Homebrew."
      info "  → $BREW_EXPAT"
    fi
  fi
fi

# ── Validar que el intérprete está funcionalmente sano ───────────────────────
# Verificamos los módulos que dependen de librerías dinámicas del sistema
# (pyexpat, ssl, sqlite3) antes de intentar crear el virtualenv.
info "Verificando integridad del intérprete Python..."

PY_HEALTH_SCRIPT='
import sys
modulos = ["xml.parsers.expat", "ssl", "sqlite3", "hashlib", "ctypes"]
fallidos = []
for m in modulos:
    try:
        __import__(m)
    except ImportError as e:
        fallidos.append(f"{m}: {e}")
if fallidos:
    for f in fallidos: print(f)
    sys.exit(1)
'

PY_HEALTH_ERROR=$("$PYTHON_BIN" -c "$PY_HEALTH_SCRIPT" 2>&1 || true)

if [[ -n "$PY_HEALTH_ERROR" ]]; then
  err "El intérprete $PYTHON_BIN tiene librerías rotas incluso después del fix de DYLD_LIBRARY_PATH:"
  echo ""
  while IFS= read -r linea; do
    echo -e "    ${RED}$linea${NC}"
  done <<< "$PY_HEALTH_ERROR"
  echo ""
  echo -e "  ${YELLOW}Este es un problema de instalación de Python, no del proyecto.${NC}"
  echo -e "  La causa más común en macOS con Homebrew es un conflicto entre"
  echo -e "  la versión de libexpat/libssl de Homebrew y la del sistema."
  echo ""
  echo -e "  ${BOLD}Opciones para resolverlo:${NC}"
  echo ""
  echo -e "  ${CYAN}A. Reinstalar expat y Python desde Homebrew:${NC}"
  echo -e "     brew reinstall expat && brew reinstall python@3.11"
  echo -e "     python3.11 -c \"import xml.parsers.expat, ssl; print('OK')\""
  echo ""
  echo -e "  ${CYAN}B. Usar Python 3.12 (no tiene este conflicto):${NC}"
  echo -e "     brew install python@3.12"
  echo ""
  echo -e "  ${CYAN}C. Usar pyenv (compila desde fuente, sin conflictos de .dylib):${NC}"
  echo -e "     brew install pyenv && pyenv install 3.11.9 && pyenv local 3.11.9"
  echo ""
  echo -e "  Luego vuelve a ejecutar: ${BOLD}./scripts/setup.sh${NC}"
  exit 1
fi
ok "Intérprete Python verificado — librerías dinámicas OK."

if ! command -v node &>/dev/null; then
  err "Node.js no encontrado. Instala Node 20+ desde https://nodejs.org/"
  exit 1
fi
NODE_VERSION=$(node --version | tr -d 'v' | cut -d. -f1)
if [[ $NODE_VERSION -lt 20 ]]; then
  err "Se requiere Node.js 20+. Versión actual: $(node --version)"
  exit 1
fi
ok "Node.js $(node --version)"

if ! command -v npm &>/dev/null; then
  err "npm no encontrado."
  exit 1
fi
ok "npm $(npm --version)"

# ── PASO 2: Levantar PostgreSQL en Docker ─────────────────────────────────────
step "PASO 2 — Levantando PostgreSQL en Docker"

if docker ps --filter "name=renta-db" --format "{{.Names}}" | grep -q "renta-db"; then
  ok "El contenedor renta-db ya está corriendo."
elif docker ps -a --filter "name=renta-db" --format "{{.Names}}" | grep -q "renta-db"; then
  info "Contenedor renta-db existe pero está detenido. Reiniciando..."
  docker start renta-db
  ok "renta-db reiniciado."
else
  info "Creando contenedor renta-db..."
  docker run -d \
    --name renta-db \
    -e POSTGRES_USER=renta \
    -e POSTGRES_PASSWORD=renta \
    -e POSTGRES_DB=renta_declaracion \
    -p 5432:5432 \
    --restart unless-stopped \
    postgres:16-alpine
  ok "Contenedor renta-db creado y corriendo."
fi

info "Esperando que PostgreSQL acepte conexiones..."
for i in {1..15}; do
  if docker exec renta-db pg_isready -U renta -q 2>/dev/null; then
    ok "PostgreSQL listo."
    break
  fi
  if [[ $i -eq 15 ]]; then
    err "PostgreSQL no respondió en 15 segundos."
    exit 1
  fi
  sleep 1
done

# ── PASO 3: Virtualenv e instalación de dependencias del backend ──────────────
step "PASO 3 — Configurando el virtualenv del backend"

cd "$BACKEND"

# Función para crear el virtualenv con manejo de ensurepip ausente.
# En macOS con Python instalado vía Homebrew o pyenv, `python3.11 -m venv`
# puede fallar con "ensurepip returned non-zero exit status 1" si el módulo
# ensurepip no está disponible. Estrategia:
#   1. Intentar la creación normal.
#   2. Si falla, intentar con --without-pip (crea el venv sin pip).
#   3. Instalar pip manualmente con get-pip.py.
crear_venv() {
  local destino=".venv"
  info "Creando virtualenv con $PYTHON_BIN ($PY_VERSION) en backend/$destino ..."

  if "$PYTHON_BIN" -m venv "$destino" 2>/dev/null; then
    ok "Virtualenv creado con Python $PY_VERSION."
    return 0
  fi

  warn "Falló la creación normal del virtualenv (posiblemente ensurepip ausente)."
  warn "Intentando con --without-pip..."

  if ! "$PYTHON_BIN" -m venv --without-pip "$destino"; then
    err "No se pudo crear el virtualenv incluso con --without-pip."
    echo ""
    echo -e "  ${YELLOW}Soluciones según tu entorno:${NC}"
    echo -e "  ${CYAN}Homebrew (macOS):${NC}  brew install python@3.11"
    echo -e "  ${CYAN}Ubuntu/Debian:${NC}     sudo apt install python3.11-venv"
    echo -e "  ${CYAN}pyenv:${NC}             pyenv install 3.11.9"
    echo ""
    exit 1
  fi

  # Instalar pip manualmente con get-pip.py
  info "Instalando pip manualmente con get-pip.py..."
  GET_PIP_TMP=$(mktemp /tmp/get-pip-XXXXXX.py)
  if command -v curl &>/dev/null; then
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o "$GET_PIP_TMP"
  elif command -v wget &>/dev/null; then
    wget -qO "$GET_PIP_TMP" https://bootstrap.pypa.io/get-pip.py
  else
    err "No se encontró curl ni wget para descargar get-pip.py."
    err "Instala pip manualmente: $PYTHON_BIN -m ensurepip --upgrade"
    rm -f "$GET_PIP_TMP"
    exit 1
  fi

  "$destino/bin/python" "$GET_PIP_TMP" --quiet
  rm -f "$GET_PIP_TMP"
  ok "pip instalado manualmente. Virtualenv listo con Python $PY_VERSION."
}

if [[ ! -d ".venv" ]]; then
  crear_venv
else
  # Verificar que el virtualenv existente es 3.11+; si no, recrearlo.
  VENV_VER=$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
  VENV_MIN=$(echo "$VENV_VER" | cut -d. -f2)
  if [[ $VENV_MIN -lt 11 ]]; then
    warn "El virtualenv existente usa Python $VENV_VER (< 3.11). Recreándolo con $PYTHON_BIN..."
    rm -rf .venv
    crear_venv
  else
    ok "Virtualenv ya existe (Python $VENV_VER)."
  fi
fi

source .venv/bin/activate
info "Instalando dependencias de Python..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Dependencias instaladas."

# ── PASO 4: Archivo .env ──────────────────────────────────────────────────────
step "PASO 4 — Configurando el archivo .env del backend"

if [[ -f ".env" ]]; then
  ok ".env ya existe, no se sobreescribe."
else
  cp .env.example .env
  # Ajustar DATABASE_URL: el backend corre en local (no en Docker), así que
  # la BD está en localhost, no en 'db' (nombre del servicio Docker Compose)
  sed -i.bak \
    's|DATABASE_URL=postgresql+psycopg://renta:renta@db:5432/|DATABASE_URL=postgresql+psycopg://renta:renta@localhost:5432/|g' \
    .env
  rm -f .env.bak
  ok ".env creado con DATABASE_URL apuntando a localhost:5432"
  warn "Recuerda cambiar JWT_SECRET_KEY en .env antes de usar en producción."
fi

# Verificar que DATABASE_URL apunta a localhost (no a 'db')
if grep -q "@db:" .env 2>/dev/null; then
  warn "DATABASE_URL en .env apunta a 'db' (host Docker Compose). Corrigiendo a 'localhost'..."
  sed -i.bak 's|@db:|@localhost:|g' .env
  rm -f .env.bak
  ok "DATABASE_URL corregida a localhost."
fi

# ── PASO 5: Pruebas unitarias del motor de reglas ─────────────────────────────
step "PASO 5 — Ejecutando pruebas unitarias del motor de reglas"

info "Corriendo pytest..."
if pytest -v --tb=short 2>&1; then
  ok "Todas las pruebas pasaron."
else
  err "Algunas pruebas fallaron. Revisa el output de arriba antes de continuar."
  echo -e "  ${YELLOW}¿Continuar de todas formas? [s/N]:${NC} \c"
  read -r respuesta
  if [[ ! "$respuesta" =~ ^[sS]$ ]]; then
    exit 1
  fi
fi

# ── PASO 6: Migraciones de Alembic ───────────────────────────────────────────
step "PASO 6 — Aplicando migraciones de Alembic"

info "alembic upgrade head..."
if DATABASE_URL="$(grep DATABASE_URL .env | cut -d= -f2-)" alembic upgrade head; then
  ok "Migraciones aplicadas."
else
  err "Fallo en alembic upgrade head."
  exit 1
fi

# ── PASO 7: Verificar coherencia de la migración ─────────────────────────────
step "PASO 7 — Verificando coherencia migración ↔ modelos"

info "alembic check..."
if DATABASE_URL="$(grep DATABASE_URL .env | cut -d= -f2-)" alembic check 2>&1; then
  ok "La migración está sincronizada con los modelos."
else
  warn "alembic check reportó diferencias. Generando migración de ajuste..."
  DATABASE_URL="$(grep DATABASE_URL .env | cut -d= -f2-)" \
    alembic revision --autogenerate -m "ajuste_post_inicial"
  DATABASE_URL="$(grep DATABASE_URL .env | cut -d= -f2-)" \
    alembic upgrade head
  ok "Migración de ajuste aplicada."
fi

# ── PASO 8: Siembra de datos iniciales ───────────────────────────────────────
step "PASO 8 — Sembrando usuario Admin y parámetros 2025"

info "Ejecutando sembrar_datos_iniciales.py..."
python3 scripts/sembrar_datos_iniciales.py \
  --admin-email    "$ADMIN_EMAIL" \
  --admin-password "$ADMIN_PASSWORD" \
  --admin-nombre   "$ADMIN_NOMBRE"
ok "Datos iniciales sembrados."

deactivate

# ── PASO 9: Dependencias del frontend ────────────────────────────────────────
step "PASO 9 — Instalando dependencias del frontend"

cd "$FRONTEND"
info "npm install..."
npm install --silent
ok "Dependencias del frontend instaladas."

# ── FIN: instrucciones ────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║           ✔  Setup completado con éxito             ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Para levantar las apps, ejecuta en terminales separadas:"
echo ""
echo -e "  ${CYAN}# Terminal 1 — API (backend)${NC}"
echo -e "  ${BOLD}./scripts/start_backend.sh${NC}"
echo ""
echo -e "  ${CYAN}# Terminal 2 — Interfaz web (frontend)${NC}"
echo -e "  ${BOLD}./scripts/start_frontend.sh${NC}"
echo ""
echo -e "  URLs disponibles:"
echo -e "  ${CYAN}http://localhost:5173${NC}        → Interfaz web"
echo -e "  ${CYAN}http://localhost:8000/docs${NC}   → Documentación interactiva de la API"
echo -e "  ${CYAN}http://localhost:8000/salud${NC}  → Health check"
echo ""
echo -e "  Credenciales del Admin:"
echo -e "  Email:      ${CYAN}$ADMIN_EMAIL${NC}"
echo -e "  Contraseña: ${CYAN}$ADMIN_PASSWORD${NC}"
echo ""