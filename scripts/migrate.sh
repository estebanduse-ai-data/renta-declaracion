#!/usr/bin/env bash
# =============================================================================
# migrate.sh — Aplica migraciones de Alembic y siembra datos iniciales
#
# Útil para:
#   - Re-ejecutar migraciones después de un cambio de modelos.
#   - Restablecer datos iniciales en una BD limpia.
#   - Ejecutar solo las migraciones sin tocar el código de las apps.
#
# Uso:
#   ./scripts/migrate.sh                         # solo migración
#   ./scripts/migrate.sh --sembrar               # migración + siembra
#   ./scripts/migrate.sh --sembrar \
#       --admin-email me@empresa.com \
#       --admin-password "ClaveSegura!" \
#       --admin-nombre "Carlos Pérez"
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✔  ${NC}$*"; }
info() { echo -e "${CYAN}  →  ${NC}$*"; }
warn() { echo -e "${YELLOW}  ⚠  ${NC}$*"; }
err()  { echo -e "${RED}  ✖  ${NC}$*" >&2; }
step() { echo -e "\n${BOLD}${BLUE}══ $* ${NC}"; }
BLUE='\033[0;34m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND="$ROOT/backend"

# ── Argumentos ────────────────────────────────────────────────────────────────
SEMBRAR=false
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@renta.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin2025!}"
ADMIN_NOMBRE="${ADMIN_NOMBRE:-Administrador}"

while [[ $# -gt 0 ]]; do
  case $1 in
    --sembrar)        SEMBRAR=true;          shift ;;
    --admin-email)    ADMIN_EMAIL="$2";      shift 2 ;;
    --admin-password) ADMIN_PASSWORD="$2";   shift 2 ;;
    --admin-nombre)   ADMIN_NOMBRE="$2";     shift 2 ;;
    *) err "Argumento desconocido: $1"; exit 1 ;;
  esac
done

echo -e "\n${BOLD}${CYAN}══ migrate.sh — Migraciones Alembic ══${NC}\n"

# ── Verificar BD corriendo ────────────────────────────────────────────────────
if ! docker ps --filter "name=renta-db" --format "{{.Names}}" | grep -q "renta-db"; then
  info "renta-db no está corriendo. Intentando iniciar..."
  docker start renta-db 2>/dev/null || {
    err "No se pudo iniciar renta-db. ¿Ya corriste setup.sh?"
    exit 1
  }
fi

for i in {1..10}; do
  if docker exec renta-db pg_isready -U renta -q 2>/dev/null; then
    ok "PostgreSQL listo."; break
  fi
  [[ $i -eq 10 ]] && { err "PostgreSQL no respondió."; exit 1; }
  sleep 1
done

# ── Activar virtualenv ────────────────────────────────────────────────────────
if [[ ! -d "$BACKEND/.venv" ]]; then
  err "Virtualenv no encontrado. Ejecuta ./scripts/setup.sh primero."
  exit 1
fi

cd "$BACKEND"

# Fix macOS/Homebrew — libexpat (mismo que setup.sh y start_backend.sh)
if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &>/dev/null; then
  BREW_EXPAT="$(brew --prefix expat 2>/dev/null)/lib"
  if [[ -d "$BREW_EXPAT" && "${DYLD_LIBRARY_PATH:-}" != *"$BREW_EXPAT"* ]]; then
    export DYLD_LIBRARY_PATH="$BREW_EXPAT${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
  fi
fi

source .venv/bin/activate

# Verificar que el virtualenv activo es 3.11+
VENV_MIN=$(python -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo 0)
VENV_VER=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")' 2>/dev/null || echo "0.0.0")
if [[ $VENV_MIN -lt 11 ]]; then
  err "El virtualenv usa Python $VENV_VER (< 3.11). Ejecuta './scripts/setup.sh' para recrearlo."
  deactivate; exit 1
fi
ok "Virtualenv activo (Python $VENV_VER)."

# Corregir DATABASE_URL si apunta a 'db'
if grep -q "@db:" .env 2>/dev/null; then
  sed -i.bak 's|@db:|@localhost:|g' .env && rm -f .env.bak
  warn "DATABASE_URL corregida de 'db' a 'localhost'."
fi

DB_URL="$(grep DATABASE_URL .env | cut -d= -f2-)"

# ── alembic upgrade head ──────────────────────────────────────────────────────
step "Aplicando migraciones"
info "alembic upgrade head..."
DATABASE_URL="$DB_URL" alembic upgrade head
ok "Migraciones aplicadas."

# ── alembic check ─────────────────────────────────────────────────────────────
step "Verificando coherencia migración ↔ modelos"
info "alembic check..."
if DATABASE_URL="$DB_URL" alembic check 2>&1; then
  ok "Migración sincronizada con los modelos."
else
  warn "alembic check reportó diferencias. Generando migración de ajuste..."
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  DATABASE_URL="$DB_URL" alembic revision --autogenerate -m "ajuste_$TIMESTAMP"
  DATABASE_URL="$DB_URL" alembic upgrade head
  ok "Migración de ajuste aplicada."
fi

# ── Siembra (opcional) ────────────────────────────────────────────────────────
if [[ "$SEMBRAR" == "true" ]]; then
  step "Sembrando datos iniciales"
  info "python3 scripts/sembrar_datos_iniciales.py..."
  python3 scripts/sembrar_datos_iniciales.py \
    --admin-email    "$ADMIN_EMAIL" \
    --admin-password "$ADMIN_PASSWORD" \
    --admin-nombre   "$ADMIN_NOMBRE"
  ok "Datos iniciales sembrados."
  echo ""
  echo -e "  Credenciales del Admin:"
  echo -e "  Email:      ${CYAN}$ADMIN_EMAIL${NC}"
  echo -e "  Contraseña: ${CYAN}$ADMIN_PASSWORD${NC}"
fi

deactivate
echo ""
ok "migrate.sh completado."