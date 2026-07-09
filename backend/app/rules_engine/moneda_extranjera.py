"""
Conversión de bienes, deudas e ingresos en moneda extranjera — art. 32-1 y
269 del E.T.

Reglas de valoración distintas según el tipo de partida:

  - Patrimonio (activos y pasivos en moneda extranjera): se valora a la TRM
    de cierre del ejercicio (31 de diciembre), art. 269 E.T.
  - Ingresos y gastos en moneda extranjera: se valoran a la TRM del día de
    causación de la operación, art. 32-1 E.T.

Ninguna función aquí obtiene la TRM por sí misma — la TRM se recibe como
argumento, típicamente resuelta antes por una fuente de datos externa
(equivalente a la hoja `TRM_diaria` del Excel actual). Ver docs/FALTANTES.md.
"""

from dataclasses import dataclass


@dataclass
class ResultadoConversion:
    valor_moneda_extranjera: float
    trm_aplicada: float
    valor_pesos: float


def valorar_patrimonio_moneda_extranjera(
    *, valor_moneda_extranjera: float, trm_cierre_anio: float
) -> ResultadoConversion:
    if trm_cierre_anio <= 0:
        raise ValueError("La TRM de cierre debe ser un valor positivo.")
    valor_pesos = valor_moneda_extranjera * trm_cierre_anio
    return ResultadoConversion(
        valor_moneda_extranjera=valor_moneda_extranjera,
        trm_aplicada=trm_cierre_anio,
        valor_pesos=valor_pesos,
    )


def valorar_ingreso_moneda_extranjera(
    *, valor_moneda_extranjera: float, trm_dia_operacion: float
) -> ResultadoConversion:
    if trm_dia_operacion <= 0:
        raise ValueError("La TRM del día de la operación debe ser un valor positivo.")
    valor_pesos = valor_moneda_extranjera * trm_dia_operacion
    return ResultadoConversion(
        valor_moneda_extranjera=valor_moneda_extranjera,
        trm_aplicada=trm_dia_operacion,
        valor_pesos=valor_pesos,
    )


def consolidar_patrimonio_moneda_extranjera(
    *, partidas: list[dict], trm_cierre_anio: float
) -> float:
    """
    Suma varias partidas en moneda extranjera (posiblemente en distintas
    divisas ya convertidas a USD equivalente por el llamador) y las valora
    todas a la misma TRM de cierre.

    `partidas`: lista de dicts con la forma {"valor_moneda_extranjera": float}
    """
    total_pesos = 0.0
    for partida in partidas:
        resultado = valorar_patrimonio_moneda_extranjera(
            valor_moneda_extranjera=partida["valor_moneda_extranjera"],
            trm_cierre_anio=trm_cierre_anio,
        )
        total_pesos += resultado.valor_pesos
    return total_pesos
