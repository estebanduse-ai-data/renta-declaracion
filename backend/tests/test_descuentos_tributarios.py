from decimal import Decimal

from app.rules_engine import parametros_2025 as P
from app.rules_engine.descuentos_tributarios import (
    calcular_descuento_donaciones,
    aplicar_limite_descuentos_tributarios,
)


def test_descuento_donaciones_es_el_25_por_ciento_del_valor():
    resultado = calcular_descuento_donaciones(
        valor_donado_pesos=Decimal("1000000"),
        tarifa_descuento=P.TARIFA_DESCUENTO_DONACIONES,
    )
    assert resultado == Decimal("250000")


def test_limite_descuentos_no_supera_el_30_por_ciento_del_impuesto_basico():
    resultado = aplicar_limite_descuentos_tributarios(
        impuesto_basico_renta_pesos=Decimal("10000000"),
        total_descuentos_pesos=Decimal("5000000"),
        limite_porcentaje=P.LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE,
    )
    assert resultado.limite_aplicable_pesos == Decimal("3000000")
    assert resultado.descuento_aplicado_pesos == Decimal("3000000")
    assert resultado.impuesto_neto_pesos == Decimal("7000000")
    assert resultado.descuento_no_utilizado_pesos == Decimal("2000000")


def test_descuentos_bajo_el_limite_se_aplican_completos():
    resultado = aplicar_limite_descuentos_tributarios(
        impuesto_basico_renta_pesos=Decimal("10000000"),
        total_descuentos_pesos=Decimal("1000000"),
        limite_porcentaje=P.LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE,
    )
    assert resultado.descuento_aplicado_pesos == Decimal("1000000")
    assert resultado.impuesto_neto_pesos == Decimal("9000000")
    assert resultado.descuento_no_utilizado_pesos == Decimal("0")