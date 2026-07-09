"""
Deducciones específicas de la cédula general, cada una con su propio tope
legal (art. 119, 387 E.T.). Reemplaza los campos genéricos del prototipo
inicial por el cálculo real de cada tope.
"""

from app.rules_engine.tarifa import a_pesos


def calcular_deduccion_intereses_vivienda(
    *, intereses_pagados_anio_pesos: float, uvt: float, tope_uvt: float
) -> float:
    tope_pesos = a_pesos(tope_uvt, uvt)
    return min(max(intereses_pagados_anio_pesos, 0.0), tope_pesos)


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
