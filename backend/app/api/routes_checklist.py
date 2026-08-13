"""
Router: /declarantes/{declarante_id}/periodos/{periodo_id}/checklist

Endpoints para gestionar el checklist de documentos de un periodo gravable.
Reemplaza el localStorage del frontend por persistencia en BD (Act. 1.1).

Diseño de la API
─────────────────
GET  /checklist         → devuelve todos los ítems del periodo (inicializa los
                          faltantes como recibido=False sin necesidad de que el
                          frontend los cree uno a uno).
PATCH /checklist/{tipo} → toggle: invierte el estado de recibido y registra
                          quién lo tocó. Idempotente y seguro para doble clic.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol, obtener_usuario_actual
from app.db.session import get_db
from app.models.checklist import DocumentoChecklist, TipoDocumento
from app.models.declarante import Declarante, PeriodoGravable
from app.models.usuario import RolUsuario, Usuario

router = APIRouter(
    prefix="/declarantes/{declarante_id}/periodos/{periodo_id}/checklist",
    tags=["checklist"],
    dependencies=[
        Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR))
    ],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_periodo_o_404(
    declarante_id: uuid.UUID,
    periodo_id: uuid.UUID,
    db: Session,
) -> PeriodoGravable:
    """Valida que el periodo pertenece al declarante indicado."""
    periodo = (
        db.query(PeriodoGravable)
        .join(Declarante)
        .filter(
            PeriodoGravable.id == periodo_id,
            Declarante.id == declarante_id,
        )
        .first()
    )
    if not periodo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Periodo no encontrado para el declarante indicado.",
        )
    return periodo


def _inicializar_faltantes(periodo_id: uuid.UUID, db: Session) -> None:
    """
    Crea registros con recibido=False para los tipos de documento que
    aún no existen en la BD. Permite que el GET siempre devuelva los
    8 tipos, sin que el frontend tenga que crearlos manualmente.
    """
    existentes = {
        r.tipo_documento
        for r in db.query(DocumentoChecklist.tipo_documento)
        .filter(DocumentoChecklist.periodo_id == periodo_id)
        .all()
    }
    faltantes = [t for t in TipoDocumento if t not in existentes]
    if faltantes:
        db.add_all([
            DocumentoChecklist(
                periodo_id=periodo_id,
                tipo_documento=tipo,
                recibido=False,
            )
            for tipo in faltantes
        ])
        db.commit()


# ── Schemas de respuesta ───────────────────────────────────────────────────────

class ItemChecklist(BaseModel):
    id: uuid.UUID
    tipo_documento: TipoDocumento
    recibido: bool
    marcado_por_id: uuid.UUID | None
    actualizado_en: datetime

    class Config:
        from_attributes = True


class RespuestaChecklist(BaseModel):
    periodo_id: uuid.UUID
    items: list[ItemChecklist]
    total: int
    recibidos: int
    porcentaje: int


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=RespuestaChecklist)
def obtener_checklist(
    declarante_id: uuid.UUID,
    periodo_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RespuestaChecklist:
    """
    Devuelve el estado completo del checklist para el periodo.
    Si algún tipo de documento no tiene registro aún, lo inicializa
    como recibido=False antes de responder.
    """
    _get_periodo_o_404(declarante_id, periodo_id, db)
    _inicializar_faltantes(periodo_id, db)

    items = (
        db.query(DocumentoChecklist)
        .filter(DocumentoChecklist.periodo_id == periodo_id)
        .order_by(DocumentoChecklist.tipo_documento)
        .all()
    )
    recibidos = sum(1 for i in items if i.recibido)
    total = len(items)

    return RespuestaChecklist(
        periodo_id=periodo_id,
        items=items,
        total=total,
        recibidos=recibidos,
        porcentaje=round((recibidos / total) * 100) if total else 0,
    )


@router.patch("/{tipo_documento}", response_model=ItemChecklist)
def toggle_documento(
    declarante_id: uuid.UUID,
    periodo_id: uuid.UUID,
    tipo_documento: TipoDocumento,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> ItemChecklist:
    """
    Invierte el estado `recibido` del tipo de documento indicado.
    Registra el usuario que realizó el cambio y la fecha/hora (UTC).
    Idempotente: dos llamadas consecutivas devuelven estados opuestos.
    """
    _get_periodo_o_404(declarante_id, periodo_id, db)

    item = (
        db.query(DocumentoChecklist)
        .filter(
            DocumentoChecklist.periodo_id == periodo_id,
            DocumentoChecklist.tipo_documento == tipo_documento,
        )
        .first()
    )

    if not item:
        # Primera vez que se toca este tipo — crear directamente como True
        item = DocumentoChecklist(
            periodo_id=periodo_id,
            tipo_documento=tipo_documento,
            recibido=True,
            marcado_por_id=usuario.id,
            actualizado_en=datetime.now(timezone.utc),
        )
        db.add(item)
    else:
        item.recibido = not item.recibido
        item.marcado_por_id = usuario.id
        item.actualizado_en = datetime.now(timezone.utc)
        db.add(item)

    db.commit()
    db.refresh(item)
    return item