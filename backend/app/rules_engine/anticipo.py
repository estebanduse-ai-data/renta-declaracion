"""
Anticipo de renta para el año gravable siguiente — art. 807 y 809 E.T.

El contribuyente puede elegir el menor valor entre dos metodologías:

  1. Individual: porcentaje sobre el impuesto neto de renta del año que se
     está declarando.
  2. Promedio: el mismo porcentaje sobre el promedio del impuesto neto de
     renta de los dos últimos años.

El porcentaje depende de si es la primera, segunda, o tercera vez (o más)
que el contribuyente declara.
"""

from dataclasses import dataclass


def _porcentaje_segun_anios_declarando(
    anios_declarando: int,
    porcentaje_primera_vez: float,
    porcentaje_segunda_vez: float,
    porcentaje_tercera_vez_en_adelante: float,
) -> float:
    if anios_declarando <= 1:
        return porcentaje_primera_vez
    if anios_declarando == 2:
        return porcentaje_segunda_vez
    return porcentaje_tercera_vez_en_adelante


@dataclass
class ResultadoAnticipo:
    porcentaje_aplicado: float
    anticipo_metodo_individual_pesos: float
    anticipo_metodo_promedio_pesos: float
    anticipo_a_pagar_pesos: float
    retenciones_estimadas_anio_siguiente_pesos: float
    saldo_anticipo_neto_pesos: float


def calcular_anticipo_renta(
    *,
    impuesto_neto_actual_pesos: float,
    impuesto_neto_anterior_pesos: float,
    anios_declarando: int,
    retenciones_estimadas_anio_siguiente_pesos: float = 0.0,
    porcentaje_primera_vez: float,
    porcentaje_segunda_vez: float,
    porcentaje_tercera_vez_en_adelante: float,
) -> ResultadoAnticipo:
    porcentaje = _porcentaje_segun_anios_declarando(
        anios_declarando,
        porcentaje_primera_vez,
        porcentaje_segunda_vez,
        porcentaje_tercera_vez_en_adelante,
    )

    metodo_individual = max(impuesto_neto_actual_pesos, 0.0) * porcentaje

    promedio = (max(impuesto_neto_actual_pesos, 0.0) + max(impuesto_neto_anterior_pesos, 0.0)) / 2
    metodo_promedio = promedio * porcentaje

    # El contribuyente elige el menor valor entre las dos metodologías.
    anticipo_elegido = min(metodo_individual, metodo_promedio)

    saldo_neto = max(anticipo_elegido - retenciones_estimadas_anio_siguiente_pesos, 0.0)

    return ResultadoAnticipo(
        porcentaje_aplicado=porcentaje,
        anticipo_metodo_individual_pesos=metodo_individual,
        anticipo_metodo_promedio_pesos=metodo_promedio,
        anticipo_a_pagar_pesos=anticipo_elegido,
        retenciones_estimadas_anio_siguiente_pesos=retenciones_estimadas_anio_siguiente_pesos,
        saldo_anticipo_neto_pesos=saldo_neto,
    )
