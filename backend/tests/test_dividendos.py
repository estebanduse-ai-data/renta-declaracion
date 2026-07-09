import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import a_pesos
from app.rules_engine.dividendos import calcular_impuesto_dividendos


def test_dividendos_gravados_bajo_el_tope_no_pagan_impuesto():
    resultado = calcular_impuesto_dividendos(
        dividendos_gravados_pesos=a_pesos(900, P.UVT),
        dividendos_no_gravados_sociedad_pesos=0,
        uvt=P.UVT,
        tabla_tarifa_dividendos_uvt=P.TABLA_TARIFA_DIVIDENDOS_UVT,
        tarifa_dividendos_no_gravados_sociedad=P.TARIFA_DIVIDENDOS_NO_GRAVADOS_SOCIEDAD,
    )
    assert resultado["impuesto_total_pesos"] == 0


def test_dividendos_gravados_sobre_el_tope_tributan_al_15_por_ciento_marginal():
    resultado = calcular_impuesto_dividendos(
        dividendos_gravados_pesos=a_pesos(2_090, P.UVT),
        dividendos_no_gravados_sociedad_pesos=0,
        uvt=P.UVT,
        tabla_tarifa_dividendos_uvt=P.TABLA_TARIFA_DIVIDENDOS_UVT,
        tarifa_dividendos_no_gravados_sociedad=P.TARIFA_DIVIDENDOS_NO_GRAVADOS_SOCIEDAD,
    )
    esperado = a_pesos(1_000, P.UVT) * 0.15  # (2.090 - 1.090) UVT al 15%
    assert resultado["impuesto_total_pesos"] == pytest.approx(esperado)


def test_dividendos_no_gravados_sociedad_pagan_primero_la_tarifa_corporativa():
    resultado = calcular_impuesto_dividendos(
        dividendos_gravados_pesos=0,
        dividendos_no_gravados_sociedad_pesos=a_pesos(1_000, P.UVT),
        uvt=P.UVT,
        tabla_tarifa_dividendos_uvt=P.TABLA_TARIFA_DIVIDENDOS_UVT,
        tarifa_dividendos_no_gravados_sociedad=P.TARIFA_DIVIDENDOS_NO_GRAVADOS_SOCIEDAD,
    )
    impuesto_corporativo_esperado = a_pesos(1_000, P.UVT) * 0.35
    assert resultado["impuesto_corporativo_equivalente_pesos"] == pytest.approx(
        impuesto_corporativo_esperado
    )
    # El remanente (650 UVT) queda bajo el tope de 1.090 UVT de la tabla marginal,
    # así que no genera impuesto adicional.
    assert resultado["impuesto_tabla_marginal_pesos"] == 0
