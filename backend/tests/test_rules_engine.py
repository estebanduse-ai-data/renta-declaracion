"""
Pruebas del motor de reglas tributarias — versión Decimal (DT-5).

Cambios respecto a la versión float
─────────────────────────────────────
• Los inputs ahora son `Decimal`, igual que los parámetros en `parametros_2025.py`.
• Las comparaciones usan `==` exacto en lugar de `pytest.approx` donde el
  resultado es determinista (ej. impuesto en tramo 0%, valor cero).
• Para tests de liquidación completa que verifican pesos, se aplica
  `_redondear()` en ambos lados: el motor devuelve Decimal con precisión
  completa; el redondeo al peso es responsabilidad de liquidacion_service.
  Comparar antes de redondear fallaría porque 77.9 * 49799 = 3.879.342.1
  (Decimal) ≠ 3.879.342 (int). Los tests reflejan el contrato real.
• Se agregan tres casos nuevos que con `float` podían enmascarar errores
  de representación pero con `Decimal` son exactos.

Estas pruebas son la primera línea de defensa contra el riesgo #1 de
docs/RIESGOS.md. Deben ampliarse con casos reales del Excel del contador
durante la fase de pruebas de paridad (ver docs/PLAN_DE_TRABAJO.md).
"""

from decimal import Decimal

import pytest

from app.rules_engine import parametros_2025 as P
from app.rules_engine.tarifa import (
    ResultadoLiquidacion,
    a_pesos,
    a_uvt,
    calcular_impuesto_uvt,
    calcular_limite_exenciones_cedula_general,
    calcular_renta_exenta_laboral,
    liquidar,
)
from app.services.liquidacion_service import _redondear


# ── Helpers ───────────────────────────────────────────────────────────────────

def d(value: str | int) -> Decimal:
    """Atajo para construir Decimal desde string o int."""
    return Decimal(str(value))


def _liquidar(**overrides) -> ResultadoLiquidacion:
    """
    Llama a liquidar() con los parámetros 2025 y los overrides indicados.
    Reduce el boilerplate de los tests de liquidación completa.
    """
    defaults = dict(
        total_ingresos_brutos_pesos=d(0),
        deducciones_imputables_pesos=d(0),
        ingreso_salarios_pesos=d(0),
        total_retenciones_pesos=d(0),
        patrimonio_liquido_anterior_pesos=d(0),
        uvt=P.UVT,
        tabla_tarifa_uvt=P.TABLA_TARIFA_UVT,
        porcentaje_renta_exenta_laboral=P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        tope_renta_exenta_laboral_uvt=P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        porcentaje_limite_exenciones=P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        tope_limite_exenciones_uvt=P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        tarifa_renta_presuntiva=P.TARIFA_RENTA_PRESUNTIVA,
    )
    defaults.update(overrides)
    return liquidar(**defaults)


# ── Conversiones UVT ──────────────────────────────────────────────────────────

def test_conversion_uvt_pesos_es_reversible():
    """La conversión pesos→UVT→pesos debe ser exacta con Decimal."""
    valor_uvt = d(1000)
    pesos = a_pesos(valor_uvt, P.UVT)
    assert a_uvt(pesos, P.UVT) == valor_uvt


def test_conversion_uvt_pesos_valores_grandes():
    """
    Con float, 450_000_000 / 49799 * 49799 no era exactamente 450_000_000
    debido a error IEEE 754. Con Decimal debe ser exacto.
    """
    pesos_originales = d(450_000_000)
    uvt = a_uvt(pesos_originales, P.UVT)
    pesos_recuperados = a_pesos(uvt, P.UVT)
    assert pesos_recuperados == pesos_originales


# ── Tabla progresiva ──────────────────────────────────────────────────────────

def test_impuesto_es_cero_bajo_el_primer_tramo():
    assert calcular_impuesto_uvt(d(500), P.TABLA_TARIFA_UVT) == d(0)
    assert calcular_impuesto_uvt(d(1090), P.TABLA_TARIFA_UVT) == d(0)


def test_impuesto_justo_en_el_limite_del_primer_tramo_gravable():
    """1090.01 UVT debe tributar exactamente 0.01 * 0.19 = 0.0019 UVT."""
    resultado = calcular_impuesto_uvt(d("1090.01"), P.TABLA_TARIFA_UVT)
    esperado = d("0.01") * d("0.19")
    assert resultado == esperado


