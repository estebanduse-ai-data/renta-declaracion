import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol
from app.db.session import get_db
from app.models.declarante import Declarante, PeriodoGravable
from app.models.usuario import RolUsuario, Usuario
from app.schemas.declarante import (
    ActualizarDeclarante,
    ActualizarPeriodoGravable,
    CrearDeclarante,
    CrearPeriodoGravable,
    RespuestaDeclarante,
    RespuestaPeriodoGravable,
)
from app.services.auditoria_service import registrar_auditoria

router = APIRouter(
    prefix="/declarantes",
    tags=["declarantes"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR))],
)


@router.get("", response_model=list[RespuestaDeclarante])
def listar_declarantes(db: Session = Depends(get_db)) -> list[Declarante]:
    return db.query(Declarante).order_by(Declarante.primer_apellido).all()


@router.post("", response_model=RespuestaDeclarante, status_code=status.HTTP_201_CREATED)
def crear_declarante(
    solicitud: CrearDeclarante,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR)),
) -> Declarante:
    existente = db.query(Declarante).filter(Declarante.nit == solicitud.nit).first()
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe un declarante con ese NIT."
        )

    declarante = Declarante(**solicitud.model_dump())
    db.add(declarante)
    db.flush()
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        entidad="declarante",
        entidad_id=str(declarante.id),
        accion="crear",
        valores_nuevos=solicitud.model_dump(),
    )
    db.commit()
    db.refresh(declarante)
    return declarante


@router.get("/{declarante_id}", response_model=RespuestaDeclarante)
def obtener_declarante(declarante_id: uuid.UUID, db: Session = Depends(get_db)) -> Declarante:
    declarante = db.query(Declarante).filter(Declarante.id == declarante_id).first()
    if declarante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Declarante no encontrado.")
    return declarante


@router.patch("/{declarante_id}", response_model=RespuestaDeclarante)
def actualizar_declarante(
    declarante_id: uuid.UUID,
    solicitud: ActualizarDeclarante,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR)),
) -> Declarante:
    declarante = db.query(Declarante).filter(Declarante.id == declarante_id).first()
    if declarante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Declarante no encontrado.")

    valores_anteriores = {
        "primer_nombre": declarante.primer_nombre,
        "primer_apellido": declarante.primer_apellido,
        "actividad_economica": declarante.actividad_economica,
    }
    datos = solicitud.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(declarante, campo, valor)

    db.add(declarante)
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        entidad="declarante",
        entidad_id=str(declarante.id),
        accion="actualizar",
        valores_anteriores=valores_anteriores,
        valores_nuevos=datos,
    )
    db.commit()
    db.refresh(declarante)
    return declarante


# --- Periodos gravables ------------------------------------------------


@router.post(
    "/{declarante_id}/periodos",
    response_model=RespuestaPeriodoGravable,
    status_code=status.HTTP_201_CREATED,
)
def crear_periodo(
    declarante_id: uuid.UUID, solicitud: CrearPeriodoGravable, db: Session = Depends(get_db)
) -> PeriodoGravable:
    declarante = db.query(Declarante).filter(Declarante.id == declarante_id).first()
    if declarante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Declarante no encontrado.")

    existente = (
        db.query(PeriodoGravable)
        .filter(
            PeriodoGravable.declarante_id == declarante_id, PeriodoGravable.anio == solicitud.anio
        )
        .first()
    )
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Este declarante ya tiene un periodo gravable {solicitud.anio}.",
        )

    periodo = PeriodoGravable(declarante_id=declarante_id, **solicitud.model_dump())
    db.add(periodo)
    db.commit()
    db.refresh(periodo)
    return periodo


@router.get("/{declarante_id}/periodos", response_model=list[RespuestaPeriodoGravable])
def listar_periodos(declarante_id: uuid.UUID, db: Session = Depends(get_db)) -> list[PeriodoGravable]:
    return (
        db.query(PeriodoGravable)
        .filter(PeriodoGravable.declarante_id == declarante_id)
        .order_by(PeriodoGravable.anio.desc())
        .all()
    )


@router.patch("/{declarante_id}/periodos/{periodo_id}", response_model=RespuestaPeriodoGravable)
def actualizar_periodo(
    declarante_id: uuid.UUID,
    periodo_id: uuid.UUID,
    solicitud: ActualizarPeriodoGravable,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR)),
) -> PeriodoGravable:
    periodo = (
        db.query(PeriodoGravable)
        .filter(PeriodoGravable.id == periodo_id, PeriodoGravable.declarante_id == declarante_id)
        .first()
    )
    if periodo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado.")

    if periodo.estado == "presentado" and solicitud.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Este periodo ya está presentado y no se puede editar. "
                "Si necesitas corregirlo, créalo como una declaración de corrección."
            ),
        )

    valores_anteriores = {
        "estado": periodo.estado,
        "patrimonio_bruto": float(periodo.patrimonio_bruto),
        "pasivos": float(periodo.pasivos),
    }
    datos = solicitud.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(periodo, campo, valor)

    db.add(periodo)
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        entidad="periodo_gravable",
        entidad_id=str(periodo.id),
        accion="actualizar",
        valores_anteriores=valores_anteriores,
        valores_nuevos=datos,
    )
    db.commit()
    db.refresh(periodo)
    return periodo
