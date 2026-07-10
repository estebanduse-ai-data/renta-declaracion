from app.rules_engine.semilla_parametros import construir_payload_parametros_2025
from app.rules_engine import parametros_2025 as P


def test_payload_de_semilla_conserva_el_uvt():
    payload = construir_payload_parametros_2025()
    assert payload["uvt"] == P.UVT


def test_payload_de_semilla_conserva_el_anio():
    payload = construir_payload_parametros_2025()
    assert payload["anio_gravable"] == P.ANIO_GRAVABLE


def test_payload_de_semilla_convierte_la_tabla_de_tarifa_a_diccionarios():
    payload = construir_payload_parametros_2025()
    assert isinstance(payload["tabla_tarifa"], list)
    assert payload["tabla_tarifa"][0] == {
        "limite_inferior": 0,
        "limite_superior": 1090,
        "tarifa": 0.0,
        "base_uvt": 0,
    }


def test_payload_de_semilla_preserva_limite_superior_infinito_como_none():
    payload = construir_payload_parametros_2025()
    assert payload["tabla_tarifa"][-1]["limite_superior"] is None


def test_payload_de_semilla_incluye_los_factores_de_ajuste_art73():
    payload = construir_payload_parametros_2025()
    assert payload["factores_ajuste_art73_por_anio"][2025] == 1.000
