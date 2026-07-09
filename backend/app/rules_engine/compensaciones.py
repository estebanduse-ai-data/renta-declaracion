"""
Compensación de pérdidas fiscales de años anteriores — art. 147 E.T.

Simplificación importante: la ley exige que la pérdida se compense contra
rentas líquidas de la MISMA cédula que la generó, y dentro de un plazo
máximo de años (`LIMITE_ANIOS_COMPENSACION_PERDIDAS`). Esta función asume
que quien la invoca ya filtró la pérdida disponible por cédula y verificó
que no ha vencido el plazo — ese control de vigencia requiere el histórico
completo por declarante y no está modelado aquí todavía (ver
docs/FALTANTES.md).
"""

from dataclasses import dataclass


@dataclass
class ResultadoCompensacion:
    renta_liquida_antes_de_compensar_pesos: float
    perdida_disponible_pesos: float
    perdida_utilizada_pesos: float
    perdida_remanente_pesos: float
    renta_liquida_despues_de_compensar_pesos: float


def calcular_compensacion_perdida(
    *, renta_liquida_cedular_pesos: float, perdida_disponible_pesos: float
) -> ResultadoCompensacion:
    renta_liquida = max(renta_liquida_cedular_pesos, 0.0)
    perdida_disponible = max(perdida_disponible_pesos, 0.0)

    perdida_utilizada = min(renta_liquida, perdida_disponible)
    perdida_remanente = perdida_disponible - perdida_utilizada
    renta_liquida_final = renta_liquida - perdida_utilizada

    return ResultadoCompensacion(
        renta_liquida_antes_de_compensar_pesos=renta_liquida,
        perdida_disponible_pesos=perdida_disponible,
        perdida_utilizada_pesos=perdida_utilizada,
        perdida_remanente_pesos=perdida_remanente,
        renta_liquida_despues_de_compensar_pesos=renta_liquida_final,
    )
