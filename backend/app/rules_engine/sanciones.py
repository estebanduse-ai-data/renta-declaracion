"""
Sanciones e intereses de mora — art. 635, 639, 640, 641 y 644 E.T.

Estas fórmulas se simplifican deliberadamente para los casos más frecuentes
(extemporaneidad al presentar por primera vez, y corrección voluntaria). Los
regímenes especiales de sanción reducida (art. 640 parágrafos de gradualidad
por buen comportamiento del contribuyente) no están cubiertos todavía — ver
docs/FALTANTES.md.

Cambios en fix/decimal-float-type-errors
─────────────────────────────────────────
Migración de `float` a `Decimal` para alinear con el motor de reglas (DT-5).
"""

import math
from dataclasses import dataclass
from decimal import Decimal

from app.rules_engine.tarifa import a_pesos

_CERO = Decimal("0")


def meses_o_fraccion_de_atraso(dias_atraso: int) -> int:
    """
    Redondea hacia arriba: un solo día de atraso ya cuenta como un mes o
    fracción de mes para efectos de la sanción por extemporaneidad.
    """
    if dias_atraso <= 0:
        return 0
    return math.ceil(dias_atraso / 30)


def calcular_sancion_extemporaneidad(
    *,
    impuesto_a_cargo_pesos: Decimal,
    ingresos_brutos_pesos: Decimal,
    dias_atraso: int,
    uvt: Decimal,
    porcentaje_mensual_sobre_impuesto: Decimal,
    tope_porcentaje_sobre_impuesto: Decimal,
    porcentaje_mensual_sobre_ingresos: Decimal,
    sancion_minima_uvt: Decimal,
) -> Decimal:
    meses = meses_o_fraccion_de_atraso(dias_atraso)
    if meses == 0:
        return _CERO

    sancion_minima_pesos = a_pesos(sancion_minima_uvt, uvt)

    if impuesto_a_cargo_pesos > _CERO:
        sancion = impuesto_a_cargo_pesos * porcentaje_mensual_sobre_impuesto * Decimal(meses)
        tope = impuesto_a_cargo_pesos * tope_porcentaje_sobre_impuesto
        sancion = min(sancion, tope)
    else:
        # Sin impuesto a cargo: la sanción se calcula sobre los ingresos brutos
        # del periodo (art. 641 E.T., simplificado).
        sancion = ingresos_brutos_pesos * porcentaje_mensual_sobre_ingresos * Decimal(meses)

    return max(sancion, sancion_minima_pesos)


def calcular_sancion_correccion(
    *,
    mayor_valor_a_pagar_pesos: Decimal,
    despues_de_emplazamiento: bool,
    porcentaje_antes: Decimal,
    porcentaje_despues: Decimal,
) -> Decimal:
    porcentaje = porcentaje_despues if despues_de_emplazamiento else porcentaje_antes
    return max(mayor_valor_a_pagar_pesos, _CERO) * porcentaje


@dataclass
class ResultadoInteresMora:
    dias_mora: int
    valor_adeudado_pesos: Decimal
    interes_pesos: Decimal


def calcular_interes_mora(
    *, valor_adeudado_pesos: Decimal, dias_mora: int, tasa_diaria: Decimal
) -> ResultadoInteresMora:
    """
    Interés simple diario sobre el valor adeudado. La tasa real la certifica
    trimestralmente la Superintendencia Financiera y varía en el tiempo; el
    parámetro `tasa_diaria` es referencial (ver parametros_2025.py) y debe
    sustituirse por la tasa vigente para el periodo exacto de mora antes de
    liquidar un caso real.
    """
    if dias_mora <= 0 or valor_adeudado_pesos <= _CERO:
        return ResultadoInteresMora(
            dias_mora=0,
            valor_adeudado_pesos=valor_adeudado_pesos,
            interes_pesos=_CERO,
        )

    interes = valor_adeudado_pesos * tasa_diaria * Decimal(dias_mora)
    return ResultadoInteresMora(
        dias_mora=dias_mora,
        valor_adeudado_pesos=valor_adeudado_pesos,
        interes_pesos=interes,
    )