from sqlalchemy.orm import Session

from app.models.auditoria import AuditoriaCambio


def registrar_auditoria(
    db: Session,
    *,
    usuario_id,
    entidad: str,
    entidad_id: str,
    accion: str,
    valores_anteriores: dict | None = None,
    valores_nuevos: dict | None = None,
) -> AuditoriaCambio:
    registro = AuditoriaCambio(
        usuario_id=usuario_id,
        entidad=entidad,
        entidad_id=entidad_id,
        accion=accion,
        valores_anteriores=valores_anteriores,
        valores_nuevos=valores_nuevos,
    )
    db.add(registro)
    db.flush()
    return registro
