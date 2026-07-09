import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import a_pesos
from app.rules_engine.sanciones import (
    meses_o_fraccion_de_atraso,
    calcular_sancion_extemporaneidad,
    calcular_sancion_correccion,
    calcular_interes_mora,
)


def test_meses_o_fraccion_redondea_hacia_arriba():
    assert meses_o_fraccion_de_atraso(0) == 0
    assert meses_o_fraccion_de_atraso(1) == 1
    assert meses_o_fraccion_de_atraso(30) == 1
    assert meses_o_fraccion_de_atraso(31) == 2
    assert meses_o_fraccion_de_atraso(60) == 2


def test_sancion_extemporaneidad_sin_atraso_es_cero():
    sancion = calcular_sancion_extemporaneidad(
        impuesto_a_cargo_pesos=10_000_000,
        ingresos_brutos_pesos=50_000_000,
        dias_atraso=0,
        uvt=P.UVT,
        porcentaje_mensual_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL,
        tope_porcentaje_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO,
        porcentaje_mensual_sobre_ingresos=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS,
        sancion_minima_uvt=P.SANCION_MINIMA_UVT,
    )
    assert sancion == 0


def test_sancion_extemporaneidad_dos_meses_con_impuesto_a_cargo():
    sancion = calcular_sancion_extemporaneidad(
        impuesto_a_cargo_pesos=10_000_000,
        ingresos_brutos_pesos=50_000_000,
        dias_atraso=45,  # 2 meses o fracción
        uvt=P.UVT,
        porcentaje_mensual_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL,
        tope_porcentaje_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO,
        porcentaje_mensual_sobre_ingresos=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS,
        sancion_minima_uvt=P.SANCION_MINIMA_UVT,
    )
    assert sancion == pytest.approx(10_000_000 * 0.05 * 2)


def test_sancion_extemporaneidad_respeta_el_tope_del_100_por_ciento():
    sancion = calcular_sancion_extemporaneidad(
        impuesto_a_cargo_pesos=10_000_000,
        ingresos_brutos_pesos=50_000_000,
        dias_atraso=900,  # 30 meses -> 150% sin tope
        uvt=P.UVT,
        porcentaje_mensual_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL,
        tope_porcentaje_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO,
        porcentaje_mensual_sobre_ingresos=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS,
        sancion_minima_uvt=P.SANCION_MINIMA_UVT,
    )
    assert sancion == pytest.approx(10_000_000 * 1.00)


def test_sancion_extemporaneidad_sin_impuesto_usa_ingresos_brutos():
    # Ingresos brutos altos para que el cálculo sobre ingresos supere la
    # sanción mínima y así se pueda verificar la fórmula, no el piso.
    sancion = calcular_sancion_extemporaneidad(
        impuesto_a_cargo_pesos=0,
        ingresos_brutos_pesos=500_000_000,
        dias_atraso=30,
        uvt=P.UVT,
        porcentaje_mensual_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL,
        tope_porcentaje_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO,
        porcentaje_mensual_sobre_ingresos=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS,
        sancion_minima_uvt=P.SANCION_MINIMA_UVT,
    )
    assert sancion == pytest.approx(500_000_000 * 0.005 * 1)


def test_sancion_extemporaneidad_con_ingresos_bajos_no_baja_del_piso_minimo():
    sancion = calcular_sancion_extemporaneidad(
        impuesto_a_cargo_pesos=0,
        ingresos_brutos_pesos=1_000_000,  # cálculo sobre ingresos quedaría bajo el mínimo
        dias_atraso=30,
        uvt=P.UVT,
        porcentaje_mensual_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL,
        tope_porcentaje_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO,
        porcentaje_mensual_sobre_ingresos=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS,
        sancion_minima_uvt=P.SANCION_MINIMA_UVT,
    )
    assert sancion == pytest.approx(a_pesos(P.SANCION_MINIMA_UVT, P.UVT))


def test_sancion_nunca_baja_de_la_sancion_minima():
    sancion = calcular_sancion_extemporaneidad(
        impuesto_a_cargo_pesos=1_000,  # impuesto irrisorio
        ingresos_brutos_pesos=0,
        dias_atraso=1,
        uvt=P.UVT,
        porcentaje_mensual_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL,
        tope_porcentaje_sobre_impuesto=P.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO,
        porcentaje_mensual_sobre_ingresos=P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS,
        sancion_minima_uvt=P.SANCION_MINIMA_UVT,
    )
    assert sancion == pytest.approx(a_pesos(P.SANCION_MINIMA_UVT, P.UVT))


def test_sancion_correccion_antes_de_emplazamiento():
    sancion = calcular_sancion_correccion(
        mayor_valor_a_pagar_pesos=1_000_000,
        despues_de_emplazamiento=False,
        porcentaje_antes=P.SANCION_CORRECCION_ANTES_EMPLAZAMIENTO_PORCENTAJE,
        porcentaje_despues=P.SANCION_CORRECCION_DESPUES_EMPLAZAMIENTO_PORCENTAJE,
    )
    assert sancion == 100_000


def test_sancion_correccion_despues_de_emplazamiento_es_el_doble():
    sancion = calcular_sancion_correccion(
        mayor_valor_a_pagar_pesos=1_000_000,
        despues_de_emplazamiento=True,
        porcentaje_antes=P.SANCION_CORRECCION_ANTES_EMPLAZAMIENTO_PORCENTAJE,
        porcentaje_despues=P.SANCION_CORRECCION_DESPUES_EMPLAZAMIENTO_PORCENTAJE,
    )
    assert sancion == 200_000


def test_interes_mora_sin_dias_de_atraso_es_cero():
    resultado = calcular_interes_mora(
        valor_adeudado_pesos=1_000_000, dias_mora=0, tasa_diaria=P.TASA_INTERES_MORA_DIARIA_REFERENCIAL
    )
    assert resultado.interes_pesos == 0


def test_interes_mora_crece_linealmente_con_los_dias():
    resultado_10 = calcular_interes_mora(
        valor_adeudado_pesos=1_000_000, dias_mora=10, tasa_diaria=P.TASA_INTERES_MORA_DIARIA_REFERENCIAL
    )
    resultado_20 = calcular_interes_mora(
        valor_adeudado_pesos=1_000_000, dias_mora=20, tasa_diaria=P.TASA_INTERES_MORA_DIARIA_REFERENCIAL
    )
    assert resultado_20.interes_pesos == pytest.approx(resultado_10.interes_pesos * 2)
