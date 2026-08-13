from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol
from app.db.session import get_db
from app.models.usuario import RolUsuario
from app.rules_engine import parametros_2025 as _DEFAULTS
from app.rules_engine.ganancias_ocasionales import (
    calcular_ganancia_ocasional_herencia,
    calcular_ganancia_ocasional_loteria,
    calcular_ganancia_ocasional_venta_acciones,
    calcular_ganancia_ocasional_venta_inmueble,
)
from app.services.parametros_service import obtener_parametros_vigentes

router = APIRouter(
    prefix="/ganancias-ocasionales",
    tags=["ganancias-ocasionales"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR))],
)

_COP = Decimal("1")


def _redondear(valor: float) -> Decimal:
    """Convierte el float del motor de reglas a Decimal redondeado al peso."""
    return Decimal(str(valor)).quantize(_COP, rounding=ROUND_HALF_UP)


class RespuestaGananciaOcasional(BaseModel):
    ganancia_bruta_pesos: Decimal
    porcion_exenta_pesos: Decimal
    base_gravable_pesos: Decimal
    tarifa_aplicada: Decimal
    impuesto_pesos: Decimal


def _a_respuesta(resultado) -> RespuestaGananciaOcasional:
    return RespuestaGananciaOcasional(
        ganancia_bruta_pesos=_redondear(resultado.ganancia_bruta_pesos),
        porcion_exenta_pesos=_redondear(resultado.porcion_exenta_pesos),
        base_gravable_pesos=_redondear(resultado.base_gravable_pesos),
        # tarifa_aplicada es un coeficiente (ej. 0.15), se guarda con 4 decimales
        tarifa_aplicada=Decimal(str(resultado.tarifa_aplicada)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        ),
        impuesto_pesos=_redondear(resultado.impuesto_pesos),
    )


class SolicitudVentaInmueble(BaseModel):
    anio_gravable: int = Field(default=_DEFAULTS.ANIO_GRAVABLE, ge=2000, le=2100)
    precio_venta_pesos: Decimal = Field(ge=0, decimal_places=2)
    costo_adquisicion_pesos: Decimal = Field(ge=0, decimal_places=2)
    anio_adquisicion: int
    es_casa_habitacion_unica: bool = False


@router.post("/venta-inmueble", response_model=RespuestaGananciaOcasional)
def venta_inmueble(
    solicitud: SolicitudVentaInmueble, db: Session = Depends(get_db)
) -> RespuestaGananciaOcasional:
    P = obtener_parametros_vigentes(db, solicitud.anio_gravable)
    resultado = calcular_ganancia_ocasional_venta_inmueble(
        precio_venta_pesos=float(solicitud.precio_venta_pesos),
        costo_adquisicion_pesos=float(solicitud.costo_adquisicion_pesos),
        anio_adquisicion=solicitud.anio_adquisicion,
        es_casa_habitacion_unica=solicitud.es_casa_habitacion_unica,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_exento_casa_habitacion_uvt=P.TOPE_EXENTO_VENTA_CASA_HABITACION_UVT,
        factores_ajuste_por_anio=P.FACTORES_AJUSTE_ART73_POR_ANIO,
    )
    return _a_respuesta(resultado)


class SolicitudVentaAcciones(BaseModel):
    anio_gravable: int = Field(default=_DEFAULTS.ANIO_GRAVABLE, ge=2000, le=2100)
    precio_venta_pesos: Decimal = Field(ge=0, decimal_places=2)
    costo_fiscal_pesos: Decimal = Field(ge=0, decimal_places=2)
    cotiza_en_bolsa: bool = False
    # porcentaje_participacion_vendida es una proporción (0-1), no un monto;
    # se mantiene como float porque no es un valor monetario en pesos.
    porcentaje_participacion_vendida: float = Field(ge=0, le=1, default=0)


@router.post("/venta-acciones", response_model=RespuestaGananciaOcasional)
def venta_acciones(
    solicitud: SolicitudVentaAcciones, db: Session = Depends(get_db)
) -> RespuestaGananciaOcasional:
    P = obtener_parametros_vigentes(db, solicitud.anio_gravable)
    resultado = calcular_ganancia_ocasional_venta_acciones(
        precio_venta_pesos=float(solicitud.precio_venta_pesos),
        costo_fiscal_pesos=float(solicitud.costo_fiscal_pesos),
        cotiza_en_bolsa=solicitud.cotiza_en_bolsa,
        porcentaje_participacion_vendida=solicitud.porcentaje_participacion_vendida,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_participacion_bolsa_no_gravado=P.TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO,
    )
    return _a_respuesta(resultado)


class SolicitudHerencia(BaseModel):
    anio_gravable: int = Field(default=_DEFAULTS.ANIO_GRAVABLE, ge=2000, le=2100)
    valor_activo_pesos: Decimal = Field(ge=0, decimal_places=2)
    es_vivienda_habitacion_causante: bool = False


@router.post("/herencia", response_model=RespuestaGananciaOcasional)
def herencia(solicitud: SolicitudHerencia, db: Session = Depends(get_db)) -> RespuestaGananciaOcasional:
    P = obtener_parametros_vigentes(db, solicitud.anio_gravable)
    resultado = calcular_ganancia_ocasional_herencia(
        valor_activo_pesos=float(solicitud.valor_activo_pesos),
        es_vivienda_habitacion_causante=solicitud.es_vivienda_habitacion_causante,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        porcentaje_exento_general=P.PORCENTAJE_EXENTO_HERENCIA_GENERAL,
        tope_exento_general_uvt=P.TOPE_EXENTO_HERENCIA_GENERAL_UVT,
        tope_exento_vivienda_uvt=P.TOPE_EXENTO_HERENCIA_VIVIENDA_UVT,
    )
    return _a_respuesta(resultado)


class SolicitudLoteria(BaseModel):
    anio_gravable: int = Field(default=_DEFAULTS.ANIO_GRAVABLE, ge=2000, le=2100)
    valor_premio_pesos: Decimal = Field(ge=0, decimal_places=2)


@router.post("/loteria", response_model=RespuestaGananciaOcasional)
def loteria(solicitud: SolicitudLoteria, db: Session = Depends(get_db)) -> RespuestaGananciaOcasional:
    P = obtener_parametros_vigentes(db, solicitud.anio_gravable)
    resultado = calcular_ganancia_ocasional_loteria(
        valor_premio_pesos=float(solicitud.valor_premio_pesos),
        tarifa_loterias=P.TARIFA_GANANCIA_OCASIONAL_LOTERIAS,
    )
    return _a_respuesta(resultado)