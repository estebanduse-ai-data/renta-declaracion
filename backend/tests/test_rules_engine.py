"""
Pruebas del motor de reglas tributarias.

Estas pruebas son la primera línea de defensa contra el riesgo #1 de
`docs/RIESGOS.md` (errores de cálculo no detectados a tiempo). Deben
ampliarse con casos reales tomados del Excel actual durante la fase de
pruebas de paridad (ver `docs/PLAN_DE_TRABAJO.md`).
"""

import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import (
    a_pesos,
    a_uvt,
    calcular_impuesto_uvt,
    calcular_renta_exenta_laboral,
    liquidar,
)


def test_conversion_uvt_pesos_es_reversible():
    valor_uvt = 1000
    pesos = a_pesos(valor_uvt, P.UVT)
    assert a_uvt(pesos, P.UVT) == pytest.approx(valor_uvt)


def test_impuesto_es_cero_bajo_el_primer_tramo():
    assert calcular_impuesto_uvt(500, P.TABLA_TARIFA_UVT) == 0
    assert calcular_impuesto_uvt(1090, P.TABLA_TARIFA_UVT) == 0


def test_impuesto_justo_en_el_limite_del_primer_tramo_gravable():
    # 1090.01 UVT debe empezar a tributar al 19%
    resultado = calcular_impuesto_uvt(1090.01, P.TABLA_TARIFA_UVT)
    assert resultado == pytest.approx(0.01 * 0.19, rel=1e-3)


def test_impuesto_tramo_mas_alto_usa_base_acumulada():
    resultado = calcular_impuesto_uvt(35_000, P.TABLA_TARIFA_UVT)
    esperado = 11_352 + (35_000 - 31_000) * 0.39
    assert resultado == pytest.approx(esperado)


def test_renta_liquida_negativa_no_genera_impuesto_negativo():
    assert calcular_impuesto_uvt(-100, P.TABLA_TARIFA_UVT) == 0


def test_renta_exenta_laboral_respeta_el_tope():
    ingreso_alto = a_pesos(10_000, P.UVT)  # muy por encima del tope
    exenta = calcular_renta_exenta_laboral(
        ingreso_alto, P.UVT, P.PORCENTAJE_RENTA_EXENTA_LABORAL, P.TOPE_RENTA_EXENTA_LABORAL_UVT
    )
    assert exenta == pytest.approx(a_pesos(P.TOPE_RENTA_EXENTA_LABORAL_UVT, P.UVT))


def test_liquidar_declarante_sin_ingresos_no_genera_impuesto():
    resultado = liquidar(
        total_ingresos_brutos_pesos=0,
        deducciones_imputables_pesos=0,
        ingreso_salarios_pesos=0,
        total_retenciones_pesos=0,
        patrimonio_liquido_anterior_pesos=0,
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )
    assert resultado.impuesto_a_cargo_pesos == 0
    assert resultado.saldo_pesos == 0


def test_liquidar_con_retenciones_mayores_al_impuesto_da_saldo_a_favor():
    resultado = liquidar(
        total_ingresos_brutos_pesos=a_pesos(500, P.UVT),  # bajo el mínimo gravable
        deducciones_imputables_pesos=0,
        ingreso_salarios_pesos=a_pesos(500, P.UVT),
        total_retenciones_pesos=a_pesos(10, P.UVT),
        patrimonio_liquido_anterior_pesos=0,
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )
    assert not resultado.es_saldo_a_pagar
    assert resultado.saldo_pesos < 0


def test_renta_presuntiva_actualmente_no_incrementa_la_base_2025():
    # Con tarifa 0% (parámetro vigente 2025), un patrimonio líquido alto no debe
    # forzar renta líquida gravable si la cedular es menor.
    resultado = liquidar(
        total_ingresos_brutos_pesos=0,
        deducciones_imputables_pesos=0,
        ingreso_salarios_pesos=0,
        total_retenciones_pesos=0,
        patrimonio_liquido_anterior_pesos=a_pesos(50_000, P.UVT),
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )
    assert resultado.renta_liquida_gravable_pesos == 0
