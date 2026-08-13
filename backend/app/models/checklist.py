"""
Modelo de checklist de documentos por periodo gravable.

Por qué existe esta tabla
──────────────────────────
Antes de Act. 1.1, el estado del checklist se guardaba en localStorage del
navegador. Eso implicaba:
  - Pérdida del checklist al limpiar el navegador o usar otro dispositivo.
  - Imposibilidad de que dos auxiliares vean el mismo estado.
  - Sin auditoría de quién marcó qué documento y cuándo.

Esta tabla reemplaza completamente el localStorage para el checklist.

Diseño
───────
• Un registro por (periodo_id, tipo_documento) — clave de negocio única.
• ON CONFLICT DO UPDATE: el endpoint PATCH es idempotente; marcar dos veces
  el mismo documento solo actualiza `actualizado_en` y `marcado_por_id`.
• `marcado_por_id` registra qué usuario tocó el ítem por última vez —
  trazabilidad suficiente para una firma unipersonal o pequeño equipo.

Referencias
───────────
  Act. 1.1  — creación de este módulo
  Act. 3.1  — el mapper del F210 podrá verificar si el checklist está completo
  docs/PLAN_DE_ACTIVIDADES.md — Sprint 1
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TipoDocumento(str, enum.Enum):
    """
    Documentos base requeridos para toda declaración de renta PN.
    Sincronizado con DOCS_BASE en frontend/src/admin/PanelAdmin.jsx.
    Al agregar un nuevo tipo aquí se debe agregar también en la migración
    0004 y en el arreglo DOCS_BASE del frontend.
    """
    RUT                    = "rut"
    CEDULA                 = "cedula"
    CERT_INGRESOS          = "cert_ingresos"
    EXTRACTOS              = "extractos"
    CERT_PENSION           = "cert_pension"
    CERT_SALUD             = "cert_salud"
    ESCRITURAS             = "escrituras"
    CERTIFICADO_RETENCION  = "certificado_retencion"


class DocumentoChecklist(Base):
    """
    Estado de un documento dentro del checklist de un periodo gravable.

    Restricción única: (periodo_id, tipo_documento) — un solo registro
    por tipo de documento por periodo. El endpoint usa upsert.
    """
    __tablename__ = "documento_checklist"
    __table_args__ = (
        UniqueConstraint("periodo_id", "tipo_documento", name="uq_checklist_periodo_tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    periodo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periodo_gravable.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    tipo_documento: Mapped[TipoDocumento] = mapped_column(
        Enum(
            TipoDocumento,
            values_callable=lambda e: [m.value for m in e],
            create_type=False,  # el tipo lo crea la migración 0004
        ),
        nullable=False,
    )

    # True = documento recibido y verificado por el equipo del contador.
    recibido: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Usuario que marcó/desmarcó el documento por última vez.
    marcado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
    )

    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relaciones de navegación
    periodo: Mapped["PeriodoGravable"] = relationship(back_populates="checklist")  # type: ignore[name-defined]
    marcado_por: Mapped["Usuario"] = relationship()  # type: ignore[name-defined]