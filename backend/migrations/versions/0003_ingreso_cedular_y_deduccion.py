"""ingreso_cedular_y_deduccion

Crea las tablas ingreso_cedular y deduccion con sus tipos ENUM.

Act. 1.2 — ver docs/PLAN_DE_ACTIVIDADES.md

Fix v4: DDL 100% puro via op.execute(). Se evita completamente sa.Enum
en op.create_table porque SQLAlchemy con psycopg3 emite CREATE TYPE
propio ignorando create_type=False en ciertos contextos. Usar TEXT con
CHECK CONSTRAINT es más portable; la validación la hace el motor igual.

Revision ID: 0003_ingreso_cedular_y_deduccion
Revises: 4c32c83f5aa4
Create Date: 2026-07-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_ingreso_cedular_y_deduccion"
down_revision: Union[str, None] = "4c32c83f5aa4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIPOS_INGRESO = [
    "salarios_y_honorarios", "honorarios_sin_empleados", "servicios",
    "comisiones", "rendimientos_financieros", "arrendamientos", "regalias",
    "explotacion_imagen", "compensaciones", "pensiones_nacionales",
    "pensiones_extranjeras", "dividendos_gravados", "dividendos_no_gravados",
    "ingreso_no_constitutivo", "renta_exenta_laboral",
    "renta_exenta_cesantias", "renta_exenta_otro",
]

TIPOS_DEDUCCION = [
    "intereses_vivienda", "intereses_icetex", "medicina_prepagada",
    "dependientes", "afc", "pension_voluntaria", "donaciones",
    "gravamen_movimientos_financieros", "otra",
]


def _vals(lista):
    return ", ".join(f"'{v}'" for v in lista)


def upgrade() -> None:
    # ── 1. ENUMs — solo si no existen ─────────────────────────────────────────
    # Usamos op.execute con DO $$ para que sea idempotente.
    # No usamos sa.Enum en absoluto: con psycopg3 ignora create_type=False.
    op.execute(sa.text(f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipoingresocedular') THEN
                CREATE TYPE tipoingresocedular AS ENUM ({_vals(TIPOS_INGRESO)});
            END IF;
        END $$
    """))
    op.execute(sa.text(f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipodeduccion') THEN
                CREATE TYPE tipodeduccion AS ENUM ({_vals(TIPOS_DEDUCCION)});
            END IF;
        END $$
    """))

    # ── 2. Tabla ingreso_cedular — DDL puro ────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE ingreso_cedular (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            periodo_id      UUID NOT NULL REFERENCES periodo_gravable(id) ON DELETE CASCADE,
            tipo            tipoingresocedular NOT NULL,
            monto_pesos     NUMERIC(18, 2) NOT NULL,
            descripcion     VARCHAR(300),
            creado_en       TIMESTAMP NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX ix_ingreso_cedular_periodo_id ON ingreso_cedular (periodo_id)"
    ))

    # ── 3. Tabla deduccion — DDL puro ──────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE deduccion (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            periodo_id              UUID NOT NULL REFERENCES periodo_gravable(id) ON DELETE CASCADE,
            tipo                    tipodeduccion NOT NULL,
            monto_informado_pesos   NUMERIC(18, 2) NOT NULL,
            monto_efectivo_pesos    NUMERIC(18, 2) NOT NULL,
            tope_aplicado           BOOLEAN NOT NULL DEFAULT false,
            tope_valor_pesos        NUMERIC(18, 2),
            descripcion             VARCHAR(300),
            creado_en               TIMESTAMP NOT NULL DEFAULT now()
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX ix_deduccion_periodo_id ON deduccion (periodo_id)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS deduccion"))
    op.execute(sa.text("DROP TABLE IF EXISTS ingreso_cedular"))
    op.execute(sa.text("DROP TYPE IF EXISTS tipodeduccion"))
    op.execute(sa.text("DROP TYPE IF EXISTS tipoingresocedular"))