def test_impuesto_tramo_mas_alto_usa_base_acumulada():
    """35.000 UVT → tramo 39%, base acumulada 11.352 UVT."""
    resultado = calcular_impuesto_uvt(d(35_000), P.TABLA_TARIFA_UVT)
    esperado = d(11_352) + (d(35_000) - d(31_000)) * d("0.39")
    assert resultado == esperado


def test_impuesto_negativo_devuelve_cero():
    assert calcular_impuesto_uvt(d(-100), P.TABLA_TARIFA_UVT) == d(0)


def test_impuesto_exactamente_en_limite_superior_de_tramo():
    """
    1.700 UVT está en el límite superior del segundo tramo (1090-1700 al 19%).
    Debe usar ese tramo, no el siguiente (28%).
    """
    resultado = calcular_impuesto_uvt(d(1700), P.TABLA_TARIFA_UVT)
    esperado = d(0) + (d(1700) - d(1090)) * d("0.19")
    assert resultado == esperado


def test_impuesto_justo_despues_del_limite_superior_de_tramo():
    """
    1.700.01 UVT entra al tercer tramo (28%, base 116 UVT).
    """
    resultado = calcular_impuesto_uvt(d("1700.01"), P.TABLA_TARIFA_UVT)
    esperado = d(116) + (d("1700.01") - d(1700)) * d("0.28")
    assert resultado == esperado


# ── Renta exenta laboral ──────────────────────────────────────────────────────

def test_renta_exenta_laboral_respeta_el_tope():
    """Ingreso muy alto → la exenta queda exactamente en el tope de 790 UVT."""
    ingreso_alto = a_pesos(d(10_000), P.UVT)
    exenta = calcular_renta_exenta_laboral(
        ingreso_alto,
        P.UVT,
        P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        P.TOPE_RENTA_EXENTA_LABORAL_UVT,
    )
    assert exenta == a_pesos(P.TOPE_RENTA_EXENTA_LABORAL_UVT, P.UVT)


def test_renta_exenta_laboral_por_debajo_del_tope():
    """Ingreso pequeño → la exenta es el 25% exacto del ingreso."""
    ingreso = a_pesos(d(100), P.UVT)   # 100 UVT → muy por debajo del tope
    exenta = calcular_renta_exenta_laboral(
        ingreso,
        P.UVT,
        P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        P.TOPE_RENTA_EXENTA_LABORAL_UVT,
    )
    assert exenta == ingreso * d("0.25")


# ── Límite del 40% ────────────────────────────────────────────────────────────

def test_limite_exenciones_respeta_tope_uvt():
    """Ingreso muy alto → el límite queda en 1.340 UVT exactos."""
    ingreso_alto = a_pesos(d(100_000), P.UVT)
    limite = calcular_limite_exenciones_cedula_general(
        ingreso_alto,
        P.UVT,
        P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
    )
    assert limite == a_pesos(P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT, P.UVT)


def test_limite_exenciones_porcentual_cuando_es_menor_al_tope():
    """Ingreso bajo → el límite es el 40% del ingreso, no el tope en UVT."""
    ingreso = a_pesos(d(10), P.UVT)    # 10 UVT → 40% = 4 UVT, muy por debajo de 1340
    limite = calcular_limite_exenciones_cedula_general(
        ingreso,
        P.UVT,
        P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
    )
    assert limite == ingreso * d("0.40")


# ── Liquidación completa ──────────────────────────────────────────────────────

def test_liquidar_sin_ingresos_no_genera_impuesto():
    resultado = _liquidar()
    assert resultado.impuesto_a_cargo_pesos == d(0)
    assert resultado.saldo_pesos == d(0)


def test_liquidar_con_retenciones_mayores_al_impuesto_da_saldo_a_favor():
    resultado = _liquidar(
        total_ingresos_brutos_pesos=a_pesos(d(500), P.UVT),
        ingreso_salarios_pesos=a_pesos(d(500), P.UVT),
        total_retenciones_pesos=a_pesos(d(10), P.UVT),
    )
    assert not resultado.es_saldo_a_pagar
    assert resultado.saldo_pesos < d(0)


