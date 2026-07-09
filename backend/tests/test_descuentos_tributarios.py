import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.descuentos_tributarios import (
    calcular_descuento_donaciones,
    aplicar_limite_descuentos_tributarios,
)


def test_descuento_donaciones_es_el_25_por_ciento_del_valor():
    resultado = calcular_descuento_donaciones(
        valor_donado_pesos=1_000_000, tarifa_descuento=P.TARIFA_DESCUENTO_DONACIONES
    )
    assert resultado == 250_000


def test_limite_descuentos_no_supera_el_30_por_ciento_del_impuesto_basico():
    resultado = aplicar_limite_descuentos_tributarios(
        impuesto_basico_renta_pesos=10_000_000,
        total_descuentos_pesos=5_000_000,  # 50% del impuesto, supera el límite
        limite_porcentaje=P.LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE,
    )
    assert resultado.limite_aplicable_pesos == 3_000_000
    assert resultado.descuento_aplicado_pesos == 3_000_000
    assert resultado.impuesto_neto_pesos == 7_000_000
    assert resultado.descuento_no_utilizado_pesos == 2_000_000


def test_descuentos_bajo_el_limite_se_aplican_completos():
    resultado = aplicar_limite_descuentos_tributarios(
        impuesto_basico_renta_pesos=10_000_000,
        total_descuentos_pesos=1_000_000,
        limite_porcentaje=P.LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE,
    )
    assert resultado.descuento_aplicado_pesos == 1_000_000
    assert resultado.impuesto_neto_pesos == 9_000_000
    assert resultado.descuento_no_utilizado_pesos == 0
