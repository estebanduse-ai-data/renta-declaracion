"""
Deducciones específicas de la cédula general (DT-5 — migración a Decimal).

Cambios respecto a la versión float
─────────────────────────────────────
Todas las firmas cambian de `float` a `Decimal`. Los cálculos intermedios
(base_porcentual, tope_anual_pesos, total_intereses) son ahora Decimal,
eliminando el error de representación IEEE 754 en multiplicaciones de
valores grandes de patrimonio o ingresos.

Los imports de `a_pesos` y `a_uvt` vienen de `tarifa.py`, que también
fue migrado a Decimal en DT-5. El comportamiento semántico es idéntico
al de la versión float — solo cambia el tipo de los operandos.
"""

from decimal import Decimal

from app.rules_engine.tarifa import a_pesos, a_uvt

_CERO = Decimal("0")


def calcular_deduccion_intereses_vivienda(
    *,
    intereses_pagados_anio_pesos: Decimal,
    uvt: Decimal,
    tope_uvt: Decimal,
) -> Decimal:
    """
    Deducción por intereses en préstamos de vivienda (art. 119 E.T.).
    Tope: 1.200 UVT anuales para 2025.
    """
    tope_pesos = a_pesos(tope_uvt, uvt)
    return min(max(intereses_pagados_anio_pesos, _CERO), tope_pesos)


def calcular_deduccion_intereses_vivienda_icetex(
    *,
    intereses_vivienda_pesos: Decimal,
    intereses_icetex_pesos: Decimal,
    uvt: Decimal,
    tope_uvt: Decimal,
) -> Decimal:
    """
    El artículo 119 E.T. comparte UN SOLO tope anual (1.200 UVT) entre los
    intereses de crédito de vivienda y los intereses de créditos educativos
    ICETEX — no son topes independientes que se puedan sumar por separado.
    Usar esta función cuando el declarante tiene ambos conceptos en el mismo año.
    """
    total_intereses = max(intereses_vivienda_pesos, _CERO) + max(intereses_icetex_pesos, _CERO)
    tope_pesos = a_pesos(tope_uvt, uvt)
    return min(total_intereses, tope_pesos)


def calcular_deduccion_salud(
    *,
    pagos_salud_anio_pesos: Decimal,
    uvt: Decimal,
    tope_uvt_mensual: Decimal,
) -> Decimal:
    """
    Deducción por pagos de salud: medicina prepagada y pólizas (art. 387 E.T.).
    Tope: 16 UVT mensuales = 192 UVT anuales para 2025.
    """
    tope_anual_pesos = a_pesos(tope_uvt_mensual, uvt) * Decimal("12")
    return min(max(pagos_salud_anio_pesos, _CERO), tope_anual_pesos)


def calcular_deduccion_dependientes(
    *,
    ingreso_laboral_anio_pesos: Decimal,
    numero_dependientes: int,
    uvt: Decimal,
    porcentaje_ingreso: Decimal,
    tope_uvt_mensual: Decimal,
    maximo_dependientes_reconocidos: int,
) -> Decimal:
    """
    Deducción por dependientes económicos (art. 387 E.T.).

    El art. 387 E.T. reconoce la deducción como un valor único (no
    acumulativo por número de personas a cargo): se calcula sobre el
    ingreso laboral total, limitado a 32 UVT mensuales, independientemente
    de si el contribuyente certifica 1 o 4 dependientes. `numero_dependientes`
    solo determina si hay derecho a la deducción (mínimo 1) — no la multiplica.

    Confirmar esta interpretación con el contador antes de producción;
    ver docs/FALTANTES.md.
    """
    if numero_dependientes <= 0:
        return _CERO

    tope_anual_pesos = a_pesos(tope_uvt_mensual, uvt) * Decimal("12")
    base_porcentual = ingreso_laboral_anio_pesos * porcentaje_ingreso
    return min(base_porcentual, tope_anual_pesos)


def calcular_exencion_cesantias(
    *,
    valor_cesantias_e_intereses_pesos: Decimal,
    promedio_mensual_ingresos_ultimos_6_meses_pesos: Decimal,
    uvt: Decimal,
    tabla_exencion_uvt_mensual: list,
) -> Decimal:
    """
    Renta exenta sobre cesantías e intereses de cesantías (art. 206 num. 4 E.T.).
    El porcentaje exento depende del promedio mensual de ingresos laborales
    de los últimos 6 meses en UVT: a mayor ingreso, menor porcentaje exento.

    tabla_exencion_uvt_mensual: lista de tuplas
        (limite_inferior: Decimal, limite_superior: Decimal | None, porcentaje: Decimal)
    """
    promedio_uvt = a_uvt(promedio_mensual_ingresos_ultimos_6_meses_pesos, uvt)

    porcentaje_exento = _CERO
    for limite_inferior, limite_superior, porcentaje in tabla_exencion_uvt_mensual:
        dentro_del_tramo = promedio_uvt > limite_inferior and (
            limite_superior is None or promedio_uvt <= limite_superior
        )
        if dentro_del_tramo:
            porcentaje_exento = porcentaje
            break
        if limite_inferior == _CERO and promedio_uvt == _CERO:
            porcentaje_exento = porcentaje
            break

    return max(valor_cesantias_e_intereses_pesos, _CERO) * porcentaje_exento


def calcular_exencion_becas(
    *,
    valor_beca_pesos: Decimal,
    es_contraprestacion_por_servicios: bool,
) -> Decimal:
    """
    Renta exenta sobre becas de estudio (art. 206 num. 9 E.T.).
    Exentas en su totalidad siempre que no sean contraprestación por servicios.
    """
    if es_contraprestacion_por_servicios:
        return _CERO
    return max(valor_beca_pesos, _CERO)