"""
Pruebas de `ParametrosTributariosPayload` — la validación que impide que un
error de digitación (UVT en cero, una tarifa de 150%, una tabla de tarifa
vacía) llegue a guardarse en base de datos y afecte el cálculo de los 200
declarantes de la cartera.

Requiere pydantic instalado; no se pudo ejecutar en el entorno de
desarrollo usado para este commit por falta de acceso a red — correrá en el
pipeline de CI de GitHub Actions.
"""

import pytest
from pydantic import ValidationError

from app.rules_engine.semilla_parametros import construir_payload_parametros_2025
from app.schemas.configuracion import ParametrosTributariosPayload


@pytest.fixture
def payload_valido() -> dict:
    return construir_payload_parametros_2025()


def test_payload_de_semilla_2025_es_valido(payload_valido):
    # Si esto falla, algo en parametros_2025.py o en el esquema se
    # desincronizó — debe arreglarse antes de sembrar producción.
    instancia = ParametrosTributariosPayload(**payload_valido)
    assert instancia.uvt == payload_valido["uvt"]


def test_uvt_en_cero_se_rechaza(payload_valido):
    payload_valido["uvt"] = 0
    with pytest.raises(ValidationError):
        ParametrosTributariosPayload(**payload_valido)


def test_uvt_negativa_se_rechaza(payload_valido):
    payload_valido["uvt"] = -1000
    with pytest.raises(ValidationError):
        ParametrosTributariosPayload(**payload_valido)


def test_tarifa_mayor_a_100_por_ciento_se_rechaza(payload_valido):
    payload_valido["tarifa_ganancia_ocasional_general"] = 1.5
    with pytest.raises(ValidationError):
        ParametrosTributariosPayload(**payload_valido)


def test_tabla_de_tarifa_vacia_se_rechaza(payload_valido):
    payload_valido["tabla_tarifa"] = []
    with pytest.raises(ValidationError):
        ParametrosTributariosPayload(**payload_valido)


def test_tramo_con_limite_superior_menor_al_inferior_se_rechaza(payload_valido):
    payload_valido["tabla_tarifa"][1]["limite_superior"] = payload_valido["tabla_tarifa"][1][
        "limite_inferior"
    ] - 1
    with pytest.raises(ValidationError):
        ParametrosTributariosPayload(**payload_valido)


def test_anio_gravable_fuera_de_rango_se_rechaza(payload_valido):
    payload_valido["anio_gravable"] = 1500
    with pytest.raises(ValidationError):
        ParametrosTributariosPayload(**payload_valido)


def test_maximo_dependientes_reconocidos_debe_ser_positivo(payload_valido):
    payload_valido["maximo_dependientes_reconocidos"] = 0
    with pytest.raises(ValidationError):
        ParametrosTributariosPayload(**payload_valido)
