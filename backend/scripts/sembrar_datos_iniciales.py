#!/usr/bin/env python3
"""
Siembra los datos mínimos para arrancar el sistema en un servidor nuevo:

  1. Un usuario Admin (para poder entrar y crear a los demás desde la API).
  2. El conjunto de parámetros tributarios 2025, tomado de
     app/rules_engine/parametros_2025.py, ya activo.

Requiere que las migraciones de Alembic ya se hayan aplicado
(`alembic upgrade head`) y que DATABASE_URL apunte a una base de datos
accesible.

Uso:
  python3 scripts/sembrar_datos_iniciales.py \
      --admin-email admin@ejemplo.com \
      --admin-password "una-clave-segura" \
      --admin-nombre "Nombre Apellido"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hashear_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.configuracion import ParametroTributario  # noqa: E402
from app.models.usuario import RolUsuario, Usuario  # noqa: E402
from app.rules_engine.semilla_parametros import construir_payload_parametros_2025  # noqa: E402
from app.schemas.configuracion import ParametrosTributariosPayload  # noqa: E402


def sembrar_admin(db, email: str, password: str, nombre: str) -> None:
    existente = db.query(Usuario).filter(Usuario.email == email).first()
    if existente is not None:
        print(f"El usuario Admin {email} ya existe, no se crea de nuevo.")
        return

    usuario = Usuario(
        email=email,
        nombre=nombre,
        password_hash=hashear_password(password),
        rol=RolUsuario.ADMIN,
    )
    db.add(usuario)
    db.commit()
    print(f"Usuario Admin creado: {email}")


def sembrar_parametros_2025(db) -> None:
    existente = (
        db.query(ParametroTributario)
        .filter(ParametroTributario.anio == 2025, ParametroTributario.activo.is_(True))
        .first()
    )
    if existente is not None:
        print("Ya existen parámetros tributarios activos para 2025, no se sobrescriben.")
        return

    payload_dict = construir_payload_parametros_2025()
    # Valida el payload contra el mismo esquema que usa la API — si algo en
    # parametros_2025.py quedó inconsistente, esto falla ruidosamente aquí
    # en vez de silenciosamente en producción.
    payload_validado = ParametrosTributariosPayload(**payload_dict)

    registro = ParametroTributario(
        anio=2025,
        valores=payload_validado.model_dump(mode="json"),
        activo=True,
        nota="Semilla inicial desde parametros_2025.py",
    )
    db.add(registro)
    db.commit()
    print("Parámetros tributarios 2025 sembrados y activados.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--admin-password", required=True)
    parser.add_argument("--admin-nombre", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        sembrar_admin(db, args.admin_email, args.admin_password, args.admin_nombre)
        sembrar_parametros_2025(db)
    finally:
        db.close()

    print("\nListo. Ya puedes iniciar sesión en /auth/login con el usuario Admin creado.")


if __name__ == "__main__":
    main()
