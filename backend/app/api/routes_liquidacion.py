import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol
from app.db.session import get_db
from app.models.usuario import RolUsuario
from app.rules_engine import parametros_2025 as _DEFAULTS
from app.services import liquidacion_service as svc

router = APIRouter(
    prefix="/liquidacion",
    tags=["liquidacion"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR))],
)


class SolicitudLiquidacion(BaseModel):
    anio_gravable: int = Field(default=_DEFAULTS.ANIO_GRAVABLE, ge=2000, le=2100)
    # Decimal para todos los valores monetarios — evita errores de punto flotante
    # IEEE 754 en cálculos presentados a la DIAN (Act. 0.5).
    total_ingresos_brutos_pesos: Decimal = Field(ge=0, decimal_places=2)
    deducciones_imputables_pesos: Decimal = Field(ge=0, default=Decimal("0"), decimal_places=2)
    ingreso_salarios_pesos: Decimal = Field(ge=0, default=Decimal("0"), decimal_places=2)
    total_retenciones_pesos: Decimal = Field(ge=0, default=Decimal("0"), decimal_places=2)
    patrimonio_liquido_anterior_pesos: Decimal = Field(default=Decimal("0"), decimal_places=2)
    # Si se provee, el resultado se persiste en el periodo gravable indicado.
    periodo_id: uuid.UUID | None = Field(default=None)


class RespuestaLiquidacion(BaseModel):
    renta_liquida_gravable_pesos: Decimal
    impuesto_uvt: Decimal
    impuesto_a_cargo_pesos: Decimal
    total_retenciones_pesos: Decimal
    saldo_pesos: Decimal
    es_saldo_a_pagar: bool
    anio_gravable: int
    uvt_utilizada: Decimal
    persistido: bool = False


@router.post("/calcular", response_model=RespuestaLiquidacion)
def calcular_liquidacion(
    solicitud: SolicitudLiquidacion,
    db: Session = Depends(get_db),
) -> RespuestaLiquidacion:
    """
    Calcula la liquidación privada para el año gravable indicado.

    Si `periodo_id` viene en el body, persiste el resultado en la columna
    `resultado_liquidacion` (JSONB) del periodo gravable correspondiente.
    """
    resultado = svc.calcular_y_persistir(
        db,
        anio_gravable=solicitud.anio_gravable,
        total_ingresos_brutos_pesos=solicitud.total_ingresos_brutos_pesos,
        deducciones_imputables_pesos=solicitud.deducciones_imputables_pesos,
        ingreso_salarios_pesos=solicitud.ingreso_salarios_pesos,
        total_retenciones_pesos=solicitud.total_retenciones_pesos,
        patrimonio_liquido_anterior_pesos=solicitud.patrimonio_liquido_anterior_pesos,
        periodo_id=solicitud.periodo_id,
    )
    return RespuestaLiquidacion(
        renta_liquida_gravable_pesos=resultado.renta_liquida_gravable_pesos,
        impuesto_uvt=resultado.impuesto_uvt,
        impuesto_a_cargo_pesos=resultado.impuesto_a_cargo_pesos,
        total_retenciones_pesos=resultado.total_retenciones_pesos,
        saldo_pesos=resultado.saldo_pesos,
        es_saldo_a_pagar=resultado.es_saldo_a_pagar,
        anio_gravable=resultado.anio_gravable,
        uvt_utilizada=resultado.uvt_utilizada,
        persistido=resultado.persistido,
    )