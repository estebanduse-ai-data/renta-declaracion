from decimal import Decimal

import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import a_pesos
from app.rules_engine.ganancias_ocasionales import (
    calcular_ganancia_ocasional_venta_inmueble,
    calcular_ganancia_ocasional_venta_acciones,
    calcular_ganancia_ocasional_herencia,
    calcular_ganancia_ocasional_loteria,
    costo_fiscal_ajustado,
)

_CERO = Decimal("0")


def test_costo_fiscal_ajustado_aplica_el_factor_del_anio():
    resultado = costo_fiscal_ajustado(
        Decimal("100000000"), 2020, P.FACTORES_AJUSTE_ART73_POR_ANIO
    )
    assert resultado == pytest.approx(float(Decimal("100000000") * Decimal("1.412")))


def test_costo_fiscal_ajustado_usa_1_si_el_anio_no_esta_en_la_tabla():
    resultado = costo_fiscal_ajustado(
        Decimal("100000000"), 1990, P.FACTORES_AJUSTE_ART73_POR_ANIO
    )
    assert resultado == Decimal("100000000")


def test_venta_inmueble_casa_habitacion_exenta_hasta_el_tope():
    resultado = calcular_ganancia_ocasional_venta_inmueble(
        precio_venta_pesos=a_pesos(Decimal("10000"), P.UVT),
        costo_adquisicion_pesos=a_pesos(Decimal("1000"), P.UVT),
        anio_adquisicion=2025,
        es_casa_habitacion_unica=True,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_exento_casa_habitacion_uvt=P.TOPE_EXENTO_VENTA_CASA_HABITACION_UVT,
        factores_ajuste_por_anio=P.FACTORES_AJUSTE_ART73_POR_ANIO,
    )
    assert resultado.porcion_exenta_pesos == pytest.approx(float(a_pesos(Decimal("5000"), P.UVT)))
    assert resultado.base_gravable_pesos == pytest.approx(float(a_pesos(Decimal("4000"), P.UVT)))
    assert resultado.impuesto_pesos == pytest.approx(
        float(a_pesos(Decimal("4000"), P.UVT) * P.TARIFA_GANANCIA_OCASIONAL_GENERAL)
    )


def test_venta_inmueble_sin_beneficio_de_casa_habitacion_tributa_todo():
    resultado = calcular_ganancia_ocasional_venta_inmueble(
        precio_venta_pesos=a_pesos(Decimal("10000"), P.UVT),
        costo_adquisicion_pesos=a_pesos(Decimal("1000"), P.UVT),
        anio_adquisicion=2025,
        es_casa_habitacion_unica=False,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_exento_casa_habitacion_uvt=P.TOPE_EXENTO_VENTA_CASA_HABITACION_UVT,
        factores_ajuste_por_anio=P.FACTORES_AJUSTE_ART73_POR_ANIO,
    )
    assert resultado.porcion_exenta_pesos == _CERO
    assert resultado.base_gravable_pesos == pytest.approx(float(a_pesos(Decimal("9000"), P.UVT)))


def test_venta_acciones_bolsa_bajo_el_tope_no_genera_impuesto():
    resultado = calcular_ganancia_ocasional_venta_acciones(
        precio_venta_pesos=a_pesos(Decimal("5000"), P.UVT),
        costo_fiscal_pesos=a_pesos(Decimal("1000"), P.UVT),
        cotiza_en_bolsa=True,
        porcentaje_participacion_vendida=Decimal("0.02"),
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_participacion_bolsa_no_gravado=P.TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO,
    )
    assert resultado.impuesto_pesos == _CERO


def test_venta_acciones_bolsa_sobre_el_tope_si_tributa():
    resultado = calcular_ganancia_ocasional_venta_acciones(
        precio_venta_pesos=a_pesos(Decimal("5000"), P.UVT),
        costo_fiscal_pesos=a_pesos(Decimal("1000"), P.UVT),
        cotiza_en_bolsa=True,
        porcentaje_participacion_vendida=Decimal("0.05"),
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        tope_participacion_bolsa_no_gravado=P.TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO,
    )
    assert resultado.impuesto_pesos == pytest.approx(
        float(a_pesos(Decimal("4000"), P.UVT) * P.TARIFA_GANANCIA_OCASIONAL_GENERAL)
    )


def test_herencia_vivienda_suma_las_dos_exenciones():
    valor_activo = a_pesos(Decimal("10000"), P.UVT)
    resultado = calcular_ganancia_ocasional_herencia(
        valor_activo_pesos=valor_activo,
        es_vivienda_habitacion_causante=True,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        porcentaje_exento_general=P.PORCENTAJE_EXENTO_HERENCIA_GENERAL,
        tope_exento_general_uvt=P.TOPE_EXENTO_HERENCIA_GENERAL_UVT,
        tope_exento_vivienda_uvt=P.TOPE_EXENTO_HERENCIA_VIVIENDA_UVT,
    )
    exencion_esperada = a_pesos(Decimal("1625"), P.UVT) + a_pesos(Decimal("3250"), P.UVT)
    assert resultado.porcion_exenta_pesos == pytest.approx(float(exencion_esperada))


def test_herencia_general_sin_vivienda_solo_aplica_exencion_general():
    valor_activo = a_pesos(Decimal("5000"), P.UVT)
    resultado = calcular_ganancia_ocasional_herencia(
        valor_activo_pesos=valor_activo,
        es_vivienda_habitacion_causante=False,
        uvt=P.UVT,
        tarifa_general=P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        porcentaje_exento_general=P.PORCENTAJE_EXENTO_HERENCIA_GENERAL,
        tope_exento_general_uvt=P.TOPE_EXENTO_HERENCIA_GENERAL_UVT,
        tope_exento_vivienda_uvt=P.TOPE_EXENTO_HERENCIA_VIVIENDA_UVT,
    )
    assert resultado.porcion_exenta_pesos == pytest.approx(float(a_pesos(Decimal("1000"), P.UVT)))


def test_loteria_no_tiene_porcion_exenta():
    resultado = calcular_ganancia_ocasional_loteria(
        valor_premio_pesos=a_pesos(Decimal("1000"), P.UVT),
        tarifa_loterias=P.TARIFA_GANANCIA_OCASIONAL_LOTERIAS,
    )
    assert resultado.porcion_exenta_pesos == _CERO
    assert resultado.impuesto_pesos == pytest.approx(
        float(a_pesos(Decimal("1000"), P.UVT) * Decimal("0.20"))
    )