#!/usr/bin/env bash
# =============================================================================
# db.sh — Gestión del contenedor PostgreSQL de desarrollo
#
# Comandos:
#   start     Inicia el contenedor (si existe pero está detenido)
#   stop      Detiene el contenedor (datos persisten)
#   restart   Detiene y vuelve a iniciar
#   status    Muestra el estado actual
#   destroy   Elimina el contenedor Y el volumen de datos (¡irreversible!)
#   recreate  destroy + crea el contenedor limpio (BD vacía)
#   logs      Muestra los logs en tiempo real
#   psql      Abre una sesión psql dentro del contenedor
#
# Uso:
#   ./scripts/db.sh start
#   ./scripts/db.sh stop
#   ./scripts/db.sh restart
#   ./scripts/db.sh status
#   ./scripts/db.sh destroy       ← borra todos los datos
#   ./scripts/db.sh recreate      ← BD completamente limpia
#   ./scripts/db.sh logs
#   ./scripts/db.sh psql
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✔  ${NC}$*"; }
info() { echo -e "${CYAN}  →  ${NC}$*"; }
warn() { echo -e "${YELLOW}  ⚠  ${NC}$*"; }
err()  { echo -e "${RED}  ✖  ${NC}$*" >&2; }

CONTAINER="renta-db"
PG_USER="renta"
PG_PASSWORD="renta"
PG_DB="renta_declaracion"
PG_PORT="5432"

COMANDO="${1:-status}"

# ── Funciones internas ────────────────────────────────────────────────────────

container_existe() {
  docker ps -a --filter "name=^${CONTAINER}$" --format "{{.Names}}" | grep -q "^${CONTAINER}$"
}

container_corriendo() {
  docker ps --filter "name=^${CONTAINER}$" --filter "status=running" --format "{{.Names}}" | grep -q "^${CONTAINER}$"
}

esperar_postgres() {
  info "Esperando que PostgreSQL acepte conexiones..."
  for i in {1..15}; do
    if docker exec "$CONTAINER" pg_isready -U "$PG_USER" -q 2>/dev/null; then
      ok "PostgreSQL listo en puerto $PG_PORT."; return 0
    fi
    sleep 1
  done
  err "PostgreSQL no respondió en 15 segundos."
  return 1
}

crear_contenedor() {
  info "Creando contenedor $CONTAINER..."
  docker run -d \
    --name "$CONTAINER" \
    -e POSTGRES_USER="$PG_USER" \
    -e POSTGRES_PASSWORD="$PG_PASSWORD" \
    -e POSTGRES_DB="$PG_DB" \
    -p "${PG_PORT}:5432" \
    --restart unless-stopped \
    postgres:16-alpine
  ok "Contenedor $CONTAINER creado."
}

# ── Comandos ─────────────────────────────────────────────────────────────────

