#!/usr/bin/env bash
# =============================================================================
# start_backend.sh — Levanta la API de FastAPI en modo desarrollo
#
# Uso:
#   ./scripts/start_backend.sh
#
# Prerequisito: haber corrido setup.sh al menos una vez.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✔  ${NC}$*"; }
info() { echo -e "${CYAN}  →  ${NC}$*"; }
err()  { echo -e "${RED}  ✖  ${NC}$*" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND="$ROOT/backend"

echo -e "\n${BOLD}${CYAN}══ Backend — FastAPI (uvicorn --reload) ══${NC}\n"

# 1. Verificar que el contenedor de BD esté corriendo
if ! docker ps --filter "name=renta-db" --format "{{.Names}}" | grep -q "renta-db"; then
  info "El contenedor renta-db no está corriendo. Iniciándolo..."
  if docker ps -a --filter "name=renta-db" --format "{{.Names}}" | grep -q "renta-db"; then
    docker start renta-db
    ok "renta-db iniciado."
  else
    err "El contenedor renta-db no existe. Ejecuta primero: ./scripts/setup.sh"
    exit 1
  fi
else
  ok "renta-db corriendo."
fi

# Esperar a que PostgreSQL esté listo
for i in {1..10}; do
  if docker exec renta-db pg_isready -U renta -q 2>/dev/null; then
    ok "PostgreSQL listo."; break
  fi
  [[ $i -eq 10 ]] && { err "PostgreSQL no respondió."; exit 1; }
  sleep 1
done

# 2. Fix macOS/Homebrew — libexpat
# Misma corrección que en setup.sh: anteponer la libexpat de Homebrew para que
# pyexpat.so la encuentre en lugar de la versión del sistema (/usr/lib).
if [[ "$OSTYPE" == "darwin"* ]] && command -v brew &>/dev/null; then
  BREW_EXPAT="$(brew --prefix expat 2>/dev/null)/lib"
  if [[ -d "$BREW_EXPAT" && "${DYLD_LIBRARY_PATH:-}" != *"$BREW_EXPAT"* ]]; then
    export DYLD_LIBRARY_PATH="$BREW_EXPAT${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
  fi
fi

# 4. Activar el virtualenv
if [[ ! -d "$BACKEND/.venv" ]]; then
  err "Virtualenv no encontrado en backend/.venv. Ejecuta primero: ./scripts/setup.sh"
  exit 1
fi

cd "$BACKEND"
source .venv/bin/activate

# 5. Verificar que el virtualenv activo es 3.11+
VENV_VER=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")' 2>/dev/null || echo "0.0.0")
VENV_MIN=$(python -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo 0)
if [[ $VENV_MIN -lt 11 ]]; then
  err "El virtualenv usa Python $VENV_VER (< 3.11). Ejecuta './scripts/setup.sh' para recrearlo con la versión correcta."
  deactivate
  exit 1
fi
ok "Virtualenv activado (Python $VENV_VER)."

# 6. Verificar .env
if [[ ! -f ".env" ]]; then
  err "Archivo .env no encontrado. Ejecuta primero: ./scripts/setup.sh"
  exit 1
fi

# Advertir si DATABASE_URL todavía apunta a 'db' (Docker Compose)
if grep -q "@db:" .env 2>/dev/null; then
  echo -e "${YELLOW}  ⚠  DATABASE_URL apunta a 'db' (Docker Compose). Corrigiendo a 'localhost'...${NC}"
  sed -i.bak 's|@db:|@localhost:|g' .env
  rm -f .env.bak
  ok "DATABASE_URL corregida."
fi

ok ".env cargado."
echo ""
echo -e "  ${CYAN}API disponible en:${NC}  http://localhost:8000"
echo -e "  ${CYAN}Docs interactivos:${NC}  http://localhost:8000/docs"
echo -e "  ${CYAN}Health check:${NC}       http://localhost:8000/salud"
echo -e "  ${YELLOW}Ctrl+C para detener.${NC}"
echo ""

# 7. Arrancar uvicorn con hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000