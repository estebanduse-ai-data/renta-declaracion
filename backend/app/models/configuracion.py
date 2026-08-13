"""
Configuración tributaria administrable desde el módulo de configuración
(rol Admin). Tres tablas, una por frecuencia real de cambio — ver
docs/ARQUITECTURA.md y la clasificación en el issue de esta funcionalidad:

  - ParametroTributario: un conjunto versionado de valores por año gravable
    (UVT, tarifas, topes). Cambia una vez al año, salvo reforma tributaria.
  - TRMDiaria: serie de tiempo, un valor por fecha. Cambia todos los días.
  - TasaInteresMora: vigente entre dos fechas. Cambia trimestralmente.

Ninguna de estas tablas reemplaza `backend/app/rules_engine/parametros_2025.py`:
ese módulo sigue siendo la fuente de valores por defecto / semilla para
desarrollo y para las pruebas unitarias del motor de reglas (que deben poder
correr sin base de datos, ver ADR 0001). `ParametroTributario.valores` se
inicializa a partir de ese módulo la primera vez que se crea un año, y desde
ahí el módulo de configuración es la fuente de verdad en producción.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParametroTributario(Base):
    __tablename__ = "parametro_tributario"
    __table_args__ = (
        # Índice único PARCIAL: solo restringe que exista un único registro
        # activo=True por año. Los registros históricos con activo=False
        # (versiones anteriores conservadas para auditoría) sí pueden
        # repetirse en cantidad para el mismo año sin violar nada — una
        # restricción única normal sobre (anio, activo) lo impediría por
        # error, ya que False no es NULL para efectos de unicidad.
        # Sintaxis específica de PostgreSQL (el motor de este proyecto).
        Index(
            "uq_un_solo_parametro_activo_por_anio",
            "anio",
            unique=True,
            postgresql_where=text("activo = true"),
        ),
        # Nota: si algún día se corren pruebas de integración contra SQLite en
        # vez de PostgreSQL, SQLAlchemy ignora `postgresql_where` en ese
        # dialecto y el índice se vuelve una unicidad total sobre `anio`,
        # bloqueando incluso los registros históricos inactivos. Correr las
        # pruebas de este módulo contra PostgreSQL real (o Postgres en
        # Docker), no contra SQLite.
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    anio: Mapped[int] = mapped_column(index=True)

    # Todos los valores normativos del año (UVT, tabla de tarifa, topes,
    # tarifas, factores de ajuste, etc.) en un único documento JSON validado
    # por app/schemas/configuracion.py antes de guardarse. Se prefiere JSON
    # sobre una columna por parámetro para no tener que migrar el esquema de
    # base de datos cada vez que una reforma agrega o quita un valor —
    # coherente con el principio de "parámetros como datos" del ADR 0001.
    valores: Mapped[dict] = mapped_column(JSONB)

    # Si hay más de un registro para el mismo año (por ejemplo, un borrador
    # de ajuste), solo el marcado como activo=True es el que usa el motor de
    # reglas en producción. La restricción única de arriba impide tener dos
    # activos para el mismo año.
    activo: Mapped[bool] = mapped_column(Boolean, default=False)

    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    nota: Mapped[str | None] = mapped_column(String(500), nullable=True)


class TRMDiaria(Base):
    __tablename__ = "trm_diaria"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fecha: Mapped[date] = mapped_column(Date, unique=True, index=True)
    valor: Mapped[float] = mapped_column(Numeric(12, 4))
    fuente: Mapped[str] = mapped_column(String(100), default="manual")
    # fuente: "manual" (cargada por el contador) o "banrep" (si en el futuro
    # se integra la API del Banco de la República — ver docs/FALTANTES.md).

    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class TasaInteresMora(Base):
    __tablename__ = "tasa_interes_mora"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vigente_desde: Mapped[date] = mapped_column(Date, index=True)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    tasa_diaria: Mapped[float] = mapped_column(Numeric(10, 8))
    tasa_efectiva_anual_referencia: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    fuente: Mapped[str] = mapped_column(String(200), default="Superintendencia Financiera de Colombia")

    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))