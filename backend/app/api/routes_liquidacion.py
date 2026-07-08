from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import liquidar

router = APIRouter(prefix="/liquidacion", tags=["liquidacion"])


class SolicitudLiquidacion(BaseModel):
    total_ingresos_brutos_pesos: float = Field(ge=0)
    deducciones_imputables_pesos: float = Field(ge=0, default=0)
    ingreso_salarios_pesos: float = Field(ge=0, default=0)
    total_retenciones_pesos: float = Field(ge=0, default=0)
    patrimonio_liquido_anterior_pesos: float = Field(default=0)


class RespuestaLiquidacion(BaseModel):
    renta_liquida_gravable_pesos: float
    impuesto_uvt: float
    impuesto_a_cargo_pesos: float
    total_retenciones_pesos: float
    saldo_pesos: float
    es_saldo_a_pagar: bool
    anio_gravable: int
    uvt_utilizada: float


@router.post("/calcular", response_model=RespuestaLiquidacion)
def calcular_liquidacion(solicitud: SolicitudLiquidacion) -> RespuestaLiquidacion:
    """
    Calcula la liquidación privada para el año gravable 2025 a partir de
    totales ya depurados. No persiste nada — el guardado del resultado en
    un periodo gravable concreto se implementa en una iteración posterior
    junto con el CRUD de declarantes.
    """
    resultado = liquidar(
        total_ingresos_brutos_pesos=solicitud.total_ingresos_brutos_pesos,
        deducciones_imputables_pesos=solicitud.deducciones_imputables_pesos,
        ingreso_salarios_pesos=solicitud.ingreso_salarios_pesos,
        total_retenciones_pesos=solicitud.total_retenciones_pesos,
        patrimonio_liquido_anterior_pesos=solicitud.patrimonio_liquido_anterior_pesos,
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )
    return RespuestaLiquidacion(
        renta_liquida_gravable_pesos=resultado.renta_liquida_gravable_pesos,
        impuesto_uvt=resultado.impuesto_uvt,
        impuesto_a_cargo_pesos=resultado.impuesto_a_cargo_pesos,
        total_retenciones_pesos=resultado.total_retenciones_pesos,
        saldo_pesos=resultado.saldo_pesos,
        es_saldo_a_pagar=resultado.es_saldo_a_pagar,
        anio_gravable=P.ANIO_GRAVABLE,
        uvt_utilizada=P.UVT,
    )
