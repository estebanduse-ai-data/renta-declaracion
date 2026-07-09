#!/usr/bin/env bash
# Crea un GitHub Project (v2) tipo tablero para el roadmap del producto y le
# agrega todas las issues abiertas del repositorio.
#
# Requisitos:
#   - GitHub CLI (`gh`) instalado y autenticado: `gh auth login`
#   - Alcance de autenticación con permisos de "project" (gh auth refresh -s project)
#
# Uso:
#   ./scripts/configurar_proyecto.sh <usuario-u-organizacion> <usuario/repositorio>
#
# Ejemplo:
#   ./scripts/configurar_proyecto.sh miusuario miusuario/renta-declaracion

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Uso: $0 <usuario-u-organizacion> <usuario/repositorio>"
  exit 1
fi

DUENIO="$1"
REPO="$2"
TITULO_PROYECTO="Renta Declaración — Roadmap"

echo "Creando el proyecto '$TITULO_PROYECTO' para $DUENIO …"
NUMERO_PROYECTO=$(gh project create --owner "$DUENIO" --title "$TITULO_PROYECTO" --format json | python3 -c "import json,sys; print(json.load(sys.stdin)['number'])")
echo "Proyecto creado: número $NUMERO_PROYECTO"

echo "Agregando columnas de estado sugeridas (Backlog, Por hacer, En progreso, En revisión, Hecho) …"
echo "Nota: gh project no permite crear campos de estado personalizados por CLI todavía;"
echo "crea las columnas manualmente en la vista del tablero en GitHub la primera vez, o usa"
echo "el campo 'Status' por defecto que Projects v2 ya trae."

echo ""
echo "Agregando todas las issues abiertas de $REPO al proyecto …"
for numero_issue in $(gh issue list --repo "$REPO" --state open --limit 500 --json number --jq '.[].number'); do
  url_issue="https://github.com/$REPO/issues/$numero_issue"
  echo "→ Agregando issue #$numero_issue"
  gh project item-add "$NUMERO_PROYECTO" --owner "$DUENIO" --url "$url_issue" >/dev/null
done

echo ""
echo "Listo. Abre https://github.com/$DUENIO?tab=projects para ver el tablero."
echo "Configura la vista de tablero agrupada por 'Status' y, opcionalmente, una segunda"
echo "vista agrupada por el label 'fase:*' para seguir el roadmap por fases."
