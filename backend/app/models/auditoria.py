"""
Auditoría de cambios — mitiga el riesgo #7 de docs/RIESGOS.md (dependencia de
una sola persona / cambios sin trazabilidad) y es un requisito explícito de
docs/PLAN_DE_TRABAJO.md para Fase 1.

Se registra especialmente cada cambio a las tablas de configuración
(`ParametroTributario`, `TRMDiaria`, `TasaInteresMora`), porque un valor mal
actualizado ahí afecta el cálculo de TODOS los declarantes, no solo uno.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditoriaCambio(Base):
    __tablename__ = "auditoria_cambio"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    entidad: Mapped[str] = mapped_column(String(100))  # ej: "parametro_tributario", "declarante"
    entidad_id: Mapped[str] = mapped_column(String(100))
    accion: Mapped[str] = mapped_column(String(20))  # crear | actualizar | eliminar | activar
    valores_anteriores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    valores_nuevos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
