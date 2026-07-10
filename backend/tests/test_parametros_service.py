"""
Pruebas del adaptador `ParametrosVigentes`. Verifican que, sin importar si
los valores vienen del módulo estático o de un `ParametroTributario.valores`
en base de datos, el motor de reglas recibe exactamente los mismos nombres
de atributo que usaba antes de existir este servicio — ver la explicación en
app/services/parametros_service.py.

Requiere sqlalchemy y pydantic instalados (ver requirements.txt); no se pudo
ejecutar en el entorno de desarrollo usado para este commit por falta de
acceso a red — correrá en el pipeline de CI de GitHub Actions.
"""

import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.semilla_parametros import construir_payload_parametros_2025
from app.services.parametros_service import ParametrosVigentes


@pytest.fixture
def parametros_desde_semilla() -> ParametrosVigentes:
    return ParametrosVigentes(construir_payload_parametros_2025())


def test_adaptador_conserva_el_uvt(parametros_desde_semilla):
    assert parametros_desde_semilla.UVT == P.UVT


def test_adaptador_reconstruye_la_tabla_de_tarifa_como_tuplas(parametros_desde_semilla):
    assert parametros_desde_semilla.TABLA_TARIFA_UVT == P.TABLA_TARIFA_UVT


def test_adaptador_reconstruye_tabla_de_dividendos(parametros_desde_semilla):
    assert parametros_desde_semilla.TABLA_TARIFA_DIVIDENDOS_UVT == P.TABLA_TARIFA_DIVIDENDOS_UVT


def test_adaptador_reconstruye_tabla_de_exencion_cesantias(parametros_desde_semilla):
    assert (
        parametros_desde_semilla.TABLA_EXENCION_CESANTIAS_UVT_MENSUAL
        == P.TABLA_EXENCION_CESANTIAS_UVT_MENSUAL
    )


def test_adaptador_reconstruye_factores_ajuste_art73_con_claves_enteras(parametros_desde_semilla):
    # El JSON de base de datos guarda las llaves del año como texto; el
    # adaptador debe volver a convertirlas a int para que
    # `costo_fiscal_ajustado()` las pueda usar con `.get(anio_adquisicion)`.
    assert parametros_desde_semilla.FACTORES_AJUSTE_ART73_POR_ANIO == P.FACTORES_AJUSTE_ART73_POR_ANIO
    for llave in parametros_desde_semilla.FACTORES_AJUSTE_ART73_POR_ANIO:
        assert isinstance(llave, int)


def test_adaptador_expone_todos_los_atributos_del_modulo_estatico(parametros_desde_semilla):
    # TASA_INTERES_MORA_DIARIA_REFERENCIAL se excluye a propósito: vive en la
    # tabla TasaInteresMora (cambia trimestralmente), no en
    # ParametroTributario (anual) — se resuelve aparte con
    # obtener_tasa_interes_mora_vigente(). Cualquier otro atributo del
    # módulo estático SÍ debe estar presente en el adaptador, o el motor de
    # reglas fallaría con un AttributeError en producción.
    excluidos_por_diseno = {"TASA_INTERES_MORA_DIARIA_REFERENCIAL"}
    atributos_modulo = [a for a in dir(P) if a.isupper()]
    faltantes = [
        a for a in atributos_modulo if not hasattr(parametros_desde_semilla, a) and a not in excluidos_por_diseno
    ]
    assert faltantes == []


def test_adaptador_es_compatible_con_el_motor_de_reglas_de_liquidacion(parametros_desde_semilla):
    from app.rules_engine.tarifa import liquidar

    resultado_con_adaptador = liquidar(
        total_ingresos_brutos_pesos=100_000_000,
        deducciones_imputables_pesos=0,
        ingreso_salarios_pesos=100_000_000,
        total_retenciones_pesos=0,
        patrimonio_liquido_anterior_pesos=0,
        uvt=parametros_desde_semilla.UVT,
        tabla_tarifa_uvt=parametros_desde_semilla.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=parametros_desde_semilla.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=parametros_desde_semilla.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=parametros_desde_semilla.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=parametros_desde_semilla.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=parametros_desde_semilla.TARIFA_RENTA_PRESUNTIVA,
    )

    resultado_con_modulo_estatico = liquidar(
        total_ingresos_brutos_pesos=100_000_000,
        deducciones_imputables_pesos=0,
        ingreso_salarios_pesos=100_000_000,
        total_retenciones_pesos=0,
        patrimonio_liquido_anterior_pesos=0,
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )

    assert resultado_con_adaptador.impuesto_a_cargo_pesos == pytest.approx(
        resultado_con_modulo_estatico.impuesto_a_cargo_pesos
    )
