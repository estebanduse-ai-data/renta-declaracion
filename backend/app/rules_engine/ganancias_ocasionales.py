"""
Ganancias ocasionales — artículos 299 a 317 del Estatuto Tributario.

Cubre los cuatro casos más frecuentes en la cartera de un contador de personas
naturales: venta de inmuebles (con ajuste fiscal art. 73), venta de acciones,
herencias/legados/donaciones, y loterías/rifas/apuestas.

Todas las funciones son puras: reciben los parámetros normativos como
argumento (ver `parametros_2025.py`) y no acceden a base de datos ni a red.

Cambios en fix/decimal-float-type-errors
─────────────────────────────────────────
Migración de `float` a `Decimal` para alinear con el motor de reglas (DT-5).
Los factores de ajuste art. 73 (FACTORES_AJUSTE_ART73_POR_ANIO) permanecen
como float en parametros_2025.py porque son informativos; se convierten a
Decimal al usarlos en costo_fiscal_ajustado().
"""

from dataclasses import dataclass
from decimal import Decimal

from app.rules_engine.tarifa import a_pesos

_CERO = Decimal("0")


@dataclass
class ResultadoGananciaOcasional:
    ganancia_bruta_pesos: Decimal
    porcion_exenta_pesos: Decimal
    base_gravable_pesos: Decimal
    tarifa_aplicada: Decimal
    impuesto_pesos: Decimal


def costo_fiscal_ajustado(
    costo_adquisicion_pesos: Decimal,
    anio_adquisicion: int,
    factores_ajuste_por_anio: dict,
) -> Decimal:
    """
    Aplica el factor de ajuste fiscal (art. 73 E.T.) correspondiente al año de
    adquisición sobre el costo original, para obtener el costo fiscal indexado
    que se resta del precio de venta.

    Los factores del diccionario son float (informativos en parametros_2025.py);
    se convierten a Decimal(str(...)) para mantener precisión en la operación.
    """
    factor = factores_ajuste_por_anio.get(anio_adquisicion)
    if factor is None:
        # Si el año de adquisición no está en la tabla (activo muy antiguo o muy
        # reciente), se usa el costo histórico sin ajustar como salvaguarda
        # conservadora, y debe revisarse manualmente antes de presentar.
        factor = 1
    return costo_adquisicion_pesos * Decimal(str(factor))


def calcular_ganancia_ocasional_venta_inmueble(
    *,
    precio_venta_pesos: Decimal,
    costo_adquisicion_pesos: Decimal,
    anio_adquisicion: int,
    es_casa_habitacion_unica: bool,
    uvt: Decimal,
    tarifa_general: Decimal,
    tope_exento_casa_habitacion_uvt: Decimal,
    factores_ajuste_por_anio: dict,
) -> ResultadoGananciaOcasional:
    costo_ajustado = costo_fiscal_ajustado(
        costo_adquisicion_pesos, anio_adquisicion, factores_ajuste_por_anio
    )
    ganancia_bruta = max(precio_venta_pesos - costo_ajustado, _CERO)

    porcion_exenta = _CERO
    if es_casa_habitacion_unica:
        tope_pesos = a_pesos(tope_exento_casa_habitacion_uvt, uvt)
        porcion_exenta = min(ganancia_bruta, tope_pesos)

    base_gravable = max(ganancia_bruta - porcion_exenta, _CERO)
    impuesto = base_gravable * tarifa_general

    return ResultadoGananciaOcasional(
        ganancia_bruta_pesos=ganancia_bruta,
        porcion_exenta_pesos=porcion_exenta,
        base_gravable_pesos=base_gravable,
        tarifa_aplicada=tarifa_general,
        impuesto_pesos=impuesto,
    )


def calcular_ganancia_ocasional_venta_acciones(
    *,
    precio_venta_pesos: Decimal,
    costo_fiscal_pesos: Decimal,
    cotiza_en_bolsa: bool,
    porcentaje_participacion_vendida: Decimal,
    uvt: Decimal,
    tarifa_general: Decimal,
    tope_participacion_bolsa_no_gravado: Decimal,
) -> ResultadoGananciaOcasional:
    """
    Si las acciones cotizan en bolsa y lo vendido en el año no supera el
    porcentaje de participación no gravado (3% por defecto), la operación es
    un ingreso no constitutivo de renta ni ganancia ocasional (art. 36-1 E.T.)
    y el resultado es cero.
    """
    if cotiza_en_bolsa and porcentaje_participacion_vendida <= tope_participacion_bolsa_no_gravado:
        ganancia_bruta = max(precio_venta_pesos - costo_fiscal_pesos, _CERO)
        return ResultadoGananciaOcasional(
            ganancia_bruta_pesos=ganancia_bruta,
            porcion_exenta_pesos=ganancia_bruta,
            base_gravable_pesos=_CERO,
            tarifa_aplicada=_CERO,
            impuesto_pesos=_CERO,
        )

    ganancia_bruta = max(precio_venta_pesos - costo_fiscal_pesos, _CERO)
    impuesto = ganancia_bruta * tarifa_general

    return ResultadoGananciaOcasional(
        ganancia_bruta_pesos=ganancia_bruta,
        porcion_exenta_pesos=_CERO,
        base_gravable_pesos=ganancia_bruta,
        tarifa_aplicada=tarifa_general,
        impuesto_pesos=impuesto,
    )


def calcular_ganancia_ocasional_herencia(
    *,
    valor_activo_pesos: Decimal,
    es_vivienda_habitacion_causante: bool,
    uvt: Decimal,
    tarifa_general: Decimal,
    porcentaje_exento_general: Decimal,
    tope_exento_general_uvt: Decimal,
    tope_exento_vivienda_uvt: Decimal,
) -> ResultadoGananciaOcasional:
    exencion_general = min(
        valor_activo_pesos * porcentaje_exento_general,
        a_pesos(tope_exento_general_uvt, uvt),
    )

    exencion_vivienda = _CERO
    if es_vivienda_habitacion_causante:
        exencion_vivienda = min(
            valor_activo_pesos - exencion_general,
            a_pesos(tope_exento_vivienda_uvt, uvt),
        )
        exencion_vivienda = max(exencion_vivienda, _CERO)

    porcion_exenta = exencion_general + exencion_vivienda
    base_gravable = max(valor_activo_pesos - porcion_exenta, _CERO)
    impuesto = base_gravable * tarifa_general

    return ResultadoGananciaOcasional(
        ganancia_bruta_pesos=valor_activo_pesos,
        porcion_exenta_pesos=porcion_exenta,
        base_gravable_pesos=base_gravable,
        tarifa_aplicada=tarifa_general,
        impuesto_pesos=impuesto,
    )


def calcular_ganancia_ocasional_loteria(
    *,
    valor_premio_pesos: Decimal,
    tarifa_loterias: Decimal,
) -> ResultadoGananciaOcasional:
    """
    Loterías, rifas, apuestas y similares no tienen porción exenta y tributan
    a una tarifa fija distinta de la tarifa general de ganancia ocasional.
    """
    impuesto = valor_premio_pesos * tarifa_loterias
    return ResultadoGananciaOcasional(
        ganancia_bruta_pesos=valor_premio_pesos,
        porcion_exenta_pesos=_CERO,
        base_gravable_pesos=valor_premio_pesos,
        tarifa_aplicada=tarifa_loterias,
        impuesto_pesos=impuesto,
    )