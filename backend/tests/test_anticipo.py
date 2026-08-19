from decimal import Decimal

import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.anticipo import calcular_anticipo_renta


def test_primera_vez_declarando_usa_25_por_ciento():
    resultado = calcular_anticipo_renta(
        impuesto_neto_actual_pesos=Decimal("10000000"),
        impuesto_neto_anterior_pesos=Decimal("0"),
        anios_declarando=1,
        porcentaje_primera_vez=P.ANTICIPO_PORCENTAJE_PRIMERA_VEZ,
        porcentaje_segunda_vez=P.ANTICIPO_PORCENTAJE_SEGUNDA_VEZ,
        porcentaje_tercera_vez_en_adelante=P.ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE,
    )
    assert resultado.porcentaje_aplicado == Decimal("0.25")
    # Primera vez: promedio con el año anterior (0) reduce el método promedio,
    # así que el anticipo elegido debe ser el menor entre los dos métodos.
    assert resultado.anticipo_a_pagar_pesos == min(Decimal("2500000"), Decimal("1250000"))


def test_segunda_vez_declarando_usa_50_por_ciento():
    resultado = calcular_anticipo_renta(
        impuesto_neto_actual_pesos=Decimal("10000000"),
        impuesto_neto_anterior_pesos=Decimal("8000000"),
        anios_declarando=2,
        porcentaje_primera_vez=P.ANTICIPO_PORCENTAJE_PRIMERA_VEZ,
        porcentaje_segunda_vez=P.ANTICIPO_PORCENTAJE_SEGUNDA_VEZ,
        porcentaje_tercera_vez_en_adelante=P.ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE,
    )
    assert resultado.porcentaje_aplicado == Decimal("0.50")
    assert resultado.anticipo_metodo_individual_pesos == Decimal("5000000")
    assert resultado.anticipo_metodo_promedio_pesos == Decimal("9000000") * Decimal("0.50")
    assert resultado.anticipo_a_pagar_pesos == Decimal("4500000")


def test_tercera_vez_en_adelante_usa_75_por_ciento():
    resultado = calcular_anticipo_renta(
        impuesto_neto_actual_pesos=Decimal("10000000"),
        impuesto_neto_anterior_pesos=Decimal("10000000"),
        anios_declarando=5,
        porcentaje_primera_vez=P.ANTICIPO_PORCENTAJE_PRIMERA_VEZ,
        porcentaje_segunda_vez=P.ANTICIPO_PORCENTAJE_SEGUNDA_VEZ,
        porcentaje_tercera_vez_en_adelante=P.ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE,
    )
    assert resultado.porcentaje_aplicado == Decimal("0.75")
    assert resultado.anticipo_a_pagar_pesos == Decimal("7500000")


def test_retenciones_estimadas_reducen_el_saldo_neto_del_anticipo():
    resultado = calcular_anticipo_renta(
        impuesto_neto_actual_pesos=Decimal("10000000"),
        impuesto_neto_anterior_pesos=Decimal("10000000"),
        anios_declarando=5,
        retenciones_estimadas_anio_siguiente_pesos=Decimal("3000000"),
        porcentaje_primera_vez=P.ANTICIPO_PORCENTAJE_PRIMERA_VEZ,
        porcentaje_segunda_vez=P.ANTICIPO_PORCENTAJE_SEGUNDA_VEZ,
        porcentaje_tercera_vez_en_adelante=P.ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE,
    )
    assert resultado.saldo_anticipo_neto_pesos == Decimal("4500000")


def test_saldo_neto_del_anticipo_nunca_es_negativo():
    resultado = calcular_anticipo_renta(
        impuesto_neto_actual_pesos=Decimal("1000000"),
        impuesto_neto_anterior_pesos=Decimal("1000000"),
        anios_declarando=5,
        retenciones_estimadas_anio_siguiente_pesos=Decimal("999000000"),
        porcentaje_primera_vez=P.ANTICIPO_PORCENTAJE_PRIMERA_VEZ,
        porcentaje_segunda_vez=P.ANTICIPO_PORCENTAJE_SEGUNDA_VEZ,
        porcentaje_tercera_vez_en_adelante=P.ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE,
    )
    assert resultado.saldo_anticipo_neto_pesos == Decimal("0")