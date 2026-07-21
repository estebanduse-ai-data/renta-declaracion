#!/usr/bin/env bash
# =============================================================================
# start_frontend.sh — Levanta la interfaz React con Vite en modo desarrollo
#
# Uso:
#   ./scripts/start_frontend.sh
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
FRONTEND="$ROOT/frontend"

echo -e "\n${BOLD}${CYAN}══ Frontend — React + Vite (npm run dev) ══${NC}\n"

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  err "node_modules no encontrado en frontend/. Ejecuta primero: ./scripts/setup.sh"
  exit 1
fi
ok "node_modules presente."

cd "$FRONTEND"

echo ""
echo -e "  ${CYAN}Interfaz disponible en:${NC}  http://localhost:5173"
echo -e "  ${YELLOW}Ctrl+C para detener.${NC}"
echo ""

npm run dev
