"""documento_checklist

Crea la tabla documento_checklist con su tipo ENUM tipodocumento.
Reemplaza el localStorage del frontend por persistencia real en BD.

Act. 1.1 — ver docs/PLAN_DE_ACTIVIDADES.md

Fix v4: DDL 100% puro via op.execute() — mismo patrón que 0003.

Revision ID: 0004_documento_checklist
Revises: 0003_ingreso_cedular_y_deduccion
Create Date: 2026-07-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_documento_checklist"
down_revision: Union[str, None] = "0003_ingreso_cedular_y_deduccion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIPOS_DOCUMENTO = [
    "rut", "cedula", "cert_ingresos", "extractos",
    "cert_pension", "cert_salud", "escrituras", "certificado_retencion",
]


def upgrade() -> None:
    vals = ", ".join(f"'{v}'" for v in TIPOS_DOCUMENTO)

    op.execute(sa.text(f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipodocumento') THEN
                CREATE TYPE tipodocumento AS ENUM ({vals});
            END IF;
        END $$
    """))

    op.execute(sa.text("""
        CREATE TABLE documento_checklist (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            periodo_id      UUID NOT NULL REFERENCES periodo_gravable(id) ON DELETE CASCADE,
            tipo_documento  tipodocumento NOT NULL,
            recibido        BOOLEAN NOT NULL DEFAULT false,
            marcado_por_id  UUID REFERENCES usuario(id) ON DELETE SET NULL,
            actualizado_en  TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT uq_checklist_periodo_tipo UNIQUE (periodo_id, tipo_documento)
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX ix_documento_checklist_periodo_id ON documento_checklist (periodo_id)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS documento_checklist"))
    op.execute(sa.text("DROP TYPE IF EXISTS tipodocumento"))