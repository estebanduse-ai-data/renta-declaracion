#!/usr/bin/env bash
# Aplica las migraciones pendientes y luego arranca la API. Se usa como
# entrypoint del contenedor backend (ver Dockerfile) para que cada
# despliegue (incluido el primero) deje el esquema de base de datos al día
# sin un paso manual aparte.
set -euo pipefail

echo "Aplicando migraciones de Alembic..."
alembic upgrade head

echo "Iniciando la API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
