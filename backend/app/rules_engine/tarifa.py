"""
Motor de reglas tributarias — funciones puras.

Reglas de diseño de este módulo:
  1. Ninguna función aquí accede a base de datos, red, ni framework web.
  2. Ninguna función aquí recibe una sesión de usuario ni un request HTTP.
  3. Todos los parámetros normativos (UVT, tarifas, topes) se reciben como
     argumento (típicamente desde un módulo `parametros_<anio>.py`), nunca
     como literales dentro de las fórmulas.

Esto permite probar el motor de forma aislada y reutilizarlo desde cualquier
interfaz (API actual, futura interfaz de línea de comandos, notebooks de
validación con el contador, etc.).
"""

from dataclasses import dataclass


def a_uvt(pesos: float, uvt: float) -> float:
    return pesos / uvt


def a_pesos(valor_uvt: float, uvt: float) -> float:
    return valor_uvt * uvt


def calcular_impuesto_uvt(base_uvt: float, tabla_tarifa_uvt: list) -> float:
    """
    Aplica la tabla progresiva del artículo 241 E.T.

    tabla_tarifa_uvt: lista de tuplas (limite_inferior, limite_superior, tarifa, base_uvt)
    """
    if base_uvt <= 0:
        return 0.0
    for limite_inferior, limite_superior, tarifa, base in tabla_tarifa_uvt:
        dentro_del_tramo = base_uvt > limite_inferior and (
            limite_superior is None or base_uvt <= limite_superior
        )
        if dentro_del_tramo:
            return base + (base_uvt - limite_inferior) * tarifa
    # Si no cayó en ningún tramo (no debería ocurrir con una tabla bien formada),
    # se aplica el último tramo como salvaguarda.
    limite_inferior, _, tarifa, base = tabla_tarifa_uvt[-1]
    return base + (base_uvt - limite_inferior) * tarifa


def calcular_renta_exenta_laboral(
    ingreso_salarios_pesos: float,
    uvt: float,
    porcentaje: float,
    tope_uvt: float,
) -> float:
    base = ingreso_salarios_pesos * porcentaje
    tope_pesos = a_pesos(tope_uvt, uvt)
    return min(base, tope_pesos)


def calcular_limite_exenciones_cedula_general(
    total_ingresos_brutos_pesos: float,
    uvt: float,
    porcentaje_limite: float,
    tope_uvt: float,
) -> float:
    tope_pesos = a_pesos(tope_uvt, uvt)
    limite_porcentual = total_ingresos_brutos_pesos * porcentaje_limite
    return min(tope_pesos, limite_porcentual)


@dataclass
class ResultadoLiquidacion:
    renta_liquida_gravable_pesos: float
    impuesto_uvt: float
    impuesto_a_cargo_pesos: float
    total_retenciones_pesos: float
    saldo_pesos: float  # positivo = saldo a pagar, negativo = saldo a favor

    @property
    def es_saldo_a_pagar(self) -> bool:
        return self.saldo_pesos >= 0


def liquidar(
    *,
    total_ingresos_brutos_pesos: float,
    deducciones_imputables_pesos: float,
    ingreso_salarios_pesos: float,
    total_retenciones_pesos: float,
    patrimonio_liquido_anterior_pesos: float,
    uvt: float,
    tabla_tarifa_uvt: list,
    porcentaje_renta_exenta_laboral: float,
    tope_renta_exenta_laboral_uvt: float,
    porcentaje_limite_exenciones: float,
    tope_limite_exenciones_uvt: float,
    tarifa_renta_presuntiva: float,
) -> ResultadoLiquidacion:
    """
    Orquesta el cálculo completo de liquidación privada a partir de los
    totales ya depurados de patrimonio e ingresos. No conoce de dónde vienen
    esos totales (API, carga masiva, pruebas) — solo aplica las reglas.
    """
    renta_exenta_laboral = calcular_renta_exenta_laboral(
        ingreso_salarios_pesos, uvt, porcentaje_renta_exenta_laboral, tope_renta_exenta_laboral_uvt
    )

    limite_exenciones = calcular_limite_exenciones_cedula_general(
        total_ingresos_brutos_pesos, uvt, porcentaje_limite_exenciones, tope_limite_exenciones_uvt
    )

    exenciones_aplicadas = min(
        deducciones_imputables_pesos + renta_exenta_laboral, limite_exenciones
    )

    renta_liquida_cedular = max(total_ingresos_brutos_pesos - exenciones_aplicadas, 0.0)

    renta_presuntiva_pesos = max(patrimonio_liquido_anterior_pesos, 0.0) * tarifa_renta_presuntiva

    renta_liquida_gravable = max(renta_liquida_cedular, renta_presuntiva_pesos)

    impuesto_uvt = calcular_impuesto_uvt(a_uvt(renta_liquida_gravable, uvt), tabla_tarifa_uvt)
    impuesto_a_cargo = a_pesos(impuesto_uvt, uvt)

    saldo = impuesto_a_cargo - total_retenciones_pesos

    return ResultadoLiquidacion(
        renta_liquida_gravable_pesos=renta_liquida_gravable,
        impuesto_uvt=impuesto_uvt,
        impuesto_a_cargo_pesos=impuesto_a_cargo,
        total_retenciones_pesos=total_retenciones_pesos,
        saldo_pesos=saldo,
    )
