#!/usr/bin/env bash
# =============================================================================
# dev.sh — Sesión de desarrollo diaria (arranca backend y frontend juntos)
#
# Levanta la BD si está detenida, luego abre backend y frontend en
# tabs/panes separados de la terminal.
#
# Detecta automáticamente iTerm2 (macOS), GNOME Terminal, Kitty y tmux.
# Si no detecta ninguno, imprime los comandos para correrlos manualmente.
#
# Uso:
#   ./scripts/dev.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✔  ${NC}$*"; }
info() { echo -e "${CYAN}  →  ${NC}$*"; }
warn() { echo -e "${YELLOW}  ⚠  ${NC}$*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "\n${BOLD}${CYAN}══ dev.sh — Sesión de desarrollo ══${NC}\n"

# ── 1. Asegurar que la BD esté corriendo ─────────────────────────────────────
"$SCRIPT_DIR/db.sh" start

# ── 2. Verificar que setup ya se corrió ──────────────────────────────────────
if [[ ! -d "$ROOT/backend/.venv" ]]; then
  warn "Virtualenv no encontrado. Ejecuta primero: ./scripts/setup.sh"
  exit 1
fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  warn "node_modules no encontrado. Ejecuta primero: ./scripts/setup.sh"
  exit 1
fi

echo ""
echo -e "  ${GREEN}BD lista.${NC} Levantando backend y frontend...\n"

# ── 3. Detectar el entorno de terminal y abrir en paralelo ───────────────────

BACKEND_CMD="$SCRIPT_DIR/start_backend.sh"
FRONTEND_CMD="$SCRIPT_DIR/start_frontend.sh"

# ── tmux ──────────────────────────────────────────────────────────────────────
if [[ -n "${TMUX:-}" ]]; then
  info "tmux detectado — abriendo ventanas separadas."
  tmux new-window -n "renta-backend" "bash '$BACKEND_CMD'; bash"
  tmux new-window -n "renta-frontend" "bash '$FRONTEND_CMD'; bash"
  ok "Backend en ventana 'renta-backend', frontend en 'renta-frontend'."
  echo -e "\n  ${CYAN}Cambia de ventana con:  Ctrl+b + n  (siguiente) / Ctrl+b + p  (anterior)${NC}"

# ── macOS: iTerm2 ─────────────────────────────────────────────────────────────
elif [[ "$OSTYPE" == "darwin"* ]] && command -v osascript &>/dev/null && \
     osascript -e 'tell application "iTerm2" to get name' &>/dev/null 2>&1; then
  info "iTerm2 detectado — abriendo tabs separados."
  osascript <<EOF
tell application "iTerm2"
  tell current window
    create tab with default profile
    tell current session
      write text "bash '$BACKEND_CMD'"
    end tell
    create tab with default profile
    tell current session
      write text "bash '$FRONTEND_CMD'"
    end tell
  end tell
end tell
EOF
  ok "Backend y frontend abiertos en tabs de iTerm2."

# ── macOS: Terminal.app ───────────────────────────────────────────────────────
elif [[ "$OSTYPE" == "darwin"* ]] && command -v osascript &>/dev/null; then
  info "Terminal.app detectado — abriendo ventanas separadas."
  osascript <<EOF
tell application "Terminal"
  do script "bash '$BACKEND_CMD'"
  do script "bash '$FRONTEND_CMD'"
end tell
EOF
  ok "Backend y frontend abiertos en ventanas de Terminal."

# ── Kitty ─────────────────────────────────────────────────────────────────────
elif [[ -n "${KITTY_WINDOW_ID:-}" ]]; then
  info "Kitty detectado — abriendo tabs separados."
  kitty @ new-window --new-tab --tab-title "backend"  bash "$BACKEND_CMD"
  kitty @ new-window --new-tab --tab-title "frontend" bash "$FRONTEND_CMD"
  ok "Backend y frontend abiertos en tabs de Kitty."

# ── GNOME Terminal ────────────────────────────────────────────────────────────
elif command -v gnome-terminal &>/dev/null; then
  info "GNOME Terminal detectado — abriendo tabs separados."
  gnome-terminal \
    --tab --title="renta-backend"  -- bash -c "bash '$BACKEND_CMD'; exec bash" \
    --tab --title="renta-frontend" -- bash -c "bash '$FRONTEND_CMD'; exec bash"
  ok "Backend y frontend abiertos en GNOME Terminal."

# ── Fallback: instrucciones manuales ─────────────────────────────────────────
else
  warn "No se detectó una terminal compatible con apertura automática."
  echo ""
  echo -e "  Abre ${BOLD}dos terminales${NC} en la raíz del proyecto y ejecuta:"
  echo ""
  echo -e "  ${CYAN}# Terminal 1 — Backend${NC}"
  echo -e "  ${BOLD}./scripts/start_backend.sh${NC}"
  echo ""
  echo -e "  ${CYAN}# Terminal 2 — Frontend${NC}"
  echo -e "  ${BOLD}./scripts/start_frontend.sh${NC}"
  echo ""
fi

echo ""
echo -e "  URLs:"
echo -e "  ${CYAN}http://localhost:5173${NC}       → Interfaz web"
echo -e "  ${CYAN}http://localhost:8000/docs${NC}  → API docs"
echo ""
