"""
Descuentos tributarios (créditos directos contra el impuesto a cargo, no
deducciones de la base gravable) — art. 254 a 259 E.T.

Cambios en fix/decimal-float-type-errors
─────────────────────────────────────────
Migración de `float` a `Decimal` para alinear con el motor de reglas (DT-5).
"""

from dataclasses import dataclass
from decimal import Decimal

_CERO = Decimal("0")


def calcular_descuento_donaciones(
    *, valor_donado_pesos: Decimal, tarifa_descuento: Decimal
) -> Decimal:
    return max(valor_donado_pesos, _CERO) * tarifa_descuento


@dataclass
class ResultadoDescuentosTributarios:
    total_descuentos_solicitados_pesos: Decimal
    limite_aplicable_pesos: Decimal
    descuento_aplicado_pesos: Decimal
    impuesto_neto_pesos: Decimal
    descuento_no_utilizado_pesos: Decimal


def aplicar_limite_descuentos_tributarios(
    *,
    impuesto_basico_renta_pesos: Decimal,
    total_descuentos_pesos: Decimal,
    limite_porcentaje: Decimal,
) -> ResultadoDescuentosTributarios:
    """
    El artículo 259 E.T. limita la suma de todos los descuentos tributarios
    (donaciones, impuestos pagados en el exterior, inversión en proyectos de
    investigación, etc.) a un porcentaje del impuesto básico de renta —
    30% por defecto para el año gravable 2025.

    El exceso no utilizado en el año se pierde para efectos de este cálculo
    simplificado; algunos descuentos específicos permiten arrastre a años
    siguientes según su norma particular — no modelado todavía, ver
    docs/FALTANTES.md.
    """
    limite_pesos = max(impuesto_basico_renta_pesos, _CERO) * limite_porcentaje
    descuento_aplicado = min(max(total_descuentos_pesos, _CERO), limite_pesos)
    impuesto_neto = max(impuesto_basico_renta_pesos - descuento_aplicado, _CERO)
    no_utilizado = max(total_descuentos_pesos - descuento_aplicado, _CERO)

    return ResultadoDescuentosTributarios(
        total_descuentos_solicitados_pesos=total_descuentos_pesos,
        limite_aplicable_pesos=limite_pesos,
        descuento_aplicado_pesos=descuento_aplicado,
        impuesto_neto_pesos=impuesto_neto,
        descuento_no_utilizado_pesos=no_utilizado,
    )