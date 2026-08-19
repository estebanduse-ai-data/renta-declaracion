from decimal import Decimal

import pytest

from app.rules_engine.moneda_extranjera import (
    valorar_patrimonio_moneda_extranjera,
    valorar_ingreso_moneda_extranjera,
    consolidar_patrimonio_moneda_extranjera,
)


def test_patrimonio_moneda_extranjera_usa_trm_de_cierre():
    resultado = valorar_patrimonio_moneda_extranjera(
        valor_moneda_extranjera=Decimal("10000"),
        trm_cierre_anio=Decimal("4100"),
    )
    assert resultado.valor_pesos == Decimal("41000000")


def test_ingreso_moneda_extranjera_usa_trm_del_dia():
    resultado = valorar_ingreso_moneda_extranjera(
        valor_moneda_extranjera=Decimal("1000"),
        trm_dia_operacion=Decimal("3950"),
    )
    assert resultado.valor_pesos == Decimal("3950000")


def test_trm_invalida_lanza_error():
    with pytest.raises(ValueError):
        valorar_patrimonio_moneda_extranjera(
            valor_moneda_extranjera=Decimal("1000"),
            trm_cierre_anio=Decimal("0"),
        )


def test_consolidar_patrimonio_suma_varias_partidas_a_la_misma_trm():
    partidas = [
        {"valor_moneda_extranjera": Decimal("5000")},
        {"valor_moneda_extranjera": Decimal("2000")},
        {"valor_moneda_extranjera": Decimal("1000")},
    ]
    total = consolidar_patrimonio_moneda_extranjera(
        partidas=partidas, trm_cierre_anio=Decimal("4000")
    )
    assert total == Decimal("8000") * Decimal("4000")