case "$COMANDO" in

  start)
    echo -e "\n${BOLD}${CYAN}══ db.sh start ══${NC}\n"
    if container_corriendo; then
      ok "$CONTAINER ya está corriendo."
    elif container_existe; then
      info "Iniciando contenedor detenido..."
      docker start "$CONTAINER"
      esperar_postgres
    else
      warn "Contenedor no existe. Creándolo..."
      crear_contenedor
      esperar_postgres
    fi
    ;;

  stop)
    echo -e "\n${BOLD}${CYAN}══ db.sh stop ══${NC}\n"
    if container_corriendo; then
      info "Deteniendo $CONTAINER..."
      docker stop "$CONTAINER"
      ok "$CONTAINER detenido. Los datos persisten."
    else
      warn "$CONTAINER no está corriendo."
    fi
    ;;

  restart)
    echo -e "\n${BOLD}${CYAN}══ db.sh restart ══${NC}\n"
    if container_corriendo; then
      info "Reiniciando $CONTAINER..."
      docker restart "$CONTAINER"
      esperar_postgres
      ok "$CONTAINER reiniciado."
    elif container_existe; then
      info "Iniciando contenedor detenido..."
      docker start "$CONTAINER"
      esperar_postgres
    else
      warn "Contenedor no existe. Creándolo..."
      crear_contenedor
      esperar_postgres
    fi
    ;;

  status)
    echo -e "\n${BOLD}${CYAN}══ db.sh status ══${NC}\n"
    if container_corriendo; then
      echo -e "  Estado:    ${GREEN}corriendo${NC}"
      docker ps --filter "name=^${CONTAINER}$" \
        --format "  Imagen:    {{.Image}}\n  Puertos:   {{.Ports}}\n  Uptime:    {{.Status}}"
    elif container_existe; then
      echo -e "  Estado:    ${YELLOW}detenido${NC} (datos persisten)"
    else
      echo -e "  Estado:    ${RED}no existe${NC}"
    fi
    echo ""
    ;;

  destroy)
    echo -e "\n${BOLD}${RED}══ db.sh destroy — OPERACIÓN IRREVERSIBLE ══${NC}\n"
    warn "Esto eliminará el contenedor $CONTAINER y TODOS los datos de la BD."
    echo -e "  ${YELLOW}¿Estás seguro? Escribe 'destruir' para confirmar:${NC} \c"
    read -r confirmacion
    if [[ "$confirmacion" != "destruir" ]]; then
      info "Operación cancelada."
      exit 0
    fi
    if container_corriendo; then
      info "Deteniendo contenedor..."
      docker stop "$CONTAINER"
    fi
    if container_existe; then
      info "Eliminando contenedor..."
      docker rm "$CONTAINER"
      ok "Contenedor eliminado."
    else
      warn "El contenedor no existía."
    fi
    # Eliminar el volumen nombrado si existe
    if docker volume ls --format "{{.Name}}" | grep -q "renta-declaracion_pgdata"; then
      info "Eliminando volumen de datos..."
      docker volume rm renta-declaracion_pgdata 2>/dev/null || true
      ok "Volumen eliminado."
    fi
    ok "BD destruida. Ejecuta './scripts/setup.sh' para empezar desde cero."
    ;;

  recreate)
    echo -e "\n${BOLD}${YELLOW}══ db.sh recreate — BD completamente limpia ══${NC}\n"
    warn "Esto eliminará todos los datos y creará una BD vacía."
    echo -e "  ${YELLOW}¿Estás seguro? Escribe 'recrear' para confirmar:${NC} \c"
    read -r confirmacion
    if [[ "$confirmacion" != "recrear" ]]; then
      info "Operación cancelada."
      exit 0
    fi

    # Destruir
    if container_corriendo; then docker stop "$CONTAINER"; fi
    if container_existe;    then docker rm   "$CONTAINER"; fi
    docker volume rm renta-declaracion_pgdata 2>/dev/null || true
    ok "Contenedor y datos eliminados."

    # Crear
    crear_contenedor
    esperar_postgres

    echo ""
    echo -e "  ${CYAN}BD recreada. Para aplicar migraciones y sembrar datos:${NC}"
    echo -e "  ${BOLD}./scripts/migrate.sh --sembrar${NC}"
    echo ""
    ;;

  logs)
    echo -e "\n${BOLD}${CYAN}══ db.sh logs — PostgreSQL ══${NC}\n"
    if ! container_existe; then
      err "El contenedor $CONTAINER no existe."
      exit 1
    fi
    info "Ctrl+C para salir."
    echo ""
    docker logs -f "$CONTAINER"
    ;;

  psql)
    echo -e "\n${BOLD}${CYAN}══ db.sh psql — Sesión interactiva ══${NC}\n"
    if ! container_corriendo; then
      err "$CONTAINER no está corriendo. Usa: ./scripts/db.sh start"
      exit 1
    fi
    info "Abriendo psql como usuario '$PG_USER' en base '$PG_DB'..."
    echo -e "  ${YELLOW}\\q para salir de psql.${NC}\n"
    docker exec -it "$CONTAINER" psql -U "$PG_USER" -d "$PG_DB"
    ;;

  *)
    echo -e "\n${BOLD}Uso:${NC} ./scripts/db.sh <comando>"
    echo ""
    echo "  Comandos disponibles:"
    echo -e "    ${CYAN}start${NC}     Inicia el contenedor (lo crea si no existe)"
    echo -e "    ${CYAN}stop${NC}      Detiene el contenedor (datos persisten)"
    echo -e "    ${CYAN}restart${NC}   Reinicia el contenedor"
    echo -e "    ${CYAN}status${NC}    Muestra el estado actual"
    echo -e "    ${CYAN}destroy${NC}   ${RED}Elimina el contenedor y todos los datos (irreversible)${NC}"
    echo -e "    ${CYAN}recreate${NC}  ${YELLOW}BD limpia: destroy + crear vacía${NC}"
    echo -e "    ${CYAN}logs${NC}      Logs de PostgreSQL en tiempo real"
    echo -e "    ${CYAN}psql${NC}      Sesión interactiva de psql"
    echo ""
    exit 1
    ;;
esac
