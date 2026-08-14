"""
routes_liquidacion.py — endpoint de liquidación privada.

Cambio en DT-7
───────────────
`SolicitudLiquidacion` y `RespuestaLiquidacion` se movieron a
`app/schemas/liquidacion.py`. El contrato HTTP no cambia.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol
from app.db.session import get_db
from app.models.usuario import RolUsuario
from app.schemas.liquidacion import RespuestaLiquidacion, SolicitudLiquidacion
from app.services import liquidacion_service as svc

router = APIRouter(
    prefix="/liquidacion",
    tags=["liquidacion"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR, RolUsuario.AUXILIAR))],
)


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