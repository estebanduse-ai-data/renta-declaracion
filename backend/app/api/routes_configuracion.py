"""
Módulo de configuración — únicamente accesible por el rol Admin.

Centraliza los tres tipos de valores que cambian con el tiempo y que el
motor de reglas necesita para calcular correctamente (ver
docs/GESTION_PROYECTO.md y la clasificación por frecuencia de cambio):

  1. Parámetros tributarios anuales (UVT, tarifas, topes) — /parametros-tributarios
  2. TRM diaria — /trm
  3. Tasa de interés de mora — /tasa-interes-mora

Todo cambio queda en `AuditoriaCambio` porque afecta el cálculo de todos los
declarantes, no solo de uno.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol
from app.db.session import get_db
from app.models.configuracion import ParametroTributario, TasaInteresMora, TRMDiaria
from app.models.usuario import RolUsuario, Usuario
from app.schemas.configuracion import ParametrosTributariosPayload
from app.services.auditoria_service import registrar_auditoria
from app.services.parametros_service import activar_parametro_tributario

router = APIRouter(
    prefix="/configuracion", tags=["configuracion"], dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))]
)


# --- Parámetros tributarios anuales ------------------------------------


@router.get("/parametros-tributarios")
def listar_parametros_tributarios(db: Session = Depends(get_db)):
    registros = db.query(ParametroTributario).order_by(ParametroTributario.anio.desc()).all()
    return [
        {
            "id": r.id,
            "anio": r.anio,
            "activo": r.activo,
            "nota": r.nota,
            "creado_en": r.creado_en,
        }
        for r in registros
    ]


@router.get("/parametros-tributarios/{anio}")
def obtener_parametros_tributarios_activos(anio: int, db: Session = Depends(get_db)):
    registro = (
        db.query(ParametroTributario)
        .filter(ParametroTributario.anio == anio, ParametroTributario.activo.is_(True))
        .first()
    )
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay parámetros tributarios activos para el año {anio}.",
        )
    return {"id": registro.id, "anio": registro.anio, "valores": registro.valores, "nota": registro.nota}


@router.post("/parametros-tributarios", status_code=status.HTTP_201_CREATED)
def crear_parametros_tributarios(
    payload: ParametrosTributariosPayload,
    nota: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    """
    Crea (o reemplaza, si ya existe uno activo) el conjunto de parámetros
    tributarios de un año gravable. El payload se valida contra
    `ParametrosTributariosPayload` — un UVT en cero, una tarifa mayor al
    100%, o una tabla de tarifa vacía se rechazan ANTES de guardarse, para
    que un error de digitación no afecte el cálculo de 200 declarantes.
    """
    nuevo = activar_parametro_tributario(
        db,
        anio=payload.anio_gravable,
        valores=payload.model_dump(mode="json"),
        usuario_id=usuario.id,
        nota=nota,
    )
    return {"id": nuevo.id, "anio": nuevo.anio, "activo": nuevo.activo}


# --- TRM diaria ----------------------------------------------------------


@router.get("/trm")
def listar_trm(desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db)):
    consulta = db.query(TRMDiaria)
    if desde:
        consulta = consulta.filter(TRMDiaria.fecha >= desde)
    if hasta:
        consulta = consulta.filter(TRMDiaria.fecha <= hasta)
    return consulta.order_by(TRMDiaria.fecha.desc()).all()


@router.post("/trm", status_code=status.HTTP_201_CREATED)
def cargar_trm(
    fecha: date,
    valor: float,
    fuente: str = "manual",
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    if valor <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La TRM debe ser positiva.")

    existente = db.query(TRMDiaria).filter(TRMDiaria.fecha == fecha).first()
    valores_anteriores = {"valor": float(existente.valor)} if existente else None

    if existente is not None:
        existente.valor = valor
        existente.fuente = fuente
        existente.creado_por_id = usuario.id
        db.add(existente)
        registro = existente
        accion = "actualizar"
    else:
        registro = TRMDiaria(fecha=fecha, valor=valor, fuente=fuente, creado_por_id=usuario.id)
        db.add(registro)
        accion = "crear"

    db.flush()
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        entidad="trm_diaria",
        entidad_id=str(registro.id),
        accion=accion,
        valores_anteriores=valores_anteriores,
        valores_nuevos={"fecha": str(fecha), "valor": valor, "fuente": fuente},
    )
    db.commit()
    db.refresh(registro)
    return {"id": registro.id, "fecha": registro.fecha, "valor": float(registro.valor)}


# --- Tasa de interés de mora ----------------------------------------------


@router.get("/tasa-interes-mora")
def listar_tasa_interes_mora(db: Session = Depends(get_db)):
    return (
        db.query(TasaInteresMora).order_by(TasaInteresMora.vigente_desde.desc()).all()
    )


@router.post("/tasa-interes-mora", status_code=status.HTTP_201_CREATED)
def cargar_tasa_interes_mora(
    vigente_desde: date,
    tasa_diaria: float,
    vigente_hasta: date | None = None,
    tasa_efectiva_anual_referencia: float | None = None,
    fuente: str = "Superintendencia Financiera de Colombia",
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    if tasa_diaria <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La tasa de interés diaria debe ser positiva.",
        )
    if vigente_hasta is not None and vigente_hasta < vigente_desde:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="vigente_hasta no puede ser anterior a vigente_desde.",
        )

    registro = TasaInteresMora(
        vigente_desde=vigente_desde,
        vigente_hasta=vigente_hasta,
        tasa_diaria=tasa_diaria,
        tasa_efectiva_anual_referencia=tasa_efectiva_anual_referencia,
        fuente=fuente,
        creado_por_id=usuario.id,
    )
    db.add(registro)
    db.flush()
    registrar_auditoria(
        db,
        usuario_id=usuario.id,
        entidad="tasa_interes_mora",
        entidad_id=str(registro.id),
        accion="crear",
        valores_nuevos={
            "vigente_desde": str(vigente_desde),
            "vigente_hasta": str(vigente_hasta) if vigente_hasta else None,
            "tasa_diaria": tasa_diaria,
        },
    )
    db.commit()
    db.refresh(registro)
    return {"id": registro.id, "vigente_desde": registro.vigente_desde, "tasa_diaria": float(registro.tasa_diaria)}
