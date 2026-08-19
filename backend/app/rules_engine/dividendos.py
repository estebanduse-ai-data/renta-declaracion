"""
Cédula de dividendos y participaciones — artículo 242 E.T. (modificado por
Ley 2277 de 2022).

Cambios en fix/decimal-float-type-errors
─────────────────────────────────────────
Migración de `float` a `Decimal` para alinear con el motor de reglas (DT-5).
"""

from decimal import Decimal

from app.rules_engine.tarifa import a_uvt, calcular_impuesto_uvt, a_pesos


def calcular_impuesto_dividendos(
    *,
    dividendos_gravados_pesos: Decimal,
    dividendos_no_gravados_sociedad_pesos: Decimal,
    uvt: Decimal,
    tabla_tarifa_dividendos_uvt: list,
    tarifa_dividendos_no_gravados_sociedad: Decimal,
) -> dict:
    """
    Dos componentes:

    1. Dividendos que ya pagaron impuesto de renta en cabeza de la sociedad
       ("gravados" para efectos de esta cédula, en la terminología del
       formulario): tributan según la tabla marginal (0% hasta 1.090 UVT,
       15% en exceso).
    2. Dividendos que NO pagaron impuesto de renta en cabeza de la sociedad:
       primero se les aplica la tarifa corporativa equivalente (35%), y el
       remanente entra a sumarse con el primer grupo para la tabla marginal.
    """
    impuesto_no_gravados_paso_1 = (
        dividendos_no_gravados_sociedad_pesos * tarifa_dividendos_no_gravados_sociedad
    )
    remanente_no_gravados = dividendos_no_gravados_sociedad_pesos - impuesto_no_gravados_paso_1

    base_total_pesos = dividendos_gravados_pesos + remanente_no_gravados
    base_total_uvt = a_uvt(base_total_pesos, uvt)

    impuesto_tabla_uvt = calcular_impuesto_uvt(base_total_uvt, tabla_tarifa_dividendos_uvt)
    impuesto_tabla_pesos = a_pesos(impuesto_tabla_uvt, uvt)

    impuesto_total_pesos = impuesto_no_gravados_paso_1 + impuesto_tabla_pesos

    return {
        "base_gravable_pesos": base_total_pesos,
        "impuesto_corporativo_equivalente_pesos": impuesto_no_gravados_paso_1,
        "impuesto_tabla_marginal_pesos": impuesto_tabla_pesos,
        "impuesto_total_pesos": impuesto_total_pesos,
    }