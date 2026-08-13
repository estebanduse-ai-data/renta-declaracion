"""
Parche al modelo PeriodoGravable: agrega la columna resultado_liquidacion (JSONB).
Este archivo muestra solo el modelo completo corregido para reemplazar declarante.py.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Declarante(Base):
    __tablename__ = "declarante"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nit: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    digito_verificacion: Mapped[str] = mapped_column(String(1))
    primer_nombre: Mapped[str] = mapped_column(String(100))
    primer_apellido: Mapped[str] = mapped_column(String(100))
    actividad_economica: Mapped[str] = mapped_column(String(10))
    contador_asignado_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    periodos: Mapped[list["PeriodoGravable"]] = relationship(back_populates="declarante")


class PeriodoGravable(Base):
    __tablename__ = "periodo_gravable"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    declarante_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("declarante.id"))
    anio: Mapped[int]
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    # estado: borrador | en_revision | presentado

    patrimonio_bruto: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    pasivos: Mapped[float] = mapped_column(Numeric(18, 2), default=0)

    # Resultado de la última liquidación calculada para este periodo.
    # None si aún no se ha calculado. Se sobreescribe en cada nuevo cálculo
    # (no se guarda historial aquí — para historial usar auditoria_cambio).
    resultado_liquidacion: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    declarante: Mapped["Declarante"] = relationship(back_populates="periodos")

    # Act. 1.2 — detalle de ingresos y deducciones por rubro.
    # Se limpian y reescriben en cada recálculo del wizard.
    # Ver app/models/ingreso_deduccion.py para la estructura completa.
    ingresos_cedulares: Mapped[list["IngresoCedular"]] = relationship(  # type: ignore[name-defined]
        back_populates="periodo",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    deducciones: Mapped[list["Deduccion"]] = relationship(  # type: ignore[name-defined]
        back_populates="periodo",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Act. 1.1 — checklist de documentos persistido en BD (reemplaza localStorage).
    # Ver app/models/checklist.py para la estructura completa.
    checklist: Mapped[list["DocumentoChecklist"]] = relationship(  # type: ignore[name-defined]
        back_populates="periodo",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )