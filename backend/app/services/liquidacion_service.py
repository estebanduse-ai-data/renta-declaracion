"""
LiquidacionService — Lógica de negocio de liquidación privada.

Cambios en DT-5
────────────────
Ya no se convierten los inputs a `float` antes de llamar a `liquidar()`.
El motor de reglas (`tarifa.py`) ahora opera en `Decimal` puro, y los
inputs que llegan de la API ya son `Decimal` (los schemas Pydantic los
validan como tal desde Act. 0.5).

La función `_redondear()` se mantiene: aunque el motor ya devuelve
`Decimal`, los valores intermedios no están redondeados al peso (tienen
más decimales de los que la DIAN espera). `_redondear()` aplica
ROUND_HALF_UP al peso antes de serializar la respuesta.

La conversión `Decimal(str(P.UVT))` ya no es necesaria porque
`parametros_2025.py` define UVT directamente como `Decimal("49799")`.

Convenciones sin cambios
──────────────────────────
• Recibe y devuelve `Decimal` para todos los valores monetarios.
• No hace commit — el router controla la transacción.
• Si `periodo_id` se provee y el periodo no está presentado, persiste
  el resultado en `periodo.resultado_liquidacion` (JSONB).

Referencias
───────────
  Act. 3.3  — creación de este módulo (service layer)
  DT-5      — migración a Decimal en el motor de reglas
  tarifa.py — motor de reglas puro (ahora Decimal completo)
  parametros_service.py — fuente de parámetros tributarios vigentes
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_COP = Decimal("1")


def _redondear(valor: Decimal) -> Decimal:
    """Redondea al peso colombiano más cercano (ROUND_HALF_UP)."""
    return valor.quantize(_COP, rounding=ROUND_HALF_UP)


@dataclass
class ResultadoLiquidacion:
    """
    Resultado completo de una liquidación privada.

    Todos los valores monetarios son Decimal redondeados al peso.
    `persistido` indica si el resultado fue guardado en la BD.
    """
    renta_liquida_gravable_pesos: Decimal
    impuesto_uvt:                 Decimal
    impuesto_a_cargo_pesos:       Decimal
    total_retenciones_pesos:      Decimal
    saldo_pesos:                  Decimal
    es_saldo_a_pagar:             bool
    anio_gravable:                int
    uvt_utilizada:                Decimal
    persistido:                   bool = False


def calcular_y_persistir(
    db: Session,
    *,
    anio_gravable: int,
    total_ingresos_brutos_pesos: Decimal,
    deducciones_imputables_pesos: Decimal,
    ingreso_salarios_pesos: Decimal,
    total_retenciones_pesos: Decimal,
    patrimonio_liquido_anterior_pesos: Decimal,
    periodo_id: uuid.UUID | None = None,
) -> ResultadoLiquidacion:
    """
    Calcula la liquidación privada y opcionalmente la persiste en el periodo.

    Flujo:
      1. Obtiene parámetros tributarios vigentes del año (BD o fallback estático).
      2. Llama a `tarifa.liquidar()` pasando los valores directamente como Decimal.
         (Antes de DT-5 se convertían a float aquí — ya no es necesario.)
      3. Redondea el resultado al peso con `_redondear()`.
      4. Si `periodo_id` se proveyó y el periodo no está presentado, persiste.
    """
    from app.models.declarante import PeriodoGravable
    from app.rules_engine.tarifa import liquidar
    from app.services.parametros_service import obtener_parametros_vigentes

    P = obtener_parametros_vigentes(db, anio_gravable)

    # DT-5: ya no hay float() — se pasan Decimal directamente al motor.
    resultado_motor = liquidar(
        total_ingresos_brutos_pesos=total_ingresos_brutos_pesos,
        deducciones_imputables_pesos=deducciones_imputables_pesos,
        ingreso_salarios_pesos=ingreso_salarios_pesos,
        total_retenciones_pesos=total_retenciones_pesos,
        patrimonio_liquido_anterior_pesos=patrimonio_liquido_anterior_pesos,
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )

    # Redondear al peso — el motor devuelve Decimal con más decimales
    renta_liq      = _redondear(resultado_motor.renta_liquida_gravable_pesos)
    impuesto_uvt   = _redondear(resultado_motor.impuesto_uvt)
    impuesto_cargo = _redondear(resultado_motor.impuesto_a_cargo_pesos)
    retenciones    = _redondear(resultado_motor.total_retenciones_pesos)
    saldo          = _redondear(resultado_motor.saldo_pesos)
    uvt_utilizada  = P.UVT   # ya es Decimal desde parametros_2025.py

    resultado = ResultadoLiquidacion(
        renta_liquida_gravable_pesos=renta_liq,
        impuesto_uvt=impuesto_uvt,
        impuesto_a_cargo_pesos=impuesto_cargo,
        total_retenciones_pesos=retenciones,
        saldo_pesos=saldo,
        es_saldo_a_pagar=resultado_motor.es_saldo_a_pagar,
        anio_gravable=P.ANIO_GRAVABLE,
        uvt_utilizada=uvt_utilizada,
        persistido=False,
    )

    if periodo_id is not None:
        periodo = (
            db.query(PeriodoGravable)
            .filter(PeriodoGravable.id == periodo_id)
            .first()
        )
        if periodo is not None and periodo.estado != "presentado":
            periodo.resultado_liquidacion = {
                "renta_liquida_gravable_pesos": str(renta_liq),
                "impuesto_uvt":                 str(impuesto_uvt),
                "impuesto_a_cargo_pesos":        str(impuesto_cargo),
                "total_retenciones_pesos":       str(retenciones),
                "saldo_pesos":                   str(saldo),
                "es_saldo_a_pagar":              resultado_motor.es_saldo_a_pagar,
                "uvt_utilizada":                 str(uvt_utilizada),
                "anio_gravable":                 P.ANIO_GRAVABLE,
            }
            db.add(periodo)
            db.commit()
            resultado.persistido = True

    return resultado