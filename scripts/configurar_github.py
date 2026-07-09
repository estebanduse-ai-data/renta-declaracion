#!/usr/bin/env python3
"""
Crea en un repositorio de GitHub los labels y milestones definidos en
data/labels.csv y data/milestones.csv.

Requisitos:
  - GitHub CLI (`gh`) instalado y autenticado: `gh auth login`
  - Ejecutar desde la raíz del repositorio clonado

Uso:
  python3 scripts/configurar_github.py usuario/renta-declaracion
"""

import csv
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def ejecutar(comando: list[str]) -> None:
    print("→", " ".join(comando))
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode != 0:
        print("  aviso:", resultado.stderr.strip())
    else:
        print("  ok")


def crear_labels(repo: str) -> None:
    ruta = RAIZ / "data" / "labels.csv"
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            ejecutar(
                [
                    "gh", "label", "create", fila["nombre"],
                    "--repo", repo,
                    "--color", fila["color"],
                    "--description", fila["descripcion"],
                    "--force",
                ]
            )


def crear_milestones(repo: str) -> None:
    ruta = RAIZ / "data" / "milestones.csv"
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            ejecutar(
                [
                    "gh", "api", f"repos/{repo}/milestones",
                    "-f", f"title={fila['titulo']}",
                    "-f", f"description={fila['descripcion']} (objetivo: {fila['fecha_objetivo']})",
                ]
            )


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python3 scripts/configurar_github.py usuario/repositorio")
        sys.exit(1)
    repo = sys.argv[1]
    print(f"Configurando labels y milestones en {repo} …\n")
    crear_labels(repo)
    print()
    crear_milestones(repo)
    print("\nListo. Revisa Issues → Labels y Issues → Milestones en GitHub para confirmar.")


if __name__ == "__main__":
    main()
