"""0005 — tabla usuario_rol (muchos a muchos, aditiva)

Revision ID: 0005_usuario_rol
Revises:     0004_documento_checklist
Create Date: 2026-07-30

Por qué esta migración es aditiva y no reemplaza usuario.rol
──────────────────────────────────────────────────────────────
La columna `usuario.rol` (Enum escalar) NO se elimina en esta migración.
Hay tres razones:

  1. El token JWT actual incluye `"rol": "admin"` (singular). El frontend
     lo lee en sesion.rol. Eliminar la columna rompería el login.

  2. Los endpoints existentes usan `usuario.rol` directamente en las
     dependencias de `requiere_rol()`. Migrar esos checks al modelo nuevo
     requiere coordinación con cada router — se hace en Act. 2F.2.

  3. Si algo sale mal, el downgrade() de esta migración elimina solo la
     tabla nueva y deja el sistema exactamente como estaba.

Estrategia de convivencia
──────────────────────────
  • `usuario_rol` almacena los roles *adicionales* de cada usuario.
  • `permisos.py` lee primero `usuario.rol` (columna original) y luego
    hace UNION con los roles en `usuario_rol`.
  • Un usuario con rol=ADMIN y una fila usuario_rol(rol=CONTADOR) tiene
    efectivamente ambos roles — sin tocar el token ni el login.

Datos sembrados en upgrade()
──────────────────────────────
Al crear la tabla, `upgrade()` siembra el rol primario de cada usuario
existente como su primer registro en `usuario_rol`. Esto garantiza que
el nuevo sistema de permisos (que lee `usuario_rol`) siga funcionando
correctamente para usuarios ya creados, sin requerir intervención manual.

Cadena de migraciones
──────────────────────
0001 → 33827e5c → 0002 → 4c32c83f → 0003 → 0004 → 0005 (HEAD)
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_usuario_rol"
down_revision = "0004_documento_checklist"
branch_labels = None
depends_on = None

# Valores válidos del enum de rol — deben coincidir con RolUsuario en models/usuario.py
ROLES_VALIDOS = ("admin", "contador", "auxiliar")


def upgrade() -> None:
    # ── 1. Crear tabla usuario_rol ─────────────────────────────────────────────
    # Usamos DDL puro (op.execute) para crear el CHECK CONSTRAINT en el enum
    # sin depender de sa.Enum(create_type=True), que con psycopg3 puede emitir
    # un CREATE TYPE duplicado. Ver ERR-001 en docs/ERRORES_Y_LECCIONES.md.
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS usuario_rol (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            usuario_id  UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
            rol         VARCHAR(20) NOT NULL
                            CHECK (rol IN ('admin', 'contador', 'auxiliar')),
            creado_en   TIMESTAMP NOT NULL DEFAULT NOW(),

            -- Un usuario no puede tener el mismo rol dos veces
            CONSTRAINT uq_usuario_rol UNIQUE (usuario_id, rol)
        )
    """))

    # Índice para lookup por usuario_id (el más frecuente en permisos.py)
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_usuario_rol_usuario_id
        ON usuario_rol (usuario_id)
    """))

    # ── 2. Sembrar los roles primarios de usuarios existentes ─────────────────
    # Al crear la tabla, copiamos el rol escalar existente de cada usuario
    # como su primer registro en usuario_rol. Así los usuarios existentes
    # tienen su rol reflejado en las dos columnas desde el primer momento.
    op.execute(sa.text("""
        INSERT INTO usuario_rol (usuario_id, rol)
        SELECT id, rol::text
        FROM usuario
        WHERE activo = TRUE
        ON CONFLICT (usuario_id, rol) DO NOTHING
    """))


def downgrade() -> None:
    # Eliminar solo la tabla nueva — usuario.rol queda intacto
    op.execute(sa.text("DROP TABLE IF EXISTS usuario_rol"))