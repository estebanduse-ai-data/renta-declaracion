"""
Deducciones específicas de la cédula general, cada una con su propio tope
legal (art. 119, 387 E.T.). Reemplaza los campos genéricos del prototipo
inicial por el cálculo real de cada tope.
"""

from app.rules_engine.tarifa import a_pesos, a_uvt


def calcular_deduccion_intereses_vivienda(
    *, intereses_pagados_anio_pesos: float, uvt: float, tope_uvt: float
) -> float:
    tope_pesos = a_pesos(tope_uvt, uvt)
    return min(max(intereses_pagados_anio_pesos, 0.0), tope_pesos)


def calcular_deduccion_intereses_vivienda_icetex(
    *,
    intereses_vivienda_pesos: float,
    intereses_icetex_pesos: float,
    uvt: float,
    tope_uvt: float,
) -> float:
    """
    El artículo 119 E.T. comparte UN SOLO tope anual (1.200 UVT) entre los
    intereses de crédito de vivienda y los intereses de créditos educativos
    ICETEX — no son topes independientes que se puedan sumar por separado.
    Usar esta función en vez de `calcular_deduccion_intereses_vivienda`
    cuando el declarante tiene ambos conceptos en el mismo año.
    """
    total_intereses = max(intereses_vivienda_pesos, 0.0) + max(intereses_icetex_pesos, 0.0)
    tope_pesos = a_pesos(tope_uvt, uvt)
    return min(total_intereses, tope_pesos)


def calcular_deduccion_salud(
    *, pagos_salud_anio_pesos: float, uvt: float, tope_uvt_mensual: float
) -> float:
    tope_anual_pesos = a_pesos(tope_uvt_mensual, uvt) * 12
    return min(max(pagos_salud_anio_pesos, 0.0), tope_anual_pesos)


def calcular_deduccion_dependientes(
    *,
    ingreso_laboral_anio_pesos: float,
    numero_dependientes: int,
    uvt: float,
    porcentaje_ingreso: float,
    tope_uvt_mensual: float,
    maximo_dependientes_reconocidos: int,
) -> float:
    """
    El art. 387 E.T. reconoce la deducción por dependientes como un valor
    único (no acumulativo por número de personas a cargo): se calcula sobre
    el ingreso laboral total, limitado a 32 UVT mensuales, independientemente
    de si el contribuyente certifica 1 o 4 dependientes. `numero_dependientes`
    solo determina si hay derecho a la deducción (mínimo 1) — no la
    multiplica. Confirmar esta interpretación con el contador antes de
    producción; ver `docs/FALTANTES.md`.
    """
    if numero_dependientes <= 0:
        return 0.0

    tope_anual_pesos = a_pesos(tope_uvt_mensual, uvt) * 12
    base_porcentual = ingreso_laboral_anio_pesos * porcentaje_ingreso
    return min(base_porcentual, tope_anual_pesos)


def calcular_exencion_cesantias(
    *,
    valor_cesantias_e_intereses_pesos: float,
    promedio_mensual_ingresos_ultimos_6_meses_pesos: float,
    uvt: float,
    tabla_exencion_uvt_mensual: list,
) -> float:
    """
    Renta exenta sobre cesantías e intereses de cesantías (art. 206 num. 4
    E.T.). El porcentaje exento depende del promedio mensual de ingresos
    laborales de los últimos 6 meses, expresado en UVT: entre más alto el
    ingreso promedio, menor el porcentaje exento, hasta llegar a 0% sobre
    650 UVT mensuales.
    """
    promedio_uvt = a_uvt(promedio_mensual_ingresos_ultimos_6_meses_pesos, uvt)

    porcentaje_exento = 0.0
    for limite_inferior, limite_superior, porcentaje in tabla_exencion_uvt_mensual:
        dentro_del_tramo = promedio_uvt > limite_inferior and (
            limite_superior is None or promedio_uvt <= limite_superior
        )
        if dentro_del_tramo:
            porcentaje_exento = porcentaje
            break
        if limite_inferior == 0 and promedio_uvt == 0:
            porcentaje_exento = porcentaje
            break

    return max(valor_cesantias_e_intereses_pesos, 0.0) * porcentaje_exento


def calcular_exencion_becas(
    *, valor_beca_pesos: float, es_contraprestacion_por_servicios: bool
) -> float:
    """
    Las becas de estudio están exentas en su totalidad (art. 206 num. 9
    E.T.), siempre que no constituyan una contraprestación por servicios
    prestados por el becario — en ese caso se tratan como un ingreso laboral
    ordinario, sin exención.
    """
    if es_contraprestacion_por_servicios:
        return 0.0
    return max(valor_beca_pesos, 0.0)
