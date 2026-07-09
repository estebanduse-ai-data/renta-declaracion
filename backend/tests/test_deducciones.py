import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import a_pesos
from app.rules_engine.deducciones import (
    calcular_deduccion_intereses_vivienda,
    calcular_deduccion_salud,
    calcular_deduccion_dependientes,
)


def test_deduccion_intereses_vivienda_respeta_el_tope():
    resultado = calcular_deduccion_intereses_vivienda(
        intereses_pagados_anio_pesos=a_pesos(5_000, P.UVT),
        uvt=P.UVT,
        tope_uvt=P.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT,
    )
    assert resultado == pytest.approx(a_pesos(P.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT, P.UVT))


def test_deduccion_intereses_vivienda_bajo_el_tope_se_reconoce_completa():
    valor = a_pesos(500, P.UVT)
    resultado = calcular_deduccion_intereses_vivienda(
        intereses_pagados_anio_pesos=valor, uvt=P.UVT, tope_uvt=P.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT
    )
    assert resultado == pytest.approx(valor)


def test_deduccion_salud_aplica_tope_mensual_por_doce():
    resultado = calcular_deduccion_salud(
        pagos_salud_anio_pesos=a_pesos(1_000, P.UVT),
        uvt=P.UVT,
        tope_uvt_mensual=P.TOPE_DEDUCCION_SALUD_UVT_MENSUAL,
    )
    tope_anual_uvt = P.TOPE_DEDUCCION_SALUD_UVT_MENSUAL * 12
    assert resultado == pytest.approx(a_pesos(tope_anual_uvt, P.UVT))


def test_deduccion_dependientes_sin_dependientes_es_cero():
    resultado = calcular_deduccion_dependientes(
        ingreso_laboral_anio_pesos=a_pesos(10_000, P.UVT),
        numero_dependientes=0,
        uvt=P.UVT,
        porcentaje_ingreso=P.PORCENTAJE_DEDUCCION_DEPENDIENTES,
        tope_uvt_mensual=P.TOPE_DEDUCCION_DEPENDIENTES_UVT_MENSUAL,
        maximo_dependientes_reconocidos=P.MAXIMO_DEPENDIENTES_RECONOCIDOS,
    )
    assert resultado == 0


def test_deduccion_dependientes_respeta_el_tope_mensual_anualizado():
    resultado = calcular_deduccion_dependientes(
        ingreso_laboral_anio_pesos=a_pesos(100_000, P.UVT),  # ingreso muy alto
        numero_dependientes=2,
        uvt=P.UVT,
        porcentaje_ingreso=P.PORCENTAJE_DEDUCCION_DEPENDIENTES,
        tope_uvt_mensual=P.TOPE_DEDUCCION_DEPENDIENTES_UVT_MENSUAL,
        maximo_dependientes_reconocidos=P.MAXIMO_DEPENDIENTES_RECONOCIDOS,
    )
    tope_anual_uvt = P.TOPE_DEDUCCION_DEPENDIENTES_UVT_MENSUAL * 12
    assert resultado == pytest.approx(a_pesos(tope_anual_uvt, P.UVT))
