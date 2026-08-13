import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol
from app.db.session import get_db
from app.models.declarante import PeriodoGravable
from app.models.usuario import RolUsuario, Usuario
from app.schemas.declarante import (
    ActualizarDeclarante,
    ActualizarPeriodoGravable,
    CrearDeclarante,
    CrearPeriodoGravable,
    RespuestaDeclarante,
    RespuestaPeriodoGravable,
)
from app.services import declarante_service as svc

router = APIRouter(
    prefix="/declarantes",
    tags=["declarantes"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR))],
)


class RespuestaListaDeclarantes(BaseModel):
    """
    Respuesta paginada del listado de declarantes.

    `total` permite al frontend saber cuántos hay en total sin cargar todos.
    `skip` y `limit` reflejan los parámetros usados para facilitar la
    construcción de controles de paginación en el cliente.
    """
    total: int
    skip: int
    limit: int
    items: list[RespuestaDeclarante]


@router.get("", response_model=RespuestaListaDeclarantes)
def listar_declarantes(
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(default=200, ge=1, le=500, description="Máximo de registros a devolver"),
    busqueda: str = Query(default="", description="Filtro por apellido o NIT (opcional)"),
) -> RespuestaListaDeclarantes:
    """Lista declarantes con paginación y filtro opcional. Act. 1.3."""
    total, items = svc.listar_declarantes(db, skip=skip, limit=limit, busqueda=busqueda)
    return RespuestaListaDeclarantes(total=total, skip=skip, limit=limit, items=items)


@router.post("", response_model=RespuestaDeclarante, status_code=status.HTTP_201_CREATED)
def crear_declarante(
    solicitud: CrearDeclarante,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR)),
) -> RespuestaDeclarante:
    try:
        declarante = svc.crear_declarante(
            db,
            nit=solicitud.nit,
            digito_verificacion=solicitud.digito_verificacion,
            primer_nombre=solicitud.primer_nombre,
            primer_apellido=solicitud.primer_apellido,
            actividad_economica=solicitud.actividad_economica,
            usuario_id=usuario.id,
        )
        db.commit()
        db.refresh(declarante)
        return declarante
    except svc.NITDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{declarante_id}", response_model=RespuestaDeclarante)
def obtener_declarante(
    declarante_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RespuestaDeclarante:
    try:
        return svc._get_declarante_o_error(db, declarante_id)
    except svc.DeclaranteNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{declarante_id}", response_model=RespuestaDeclarante)
def actualizar_declarante(
    declarante_id: uuid.UUID,
    solicitud: ActualizarDeclarante,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR)),
) -> RespuestaDeclarante:
    try:
        declarante = svc.actualizar_declarante(
            db,
            declarante_id=declarante_id,
            datos=solicitud.model_dump(exclude_unset=True),
            usuario_id=usuario.id,
        )
        db.commit()
        db.refresh(declarante)
        return declarante
    except svc.DeclaranteNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Periodos gravables ─────────────────────────────────────────────────────────

@router.post(
    "/{declarante_id}/periodos",
    response_model=RespuestaPeriodoGravable,
    status_code=status.HTTP_201_CREATED,
)
def crear_periodo(
    declarante_id: uuid.UUID,
    solicitud: CrearPeriodoGravable,
    db: Session = Depends(get_db),
) -> RespuestaPeriodoGravable:
    try:
        periodo = svc.crear_periodo(
            db,
            declarante_id=declarante_id,
            anio=solicitud.anio,
            patrimonio_bruto=float(solicitud.patrimonio_bruto) if solicitud.patrimonio_bruto else 0,
            pasivos=float(solicitud.pasivos) if solicitud.pasivos else 0,
        )
        db.commit()
        db.refresh(periodo)
        return periodo
    except svc.DeclaranteNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except svc.PeriodoDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{declarante_id}/periodos", response_model=list[RespuestaPeriodoGravable])
def listar_periodos(
    declarante_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> list[PeriodoGravable]:
    return svc.listar_periodos(db, declarante_id)


@router.patch("/{declarante_id}/periodos/{periodo_id}", response_model=RespuestaPeriodoGravable)
def actualizar_periodo(
    declarante_id: uuid.UUID,
    periodo_id: uuid.UUID,
    solicitud: ActualizarPeriodoGravable,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR)),
) -> RespuestaPeriodoGravable:
    try:
        periodo = svc.actualizar_periodo(
            db,
            declarante_id=declarante_id,
            periodo_id=periodo_id,
            datos=solicitud.model_dump(exclude_unset=True),
            usuario_id=usuario.id,
        )
        db.commit()
        db.refresh(periodo)
        return periodo
    except svc.PeriodoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except svc.PeriodoPresentadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))