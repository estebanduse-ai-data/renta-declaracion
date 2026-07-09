#!/usr/bin/env python3
"""
Crea en un repositorio de GitHub una issue por cada fila de data/backlog.csv,
asignando milestone y labels automáticamente.

Requisitos:
  - Haber ejecutado antes scripts/configurar_github.py (labels y milestones deben existir)
  - GitHub CLI (`gh`) instalado y autenticado: `gh auth login`

Uso:
  python3 scripts/crear_issues.py usuario/renta-declaracion
  python3 scripts/crear_issues.py usuario/renta-declaracion --solo-fase "Fase 1 — MVP interno"
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def crear_issue(repo: str, fila: dict) -> None:
    cuerpo = (
        f"{fila['descripcion']}\n\n"
        f"**Épica:** {fila['epic']}\n"
        f"**Prioridad:** {fila['prioridad']}\n\n"
        f"Generada desde `data/backlog.csv` — ver `docs/PLAN_DE_TRABAJO.md` y "
        f"`docs/FALTANTES.md` para contexto completo."
    )
    if fila.get("nota_estado"):
        cuerpo += f"\n\n**Nota de estado:** {fila['nota_estado']}"

    comando = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", fila["titulo"],
        "--body", cuerpo,
        "--milestone", fila["milestone"],
    ]
    for label in fila["labels"].split(","):
        comando += ["--label", label.strip()]

    print("→", fila["titulo"], f"[{fila.get('estado', 'pendiente')}]")
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode != 0:
        print("  aviso:", resultado.stderr.strip())
        return

    url_issue = resultado.stdout.strip()
    print("  creada:", url_issue)

    if fila.get("estado") == "hecho":
        cierre = subprocess.run(
            [
                "gh", "issue", "close", url_issue,
                "--repo", repo,
                "--comment", "Cerrada automáticamente: ya implementada al momento de cargar el backlog.",
            ],
            capture_output=True,
            text=True,
        )
        if cierre.returncode == 0:
            print("  cerrada automáticamente (ya estaba hecha)")
        else:
            print("  aviso al cerrar:", cierre.stderr.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="usuario/repositorio en GitHub")
    parser.add_argument("--solo-fase", default=None, help='Ej: "Fase 1 — MVP interno"')
    args = parser.parse_args()

    ruta = RAIZ / "data" / "backlog.csv"
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    if args.solo_fase:
        filas = [f for f in filas if f["milestone"] == args.solo_fase]

    print(f"Creando {len(filas)} issues en {args.repo} …\n")
    for fila in filas:
        crear_issue(args.repo, fila)

    print("\nListo. Revisa la pestaña Issues del repositorio.")


if __name__ == "__main__":
    main()
