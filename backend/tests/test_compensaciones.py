import pytest

from app.rules_engine.compensaciones import calcular_compensacion_perdida


def test_perdida_menor_a_la_renta_se_usa_completa():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=10_000_000, perdida_disponible_pesos=4_000_000
    )
    assert resultado.perdida_utilizada_pesos == 4_000_000
    assert resultado.perdida_remanente_pesos == 0
    assert resultado.renta_liquida_despues_de_compensar_pesos == 6_000_000


def test_perdida_mayor_a_la_renta_deja_remanente():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=3_000_000, perdida_disponible_pesos=10_000_000
    )
    assert resultado.perdida_utilizada_pesos == 3_000_000
    assert resultado.perdida_remanente_pesos == 7_000_000
    assert resultado.renta_liquida_despues_de_compensar_pesos == 0


def test_sin_perdida_disponible_no_cambia_la_renta():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=5_000_000, perdida_disponible_pesos=0
    )
    assert resultado.renta_liquida_despues_de_compensar_pesos == 5_000_000


def test_renta_liquida_negativa_se_trata_como_cero():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=-1_000_000, perdida_disponible_pesos=5_000_000
    )
    assert resultado.renta_liquida_antes_de_compensar_pesos == 0
    assert resultado.perdida_utilizada_pesos == 0
    assert resultado.perdida_remanente_pesos == 5_000_000
