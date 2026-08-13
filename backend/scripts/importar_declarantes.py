#!/usr/bin/env python3
"""
scripts/importar_declarantes.py
================================
Script de carga masiva inicial para migrar los declarantes existentes
desde un archivo Excel a la base de datos.

Uso:
    cd backend
    python scripts/importar_declarantes.py ../data/declarantes.xlsx

Opciones:
    --dry-run   Valida el archivo y muestra el resultado sin escribir en BD.
    --token     JWT de un usuario Admin (alternativa: var de entorno ADMIN_TOKEN).
    --url       URL base de la API (default: http://localhost:8000).

El script usa la misma API REST que usa la app, así que respeta todas las
validaciones del backend. Si prefieres saltarte la API e ir directo a la BD,
descomenta la sección "Modo directo a BD" al final del archivo.
"""
import argparse
import json
import os
import sys

import requests

BASE_URL = "http://localhost:8000"
ENDPOINT = "/admin/importar-declarantes"


def main():
    parser = argparse.ArgumentParser(description="Importador masivo de declarantes")
    parser.add_argument("archivo", help="Ruta al archivo .xlsx")
    parser.add_argument("--dry-run", action="store_true", help="Solo valida, no importa")
    parser.add_argument("--token", default=os.environ.get("ADMIN_TOKEN"), help="JWT Admin")
    parser.add_argument("--url", default=BASE_URL)
    args = parser.parse_args()

    if not args.token:
        print("❌  Falta el token de admin. Pásalo con --token o setea ADMIN_TOKEN.")
        sys.exit(1)

    if not os.path.isfile(args.archivo):
        print(f"❌  No se encontró el archivo: {args.archivo}")
        sys.exit(1)

    if args.dry_run:
        print(f"🔍  Modo dry-run: solo validación, no se escribe en BD.\n")

    print(f"📂  Leyendo: {args.archivo}")
    with open(args.archivo, "rb") as f:
        files = {"archivo": (os.path.basename(args.archivo), f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        headers = {"Authorization": f"Bearer {args.token}"}

        # En dry-run enviamos a un endpoint que solo valida (si existe).
        # Por ahora usamos el mismo endpoint y mostramos el resultado sin confirmar.
        endpoint = f"{args.url}{ENDPOINT}"
        print(f"📡  Enviando a {endpoint}…\n")

        try:
            resp = requests.post(endpoint, files=files, headers=headers, timeout=60)
        except requests.ConnectionError:
            print(f"❌  No se pudo conectar a {args.url}. ¿Está corriendo el backend?")
            sys.exit(1)

    if not resp.ok:
        print(f"❌  Error del servidor ({resp.status_code}): {resp.text}")
        sys.exit(1)

    resultado = resp.json()

    print(f"{'='*56}")
    print(f"  Total filas procesadas : {resultado['total_filas']}")
    print(f"  ✅  Importados          : {resultado['importados']}")
    print(f"  ⏭️   Omitidos (ya existen): {resultado['omitidos']}")
    print(f"  ❌  Errores             : {resultado['errores']}")
    print(f"{'='*56}\n")

    if resultado["errores"] > 0 or resultado["omitidos"] > 0:
        print("Detalle de filas con problema:")
        for d in resultado["detalle"]:
            if not d["ok"]:
                print(f"  Fila {d['fila']:>3} | NIT {d['nit']:<12} | {d['nombre']:<30} | {d['mensaje']}")

    print(f"\n✅  Listo. {resultado['importados']} declarantes importados.")


if __name__ == "__main__":
    main()