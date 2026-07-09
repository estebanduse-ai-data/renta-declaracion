import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import a_pesos
from app.rules_engine.deducciones import (
    calcular_deduccion_intereses_vivienda,
    calcular_deduccion_intereses_vivienda_icetex,
    calcular_deduccion_salud,
    calcular_deduccion_dependientes,
    calcular_exencion_cesantias,
    calcular_exencion_becas,
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


def test_intereses_vivienda_icetex_comparten_un_solo_tope():
    resultado = calcular_deduccion_intereses_vivienda_icetex(
        intereses_vivienda_pesos=a_pesos(800, P.UVT),
        intereses_icetex_pesos=a_pesos(800, P.UVT),
        uvt=P.UVT,
        tope_uvt=P.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT,
    )
    # 1.600 UVT combinados superan el tope de 1.200 UVT
    assert resultado == pytest.approx(a_pesos(P.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT, P.UVT))


def test_intereses_vivienda_icetex_bajo_el_tope_se_suman_completos():
    resultado = calcular_deduccion_intereses_vivienda_icetex(
        intereses_vivienda_pesos=a_pesos(300, P.UVT),
        intereses_icetex_pesos=a_pesos(200, P.UVT),
        uvt=P.UVT,
        tope_uvt=P.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT,
    )
    assert resultado == pytest.approx(a_pesos(500, P.UVT))


def test_cesantias_ingreso_bajo_es_100_por_ciento_exento():
    resultado = calcular_exencion_cesantias(
        valor_cesantias_e_intereses_pesos=a_pesos(1_000, P.UVT),
        promedio_mensual_ingresos_ultimos_6_meses_pesos=a_pesos(200, P.UVT),
        uvt=P.UVT,
        tabla_exencion_uvt_mensual=P.TABLA_EXENCION_CESANTIAS_UVT_MENSUAL,
    )
    assert resultado == pytest.approx(a_pesos(1_000, P.UVT))


def test_cesantias_ingreso_alto_no_tiene_exencion():
    resultado = calcular_exencion_cesantias(
        valor_cesantias_e_intereses_pesos=a_pesos(1_000, P.UVT),
        promedio_mensual_ingresos_ultimos_6_meses_pesos=a_pesos(700, P.UVT),
        uvt=P.UVT,
        tabla_exencion_uvt_mensual=P.TABLA_EXENCION_CESANTIAS_UVT_MENSUAL,
    )
    assert resultado == 0


def test_cesantias_ingreso_intermedio_aplica_porcentaje_parcial():
    resultado = calcular_exencion_cesantias(
        valor_cesantias_e_intereses_pesos=a_pesos(1_000, P.UVT),
        promedio_mensual_ingresos_ultimos_6_meses_pesos=a_pesos(450, P.UVT),  # tramo 80%
        uvt=P.UVT,
        tabla_exencion_uvt_mensual=P.TABLA_EXENCION_CESANTIAS_UVT_MENSUAL,
    )
    assert resultado == pytest.approx(a_pesos(1_000, P.UVT) * 0.80)


def test_beca_de_estudio_pura_es_totalmente_exenta():
    resultado = calcular_exencion_becas(
        valor_beca_pesos=5_000_000, es_contraprestacion_por_servicios=False
    )
    assert resultado == 5_000_000


def test_beca_que_es_contraprestacion_por_servicios_no_es_exenta():
    resultado = calcular_exencion_becas(
        valor_beca_pesos=5_000_000, es_contraprestacion_por_servicios=True
    )
    assert resultado == 0
