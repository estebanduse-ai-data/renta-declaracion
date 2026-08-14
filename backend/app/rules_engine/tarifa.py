"""
Motor de reglas tributarias — funciones puras.

Cambios en DT-5
────────────────
Migración de `float` a `Decimal` en todos los cálculos monetarios y de UVT.

Por qué importa para una declaración de renta
───────────────────────────────────────────────
`float` en Python usa aritmética IEEE 754 de 64 bits. Eso significa que
0.1 + 0.2 ≠ 0.3 en términos de representación binaria. Para valores
cotidianos de patrimonio (ej. $450.000.000 COP), el error acumulado en
una cadena de 6-8 operaciones puede ser de $10–$100 pesos — invisible al
ojo, pero técnicamente incorrecto si la DIAN compara el resultado con su
propio cálculo.

Antes de DT-5: el motor calculaba en `float`; `_redondear()` en
`liquidacion_service.py` convertía a `Decimal` al final. El error IEEE 754
se acumulaba durante los cálculos intermedios (renta exenta, límite 40%,
renta presuntiva) aunque el resultado final se redondeara.

Después de DT-5: todos los valores en pesos y en UVT son `Decimal` dentro
del motor. Los coeficientes normativos (tarifas, porcentajes) también son
`Decimal`, definidos como tales en `parametros_2025.py`.

Impacto en código que llama al motor
──────────────────────────────────────
`liquidacion_service.py` ya no necesita convertir los inputs a `float`:
los pasa directamente como `Decimal`. La función `_redondear()` del service
sigue siendo necesaria para redondear al peso antes de serializar, pero
ya no es la única defensa contra el error de representación.

Reglas de diseño que NO cambian
─────────────────────────────────
  1. Ninguna función accede a BD, red ni framework web.
  2. Ninguna función recibe sesión de usuario ni request HTTP.
  3. Todos los parámetros normativos se reciben como argumento.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# Cuantía mínima para redondeo interno (1 peso colombiano).
# Se usa en funciones que deben devolver valores enteros de pesos,
# NO en cálculos intermedios (donde queremos mantener la precisión completa).
_COP = Decimal("1")
_CERO = Decimal("0")


# ── Conversiones UVT ─────────────────────────────────────────────────────────

def a_uvt(pesos: Decimal, uvt: Decimal) -> Decimal:
    """Convierte pesos a UVT con precisión decimal completa."""
    return pesos / uvt


def a_pesos(valor_uvt: Decimal, uvt: Decimal) -> Decimal:
    """Convierte UVT a pesos con precisión decimal completa."""
    return valor_uvt * uvt


# ── Tabla progresiva del impuesto ─────────────────────────────────────────────

def calcular_impuesto_uvt(base_uvt: Decimal, tabla_tarifa_uvt: list) -> Decimal:
    """
    Aplica la tabla progresiva del artículo 241 E.T.

    tabla_tarifa_uvt: lista de tuplas
        (limite_inferior: Decimal, limite_superior: Decimal | None,
         tarifa: Decimal, base_uvt: Decimal)

    Todos los valores de la tabla deben ser Decimal (definidos así en
    parametros_2025.py). La función no convierte — si se pasan float
    se pierde la garantía de precisión.

    Devuelve el impuesto en UVT (Decimal, sin redondear al peso).
    El redondeo a pesos ocurre en liquidacion_service._redondear().
    """
    if base_uvt <= _CERO:
        return _CERO

    for limite_inferior, limite_superior, tarifa, base in tabla_tarifa_uvt:
        dentro_del_tramo = base_uvt > limite_inferior and (
            limite_superior is None or base_uvt <= limite_superior
        )
        if dentro_del_tramo:
            return base + (base_uvt - limite_inferior) * tarifa

    # Salvaguarda: si la base supera todos los tramos (tabla mal formada),
    # aplicar el último tramo. Con una tabla bien formada (último limite_superior=None)
    # nunca se llega aquí.
    limite_inferior, _, tarifa, base = tabla_tarifa_uvt[-1]
    return base + (base_uvt - limite_inferior) * tarifa


# ── Renta exenta laboral ──────────────────────────────────────────────────────

def calcular_renta_exenta_laboral(
    ingreso_salarios_pesos: Decimal,
    uvt: Decimal,
    porcentaje: Decimal,
    tope_uvt: Decimal,
) -> Decimal:
    """
    Renta exenta del 25% sobre pagos laborales (art. 206 num. 10 E.T.),
    limitada a 790 UVT anuales para 2025.
    """
    base = ingreso_salarios_pesos * porcentaje
    tope_pesos = a_pesos(tope_uvt, uvt)
    return min(base, tope_pesos)


# ── Límite del 40% de exenciones y deducciones ───────────────────────────────

def calcular_limite_exenciones_cedula_general(
    total_ingresos_brutos_pesos: Decimal,
    uvt: Decimal,
    porcentaje_limite: Decimal,
    tope_uvt: Decimal,
) -> Decimal:
    """
    Límite conjunto de rentas exentas y deducciones de la cédula general
    (art. 336 E.T.): el menor entre el 40% del ingreso bruto cedular
    y 1.340 UVT anuales para 2025.
    """
    tope_pesos = a_pesos(tope_uvt, uvt)
    limite_porcentual = total_ingresos_brutos_pesos * porcentaje_limite
    return min(tope_pesos, limite_porcentual)


# ── Dataclass de resultado ────────────────────────────────────────────────────

@dataclass
class ResultadoLiquidacion:
    renta_liquida_gravable_pesos: Decimal
    impuesto_uvt:                 Decimal
    impuesto_a_cargo_pesos:       Decimal
    total_retenciones_pesos:      Decimal
    saldo_pesos:                  Decimal   # positivo = a pagar, negativo = a favor

    @property
    def es_saldo_a_pagar(self) -> bool:
        return self.saldo_pesos >= _CERO


# ── Función principal de liquidación ─────────────────────────────────────────

def liquidar(
    *,
    total_ingresos_brutos_pesos:      Decimal,
    deducciones_imputables_pesos:     Decimal,
    ingreso_salarios_pesos:           Decimal,
    total_retenciones_pesos:          Decimal,
    patrimonio_liquido_anterior_pesos: Decimal,
    uvt:                              Decimal,
    tabla_tarifa_uvt:                 list,
    porcentaje_renta_exenta_laboral:  Decimal,
    tope_renta_exenta_laboral_uvt:    Decimal,
    porcentaje_limite_exenciones:     Decimal,
    tope_limite_exenciones_uvt:       Decimal,
    tarifa_renta_presuntiva:          Decimal,
) -> ResultadoLiquidacion:
    """
    Orquesta el cálculo completo de la liquidación privada.

    Todos los parámetros deben ser Decimal. El motor no convierte float
    a Decimal internamente — esa conversión debe ocurrir antes de llamar
    a esta función (en liquidacion_service.calcular_y_persistir).

    Devuelve ResultadoLiquidacion con todos los campos en Decimal.
    El redondeo al peso ocurre en liquidacion_service._redondear().
    """
    # 1. Renta exenta laboral (25% pagos laborales, tope 790 UVT)
    renta_exenta_laboral = calcular_renta_exenta_laboral(
        ingreso_salarios_pesos,
        uvt,
        porcentaje_renta_exenta_laboral,
        tope_renta_exenta_laboral_uvt,
    )

    # 2. Límite del 40% de exenciones y deducciones (art. 336 E.T.)
    limite_exenciones = calcular_limite_exenciones_cedula_general(
        total_ingresos_brutos_pesos,
        uvt,
        porcentaje_limite_exenciones,
        tope_limite_exenciones_uvt,
    )

    # 3. Total de exenciones y deducciones efectivamente aplicadas
    exenciones_aplicadas = min(
        deducciones_imputables_pesos + renta_exenta_laboral,
        limite_exenciones,
    )

    # 4. Renta líquida de la cédula general
    renta_liquida_cedular = max(
        total_ingresos_brutos_pesos - exenciones_aplicadas,
        _CERO,
    )

    # 5. Renta presuntiva (0% para 2025 — Ley 2277 de 2022)
    renta_presuntiva_pesos = max(patrimonio_liquido_anterior_pesos, _CERO) * tarifa_renta_presuntiva

    # 6. Renta líquida gravable: la mayor entre la cedular y la presuntiva
    renta_liquida_gravable = max(renta_liquida_cedular, renta_presuntiva_pesos)

    # 7. Impuesto según tabla progresiva (en UVT primero, luego en pesos)
    impuesto_uvt = calcular_impuesto_uvt(
        a_uvt(renta_liquida_gravable, uvt),
        tabla_tarifa_uvt,
    )
    impuesto_a_cargo = a_pesos(impuesto_uvt, uvt)

    # 8. Saldo a pagar o a favor
    saldo = impuesto_a_cargo - total_retenciones_pesos

    return ResultadoLiquidacion(
        renta_liquida_gravable_pesos=renta_liquida_gravable,
        impuesto_uvt=impuesto_uvt,
        impuesto_a_cargo_pesos=impuesto_a_cargo,
        total_retenciones_pesos=total_retenciones_pesos,
        saldo_pesos=saldo,
    )