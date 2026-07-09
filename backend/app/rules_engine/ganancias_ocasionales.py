"""
Ganancias ocasionales — artículos 299 a 317 del Estatuto Tributario.

Cubre los cuatro casos más frecuentes en la cartera de un contador de personas
naturales: venta de inmuebles (con ajuste fiscal art. 73), venta de acciones,
herencias/legados/donaciones, y loterías/rifas/apuestas.

Todas las funciones son puras: reciben los parámetros normativos como
argumento (ver `parametros_2025.py`) y no acceden a base de datos ni a red.
"""

from dataclasses import dataclass

from app.rules_engine.tarifa import a_pesos


@dataclass
class ResultadoGananciaOcasional:
    ganancia_bruta_pesos: float
    porcion_exenta_pesos: float
    base_gravable_pesos: float
    tarifa_aplicada: float
    impuesto_pesos: float


def costo_fiscal_ajustado(
    costo_adquisicion_pesos: float,
    anio_adquisicion: int,
    factores_ajuste_por_anio: dict,
) -> float:
    """
    Aplica el factor de ajuste fiscal (art. 73 E.T.) correspondiente al año de
    adquisición sobre el costo original, para obtener el costo fiscal indexado
    que se resta del precio de venta.
    """
    factor = factores_ajuste_por_anio.get(anio_adquisicion)
    if factor is None:
        # Si el año de adquisición no está en la tabla (activo muy antiguo o muy
        # reciente), se usa el costo histórico sin ajustar como salvaguarda
        # conservadora, y debe revisarse manualmente antes de presentar.
        factor = 1.0
    return costo_adquisicion_pesos * factor


def calcular_ganancia_ocasional_venta_inmueble(
    *,
    precio_venta_pesos: float,
    costo_adquisicion_pesos: float,
    anio_adquisicion: int,
    es_casa_habitacion_unica: bool,
    uvt: float,
    tarifa_general: float,
    tope_exento_casa_habitacion_uvt: float,
    factores_ajuste_por_anio: dict,
) -> ResultadoGananciaOcasional:
    costo_ajustado = costo_fiscal_ajustado(
        costo_adquisicion_pesos, anio_adquisicion, factores_ajuste_por_anio
    )
    ganancia_bruta = max(precio_venta_pesos - costo_ajustado, 0.0)

    porcion_exenta = 0.0
    if es_casa_habitacion_unica:
        tope_pesos = a_pesos(tope_exento_casa_habitacion_uvt, uvt)
        porcion_exenta = min(ganancia_bruta, tope_pesos)

    base_gravable = max(ganancia_bruta - porcion_exenta, 0.0)
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
    precio_venta_pesos: float,
    costo_fiscal_pesos: float,
    cotiza_en_bolsa: bool,
    porcentaje_participacion_vendida: float,
    uvt: float,
    tarifa_general: float,
    tope_participacion_bolsa_no_gravado: float,
) -> ResultadoGananciaOcasional:
    """
    Si las acciones cotizan en bolsa y lo vendido en el año no supera el
    porcentaje de participación no gravado (3% por defecto), la operación es
    un ingreso no constitutivo de renta ni ganancia ocasional (art. 36-1 E.T.)
    y el resultado es cero.
    """
    if cotiza_en_bolsa and porcentaje_participacion_vendida <= tope_participacion_bolsa_no_gravado:
        return ResultadoGananciaOcasional(
            ganancia_bruta_pesos=max(precio_venta_pesos - costo_fiscal_pesos, 0.0),
            porcion_exenta_pesos=max(precio_venta_pesos - costo_fiscal_pesos, 0.0),
            base_gravable_pesos=0.0,
            tarifa_aplicada=0.0,
            impuesto_pesos=0.0,
        )

    ganancia_bruta = max(precio_venta_pesos - costo_fiscal_pesos, 0.0)
    impuesto = ganancia_bruta * tarifa_general

    return ResultadoGananciaOcasional(
        ganancia_bruta_pesos=ganancia_bruta,
        porcion_exenta_pesos=0.0,
        base_gravable_pesos=ganancia_bruta,
        tarifa_aplicada=tarifa_general,
        impuesto_pesos=impuesto,
    )


def calcular_ganancia_ocasional_herencia(
    *,
    valor_activo_pesos: float,
    es_vivienda_habitacion_causante: bool,
    uvt: float,
    tarifa_general: float,
    porcentaje_exento_general: float,
    tope_exento_general_uvt: float,
    tope_exento_vivienda_uvt: float,
) -> ResultadoGananciaOcasional:
    exencion_general = min(
        valor_activo_pesos * porcentaje_exento_general,
        a_pesos(tope_exento_general_uvt, uvt),
    )

    exencion_vivienda = 0.0
    if es_vivienda_habitacion_causante:
        exencion_vivienda = min(
            valor_activo_pesos - exencion_general,
            a_pesos(tope_exento_vivienda_uvt, uvt),
        )
        exencion_vivienda = max(exencion_vivienda, 0.0)

    porcion_exenta = exencion_general + exencion_vivienda
    base_gravable = max(valor_activo_pesos - porcion_exenta, 0.0)
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
    valor_premio_pesos: float,
    tarifa_loterias: float,
) -> ResultadoGananciaOcasional:
    """
    Loterías, rifas, apuestas y similares no tienen porción exenta y tributan
    a una tarifa fija distinta de la tarifa general de ganancia ocasional.
    """
    impuesto = valor_premio_pesos * tarifa_loterias
    return ResultadoGananciaOcasional(
        ganancia_bruta_pesos=valor_premio_pesos,
        porcion_exenta_pesos=0.0,
        base_gravable_pesos=valor_premio_pesos,
        tarifa_aplicada=tarifa_loterias,
        impuesto_pesos=impuesto,
    )
