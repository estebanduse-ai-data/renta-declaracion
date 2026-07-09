"""
Descuentos tributarios (créditos directos contra el impuesto a cargo, no
deducciones de la base gravable) — art. 254 a 259 E.T.
"""

from dataclasses import dataclass


def calcular_descuento_donaciones(
    *, valor_donado_pesos: float, tarifa_descuento: float
) -> float:
    return max(valor_donado_pesos, 0.0) * tarifa_descuento


@dataclass
class ResultadoDescuentosTributarios:
    total_descuentos_solicitados_pesos: float
    limite_aplicable_pesos: float
    descuento_aplicado_pesos: float
    impuesto_neto_pesos: float
    descuento_no_utilizado_pesos: float


def aplicar_limite_descuentos_tributarios(
    *,
    impuesto_basico_renta_pesos: float,
    total_descuentos_pesos: float,
    limite_porcentaje: float,
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
    limite_pesos = max(impuesto_basico_renta_pesos, 0.0) * limite_porcentaje
    descuento_aplicado = min(max(total_descuentos_pesos, 0.0), limite_pesos)
    impuesto_neto = max(impuesto_basico_renta_pesos - descuento_aplicado, 0.0)
    no_utilizado = max(total_descuentos_pesos - descuento_aplicado, 0.0)

    return ResultadoDescuentosTributarios(
        total_descuentos_solicitados_pesos=total_descuentos_pesos,
        limite_aplicable_pesos=limite_pesos,
        descuento_aplicado_pesos=descuento_aplicado,
        impuesto_neto_pesos=impuesto_neto,
        descuento_no_utilizado_pesos=no_utilizado,
    )
