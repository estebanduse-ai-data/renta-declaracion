"""
Modelos de datos — esqueleto inicial (SQLAlchemy).

Este es un punto de partida deliberadamente mínimo: cubre lo necesario para
Datos generales y Patrimonio (ver docs/PLAN_DE_TRABAJO.md, Fase 1). Los
modelos de ingresos, deducciones y liquidación se agregan en la siguiente
iteración, siguiendo el mismo patrón.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
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
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

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

    declarante: Mapped["Declarante"] = relationship(back_populates="periodos")
