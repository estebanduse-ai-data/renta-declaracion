from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.rules_engine import parametros_2025 as P
from app.rules_engine.ganancias_ocasionales import (
    calcular_ganancia_ocasional_venta_inmueble,
    calcular_ganancia_ocasional_venta_acciones,
    calcular_ganancia_ocasional_herencia,
    calcular_ganancia_ocasional_loteria,
)

router = APIRouter(prefix="/ganancias-ocasionales", tags=["ganancias-ocasionales"])


class RespuestaGananciaOcasional(BaseModel):
    ganancia_bruta_pesos: float
    porcion_exenta_pesos: float
    base_gravable_pesos: float
    tarifa_aplicada: float
    impuesto_pesos: float


def _a_respuesta(resultado) -> RespuestaGananciaOcasional:
    return RespuestaGananciaOcasional(
        ganancia_bruta_pesos=resultado.ganancia_bruta_pesos,
        porcion_exenta_pesos=resultado.porcion_exenta_pesos,
        base_gravable_pesos=resultado.base_gravable_pesos,
        tarifa_aplicada=resultado.tarifa_aplicada,
        impuesto_pesos=resultado.impuesto_pesos,
    )


class SolicitudVentaInmueble(BaseModel):
    precio_venta_pesos: float = Field(ge=0)
    costo_adquisicion_pesos: float = Field(ge=0)
    anio_adquisicion: int
    es_casa_habitacion_unica: bool = False


@router.post("/venta-inmueble", response_model=RespuestaGananciaOcasional)
def venta_inmueble(solicitud: SolicitudVentaInmueble) -> RespuestaGananciaOcasional:
    resultado = calcular_ganancia_ocasional_venta_inmueble(
        precio_venta_pesos=solicitud.precio_venta_pesos,
        costo_adquisicion_pesos=solicitud.costo_adquisicion_pesos,
        anio_adquisicion=solicitud.anio_adquisicion,
        es_casa_habitacion_unica=solicitud.es_casa_habitacion_unica,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_exento_casa_habitacion_uvt=P.TOPE_EXENTO_VENTA_CASA_HABITACION_UVT,
        factores_ajuste_por_anio=P.FACTORES_AJUSTE_ART73_POR_ANIO,
    )
    return _a_respuesta(resultado)


class SolicitudVentaAcciones(BaseModel):
    precio_venta_pesos: float = Field(ge=0)
    costo_fiscal_pesos: float = Field(ge=0)
    cotiza_en_bolsa: bool = False
    porcentaje_participacion_vendida: float = Field(ge=0, le=1, default=0)


@router.post("/venta-acciones", response_model=RespuestaGananciaOcasional)
def venta_acciones(solicitud: SolicitudVentaAcciones) -> RespuestaGananciaOcasional:
    resultado = calcular_ganancia_ocasional_venta_acciones(
        precio_venta_pesos=solicitud.precio_venta_pesos,
        costo_fiscal_pesos=solicitud.costo_fiscal_pesos,
        cotiza_en_bolsa=solicitud.cotiza_en_bolsa,
        porcentaje_participacion_vendida=solicitud.porcentaje_participacion_vendida,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_participacion_bolsa_no_gravado=P.TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO,
    )
    return _a_respuesta(resultado)


class SolicitudHerencia(BaseModel):
    valor_activo_pesos: float = Field(ge=0)
    es_vivienda_habitacion_causante: bool = False


@router.post("/herencia", response_model=RespuestaGananciaOcasional)
def herencia(solicitud: SolicitudHerencia) -> RespuestaGananciaOcasional:
    resultado = calcular_ganancia_ocasional_herencia(
        valor_activo_pesos=solicitud.valor_activo_pesos,
        es_vivienda_habitacion_causante=solicitud.es_vivienda_habitacion_causante,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        porcentaje_exento_general=P.PORCENTAJE_EXENTO_HERENCIA_GENERAL,
        tope_exento_general_uvt=P.TOPE_EXENTO_HERENCIA_GENERAL_UVT,
        tope_exento_vivienda_uvt=P.TOPE_EXENTO_HERENCIA_VIVIENDA_UVT,
    )
    return _a_respuesta(resultado)


class SolicitudLoteria(BaseModel):
    valor_premio_pesos: float = Field(ge=0)


@router.post("/loteria", response_model=RespuestaGananciaOcasional)
def loteria(solicitud: SolicitudLoteria) -> RespuestaGananciaOcasional:
    resultado = calcular_ganancia_ocasional_loteria(
        valor_premio_pesos=solicitud.valor_premio_pesos,
        tarifa_loterias=P.TARIFA_GANANCIA_OCASIONAL_LOTERIAS,
    )
    return _a_respuesta(resultado)
