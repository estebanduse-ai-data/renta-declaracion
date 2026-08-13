"""Agrega columna resultado_liquidacion a periodo_gravable

Revision ID: 0002_resultado_liquidacion
Revises: 0001_inicial
Create Date: 2026-07-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_resultado_liquidacion"
down_revision: Union[str, None] = "0001_inicial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "periodo_gravable",
        sa.Column("resultado_liquidacion", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("periodo_gravable", "resultado_liquidacion")