def test_renta_presuntiva_cero_en_2025_no_incrementa_base():
    """Con tarifa 0%, un patrimonio alto no debe forzar renta gravable."""
    resultado = _liquidar(
        patrimonio_liquido_anterior_pesos=a_pesos(d(50_000), P.UVT),
    )
    assert resultado.renta_liquida_gravable_pesos == d(0)


def test_liquidar_caso_tipico_asalariado():
    """
    Declarante asalariado típico:
      Ingresos brutos: 2.000 UVT (~$99.598.000)
      Retenciones:       100 UVT

    Pasos manuales:
      Renta exenta laboral = min(2000 * 0.25, 790) = 500 UVT
      Límite 40%           = min(2000 * 0.40, 1340) = 800 UVT
      Exenciones aplicadas = min(0 + 500, 800) = 500 UVT
      Renta liq cedular    = 2000 - 500 = 1500 UVT
      Renta liq gravable   = max(1500, 0) = 1500 UVT
      Impuesto (tramo 19%) = 0 + (1500 - 1090) * 0.19 = 77.9 UVT
      Impuesto en pesos    = 77.9 * 49799 = 3.879.342.1 → 3.879.342 (redondeado)
      Saldo                = 3.879.342 - (100 * 49799) = 3.879.342 - 4.979.900 = -1.100.558

    Nota sobre redondeo
    ────────────────────
    El motor devuelve Decimal con precisión completa (3.879.342.1...).
    El redondeo al peso lo aplica liquidacion_service._redondear() antes
    de serializar. Los tests comparan con _redondear() aplicado en ambos
    lados para reflejar ese contrato.
    """
    uvt = P.UVT
    ingresos    = a_pesos(d(2000), uvt)
    retenciones = a_pesos(d(100), uvt)

    resultado = _liquidar(
        total_ingresos_brutos_pesos=ingresos,
        ingreso_salarios_pesos=ingresos,
        total_retenciones_pesos=retenciones,
    )

    # Verificar que el impuesto es positivo y hay saldo a favor
    assert resultado.impuesto_a_cargo_pesos > d(0)
    assert not resultado.es_saldo_a_pagar   # retenciones superan el impuesto

    # Verificar el cálculo exacto del impuesto redondeado al peso
    # El motor devuelve 77.9 UVT * 49799 = 3.879.342.1 (Decimal sin redondear)
    # _redondear() lo lleva a 3.879.342
    impuesto_uvt_esperado   = d("77.9")
    impuesto_pesos_esperado = _redondear(impuesto_uvt_esperado * uvt)
    assert _redondear(resultado.impuesto_a_cargo_pesos) == impuesto_pesos_esperado


def test_liquidar_precision_decimal_vs_float():
    """
    Verifica que el resultado Decimal es exactamente reproducible para
    valores que con float IEEE 754 producirían error de representación.

    Con float: impuesto_a_cargo podía diferir en $1-$100 pesos vs. el
              cálculo manual, dependiendo del orden de las operaciones.
    Con Decimal: el motor y el cálculo manual producen exactamente el
              mismo valor antes del redondeo, y el mismo peso tras él.

    Nota sobre redondeo
    ────────────────────
    El motor devuelve Decimal sin redondear al peso. El contrato que
    probamos es: _redondear(motor) == _redondear(cálculo_manual).
    Ambos lados aplican _redondear() para que la comparación sea sobre
    el mismo nivel de precisión que el service entrega a la API.
    """
    uvt = P.UVT
    # $87.500.000 no es múltiplo exacto de UVT (49799) — produce periódico
    ingresos = d("87500000")

    resultado = _liquidar(
        total_ingresos_brutos_pesos=ingresos,
        ingreso_salarios_pesos=ingresos,
    )

    # Cálculo manual con Decimal — misma aritmética que el motor
    renta_exenta          = min(ingresos * d("0.25"), a_pesos(d(790), uvt))
    limite_40             = min(ingresos * d("0.40"), a_pesos(d(1340), uvt))
    exenciones            = min(renta_exenta, limite_40)
    renta_liq             = ingresos - exenciones
    base_uvt              = renta_liq / uvt
    impuesto_uvt_manual   = (base_uvt - d(1090)) * d("0.19")
    impuesto_pesos_manual = impuesto_uvt_manual * uvt

    # Comparar con redondeo aplicado en ambos lados
    assert _redondear(resultado.impuesto_a_cargo_pesos) == _redondear(impuesto_pesos_manual)