"""
Sanciones e intereses de mora — art. 635, 639, 640, 641 y 644 E.T.

Estas fórmulas se simplifican deliberadamente para los casos más frecuentes
(extemporaneidad al presentar por primera vez, y corrección voluntaria). Los
regímenes especiales de sanción reducida (art. 640 parágrafos de gradualidad
por buen comportamiento del contribuyente) no están cubiertos todavía — ver
docs/FALTANTES.md.
"""

import math
from dataclasses import dataclass

from app.rules_engine.tarifa import a_pesos


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
    impuesto_a_cargo_pesos: float,
    ingresos_brutos_pesos: float,
    dias_atraso: int,
    uvt: float,
    porcentaje_mensual_sobre_impuesto: float,
    tope_porcentaje_sobre_impuesto: float,
    porcentaje_mensual_sobre_ingresos: float,
    sancion_minima_uvt: float,
) -> float:
    meses = meses_o_fraccion_de_atraso(dias_atraso)
    if meses == 0:
        return 0.0

    sancion_minima_pesos = a_pesos(sancion_minima_uvt, uvt)

    if impuesto_a_cargo_pesos > 0:
        sancion = impuesto_a_cargo_pesos * porcentaje_mensual_sobre_impuesto * meses
        tope = impuesto_a_cargo_pesos * tope_porcentaje_sobre_impuesto
        sancion = min(sancion, tope)
    else:
        # Sin impuesto a cargo: la sanción se calcula sobre los ingresos brutos
        # del periodo (art. 641 E.T., simplificado).
        sancion = ingresos_brutos_pesos * porcentaje_mensual_sobre_ingresos * meses

    return max(sancion, sancion_minima_pesos)


def calcular_sancion_correccion(
    *,
    mayor_valor_a_pagar_pesos: float,
    despues_de_emplazamiento: bool,
    porcentaje_antes: float,
    porcentaje_despues: float,
) -> float:
    porcentaje = porcentaje_despues if despues_de_emplazamiento else porcentaje_antes
    return max(mayor_valor_a_pagar_pesos, 0.0) * porcentaje


@dataclass
class ResultadoInteresMora:
    dias_mora: int
    valor_adeudado_pesos: float
    interes_pesos: float


def calcular_interes_mora(
    *, valor_adeudado_pesos: float, dias_mora: int, tasa_diaria: float
) -> ResultadoInteresMora:
    """
    Interés simple diario sobre el valor adeudado. La tasa real la certifica
    trimestralmente la Superintendencia Financiera y varía en el tiempo; el
    parámetro `tasa_diaria` es referencial (ver parametros_2025.py) y debe
    sustituirse por la tasa vigente para el periodo exacto de mora antes de
    liquidar un caso real.
    """
    if dias_mora <= 0 or valor_adeudado_pesos <= 0:
        return ResultadoInteresMora(dias_mora=0, valor_adeudado_pesos=valor_adeudado_pesos, interes_pesos=0.0)

    interes = valor_adeudado_pesos * tasa_diaria * dias_mora
    return ResultadoInteresMora(
        dias_mora=dias_mora, valor_adeudado_pesos=valor_adeudado_pesos, interes_pesos=interes
    )
