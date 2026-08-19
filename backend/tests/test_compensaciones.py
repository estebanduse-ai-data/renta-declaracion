from decimal import Decimal

from app.rules_engine.compensaciones import calcular_compensacion_perdida


def test_perdida_menor_a_la_renta_se_usa_completa():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=Decimal("10000000"),
        perdida_disponible_pesos=Decimal("4000000"),
    )
    assert resultado.perdida_utilizada_pesos == Decimal("4000000")
    assert resultado.perdida_remanente_pesos == Decimal("0")
    assert resultado.renta_liquida_despues_de_compensar_pesos == Decimal("6000000")


def test_perdida_mayor_a_la_renta_deja_remanente():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=Decimal("3000000"),
        perdida_disponible_pesos=Decimal("10000000"),
    )
    assert resultado.perdida_utilizada_pesos == Decimal("3000000")
    assert resultado.perdida_remanente_pesos == Decimal("7000000")
    assert resultado.renta_liquida_despues_de_compensar_pesos == Decimal("0")


def test_sin_perdida_disponible_no_cambia_la_renta():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=Decimal("5000000"),
        perdida_disponible_pesos=Decimal("0"),
    )
    assert resultado.renta_liquida_despues_de_compensar_pesos == Decimal("5000000")


def test_renta_liquida_negativa_se_trata_como_cero():
    resultado = calcular_compensacion_perdida(
        renta_liquida_cedular_pesos=Decimal("-1000000"),
        perdida_disponible_pesos=Decimal("5000000"),
    )
    assert resultado.renta_liquida_antes_de_compensar_pesos == Decimal("0")
    assert resultado.perdida_utilizada_pesos == Decimal("0")
    assert resultado.perdida_remanente_pesos == Decimal("5000000")