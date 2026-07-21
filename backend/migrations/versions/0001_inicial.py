"""esquema inicial: usuarios, declarantes, configuracion, auditoria

Revision ID: 0001_inicial
Revises:
Create Date: 2026-07-09

Nota: esta migración se escribió a mano (no con `alembic revision
--autogenerate`) porque este entorno de desarrollo no tiene acceso a una
base de datos PostgreSQL real ni a internet para instalar Alembic. Antes de
usarla en un entorno real, se recomienda:

    alembic upgrade head          # aplicarla
    alembic check                 # (Alembic 1.13+) confirmar que coincide
                                   # con el estado actual de los modelos

y si `alembic check` reporta diferencias, generar una migración adicional
con `alembic revision --autogenerate -m "ajustes"` en vez de editar esta.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_inicial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create_type=False evita que SQLAlchemy emita un segundo CREATE TYPE
    # automáticamente al disparar el evento before_create de la tabla.
    # La creación la hacemos nosotros explícitamente con IF NOT EXISTS.
    rol_usuario = postgresql.ENUM(
        "admin", "contador", "auxiliar",
        name="rolusuario",
        create_type=False,
    )
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE rolusuario AS ENUM ('admin', 'contador', 'auxiliar');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.create_table(
        "usuario",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", rol_usuario, nullable=False, server_default="auxiliar"),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)

    op.create_table(
        "declarante",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nit", sa.String(10), nullable=False),
        sa.Column("digito_verificacion", sa.String(1), nullable=False),
        sa.Column("primer_nombre", sa.String(100), nullable=False),
        sa.Column("primer_apellido", sa.String(100), nullable=False),
        sa.Column("actividad_economica", sa.String(10), nullable=False),
        sa.Column("contador_asignado_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("creado_en", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_declarante_nit", "declarante", ["nit"], unique=True)

    op.create_table(
        "periodo_gravable",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "declarante_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("declarante.id"),
            nullable=False,
        ),
        sa.Column("anio", sa.Integer, nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="borrador"),
        sa.Column("patrimonio_bruto", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("pasivos", sa.Numeric(18, 2), nullable=False, server_default="0"),
    )
    op.create_unique_constraint(
        "uq_periodo_por_declarante_anio", "periodo_gravable", ["declarante_id", "anio"]
    )

    op.create_table(
        "parametro_tributario",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("anio", sa.Integer, nullable=False),
        sa.Column("valores", postgresql.JSONB, nullable=False),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "creado_por_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"), nullable=True
        ),
        sa.Column("creado_en", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("nota", sa.String(500), nullable=True),
    )
    op.create_index("ix_parametro_tributario_anio", "parametro_tributario", ["anio"])
    op.execute(
        "CREATE UNIQUE INDEX uq_un_solo_parametro_activo_por_anio "
        "ON parametro_tributario (anio) WHERE activo = true"
    )

    op.create_table(
        "trm_diaria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("valor", sa.Numeric(12, 4), nullable=False),
        sa.Column("fuente", sa.String(100), nullable=False, server_default="manual"),
        sa.Column(
            "creado_por_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"), nullable=True
        ),
        sa.Column("creado_en", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_trm_diaria_fecha", "trm_diaria", ["fecha"], unique=True)

    op.create_table(
        "tasa_interes_mora",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vigente_desde", sa.Date, nullable=False),
        sa.Column("vigente_hasta", sa.Date, nullable=True),
        sa.Column("tasa_diaria", sa.Numeric(10, 8), nullable=False),
        sa.Column("tasa_efectiva_anual_referencia", sa.Numeric(6, 4), nullable=True),
        sa.Column(
            "fuente",
            sa.String(200),
            nullable=False,
            server_default="Superintendencia Financiera de Colombia",
        ),
        sa.Column(
            "creado_por_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"), nullable=True
        ),
        sa.Column("creado_en", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_tasa_interes_mora_vigente_desde", "tasa_interes_mora", ["vigente_desde"])

    op.create_table(
        "auditoria_cambio",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"), nullable=True
        ),
        sa.Column("entidad", sa.String(100), nullable=False),
        sa.Column("entidad_id", sa.String(100), nullable=False),
        sa.Column("accion", sa.String(20), nullable=False),
        sa.Column("valores_anteriores", postgresql.JSONB, nullable=True),
        sa.Column("valores_nuevos", postgresql.JSONB, nullable=True),
        sa.Column("creado_en", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("auditoria_cambio")
    op.drop_table("tasa_interes_mora")
    op.drop_table("trm_diaria")
    op.execute("DROP INDEX IF EXISTS uq_un_solo_parametro_activo_por_anio")
    op.drop_table("parametro_tributario")
    op.drop_table("periodo_gravable")
    op.drop_table("declarante")
    op.drop_table("usuario")
    op.execute("DROP TYPE IF EXISTS rolusuario")