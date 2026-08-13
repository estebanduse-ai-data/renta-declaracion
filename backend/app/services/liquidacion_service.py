"""
LiquidacionService — Lógica de negocio de liquidación privada.

Por qué existe este servicio
─────────────────────────────
`routes_liquidacion.py` mezclaba tres responsabilidades distintas en un solo
handler de 50 líneas:

  1. Obtener los parámetros tributarios vigentes (delega a parametros_service).
  2. Llamar al motor de reglas y convertir los resultados a Decimal.
  3. Persistir el resultado en el periodo gravable si se proveyó periodo_id.

Al separarlo aquí, cada responsabilidad queda aislada y testeable sin FastAPI.
El router pasa a ser un thin wrapper de 10 líneas.

Convenciones
─────────────
• Recibe y devuelve `Decimal` para todos los valores monetarios.
  El motor de reglas (tarifa.py) sigue usando `float` internamente — la
  conversión ocurre en `_redondear()`, mantenida aquí junto al servicio
  que la usa (no en el router). Esto facilita la migración futura del
  motor a Decimal completo (Act. pendiente post-Sprint 3).
• La función `calcular_y_persistir` no hace commit — el router controla
  la transacción. La única excepción es el caso donde `periodo_id` se
  provee y el periodo existe: en ese caso sí hace commit parcial de la
  persistencia del resultado.

Referencias
───────────
  Act. 3.3  — creación de este módulo
  routes_liquidacion.py  — thin wrapper
  tarifa.py  — motor de reglas puro (sin estado, sin ORM)
  parametros_service.py  — fuente de parámetros tributarios vigentes
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Cuantía mínima de redondeo para valores en pesos colombianos.
_COP = Decimal("1")


def _redondear(valor: float) -> Decimal:
    """Convierte el float del motor de reglas a Decimal redondeado al peso."""
    return Decimal(str(valor)).quantize(_COP, rounding=ROUND_HALF_UP)


# ── DTO de resultado ───────────────────────────────────────────────────────────

@dataclass
class ResultadoLiquidacion:
    """
    Resultado completo de una liquidación privada.

    Todos los valores monetarios son Decimal redondeados al peso.
    `persistido` indica si el resultado fue guardado en la BD
    (solo True cuando se proveyó periodo_id y el periodo no está presentado).
    """
    renta_liquida_gravable_pesos: Decimal
    impuesto_uvt: Decimal
    impuesto_a_cargo_pesos: Decimal
    total_retenciones_pesos: Decimal
    saldo_pesos: Decimal
    es_saldo_a_pagar: bool
    anio_gravable: int
    uvt_utilizada: Decimal
    persistido: bool = False


# ── Función principal ──────────────────────────────────────────────────────────

def calcular_y_persistir(
    db: "Session",
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
    Calcula la liquidación privada y, si se indica `periodo_id`, persiste
    el resultado en el campo `resultado_liquidacion` del periodo.

    Flujo:
      1. Obtiene parámetros tributarios vigentes del año (BD o fallback estático).
      2. Llama a `tarifa.liquidar()` con los valores convertidos a float.
      3. Convierte el resultado a Decimal con `_redondear()`.
      4. Si `periodo_id` se proveyó y el periodo no está presentado, guarda
         el resultado en `periodo.resultado_liquidacion` (JSONB) y hace commit.

    Lanza:
      - `ParametrosNoConfiguradosError` si no hay parámetros para el año.
      - No lanza si `periodo_id` no se encuentra — simplemente no persiste.
    """
    from app.models.declarante import PeriodoGravable
    from app.rules_engine.tarifa import liquidar
    from app.services.parametros_service import obtener_parametros_vigentes

    P = obtener_parametros_vigentes(db, anio_gravable)

    resultado_motor = liquidar(
        total_ingresos_brutos_pesos=float(total_ingresos_brutos_pesos),
        deducciones_imputables_pesos=float(deducciones_imputables_pesos),
        ingreso_salarios_pesos=float(ingreso_salarios_pesos),
        total_retenciones_pesos=float(total_retenciones_pesos),
        patrimonio_liquido_anterior_pesos=float(patrimonio_liquido_anterior_pesos),
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )

    renta_liq      = _redondear(resultado_motor.renta_liquida_gravable_pesos)
    impuesto_uvt   = _redondear(resultado_motor.impuesto_uvt)
    impuesto_cargo = _redondear(resultado_motor.impuesto_a_cargo_pesos)
    retenciones    = _redondear(resultado_motor.total_retenciones_pesos)
    saldo          = _redondear(resultado_motor.saldo_pesos)
    uvt_utilizada  = Decimal(str(P.UVT))

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

    # Persistencia opcional: guardar en el periodo si se indicó
    if periodo_id is not None:
        periodo = (
            db.query(PeriodoGravable)
            .filter(PeriodoGravable.id == periodo_id)
            .first()
        )
        if periodo is not None and periodo.estado != "presentado":
            periodo.resultado_liquidacion = {
                "renta_liquida_gravable_pesos": str(renta_liq),
                "impuesto_uvt": str(impuesto_uvt),
                "impuesto_a_cargo_pesos": str(impuesto_cargo),
                "total_retenciones_pesos": str(retenciones),
                "saldo_pesos": str(saldo),
                "es_saldo_a_pagar": resultado_motor.es_saldo_a_pagar,
                "uvt_utilizada": str(uvt_utilizada),
                "anio_gravable": P.ANIO_GRAVABLE,
            }
            db.add(periodo)
            db.commit()
            resultado.persistido = True

    return resultado