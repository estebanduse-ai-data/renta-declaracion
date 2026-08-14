"""
Parámetros tributarios — Año gravable 2025.

Cambios en DT-5
────────────────
Todos los valores numéricos que entran al motor de reglas como parámetros
de cálculo (UVT, tarifas, porcentajes, topes) son ahora `Decimal`.

Por qué Decimal y no float aquí
─────────────────────────────────
Los valores de este módulo son los operandos directos del motor de reglas
(`tarifa.py`, `deducciones.py`). Si se definen como `float`, la aritmética
dentro del motor sigue siendo IEEE 754 aunque el motor use `Decimal` — un
`Decimal * float` en Python produce `TypeError`, pero `Decimal(float)` es
inexacto (ej. `Decimal(0.19)` → `Decimal('0.18999999999999...')`).

La forma correcta es `Decimal("0.19")` — construido desde string, que
representa exactamente `19/100`.

Qué se deja como int/float
───────────────────────────
• Los valores que son puramente informativos y no entran al motor
  (LIMITE_ANIOS_COMPENSACION_PERDIDAS, FACTORES_AJUSTE_ART73_POR_ANIO,
  los comentarios de referencia legal) se dejan como `float` o `int`
  porque no participan en cálculos de Decimal.
• Las claves de diccionario (años en FACTORES_AJUSTE) siguen siendo `int`.

Invariante de este módulo
──────────────────────────
Este módulo NO contiene lógica de cálculo, solo datos. Cada año gravable
nuevo debe crear un archivo `parametros_<anio>.py` propio para conservar
el histórico y permitir recalcular declaraciones pasadas con sus parámetros
originales.

Fuente de referencia obligatoria: resolución vigente de la DIAN para el
año gravable. Los valores aquí son referenciales y deben confirmarse antes
de un despliegue a producción.
"""

from decimal import Decimal

ANIO_GRAVABLE = 2025

# Valor de la Unidad de Valor Tributario (UVT) para el año gravable.
UVT = Decimal("49799")

# Tabla progresiva del impuesto de renta — cédula general (artículo 241 E.T.).
# Cada tramo: (limite_inferior_uvt, limite_superior_uvt, tarifa_marginal, impuesto_base_uvt)
# None en limite_superior = sin límite superior (último tramo).
# Todos los valores son Decimal para que calcular_impuesto_uvt() opere en Decimal puro.
TABLA_TARIFA_UVT = [
    (Decimal("0"),      Decimal("1090"),  Decimal("0.00"), Decimal("0")),
    (Decimal("1090"),   Decimal("1700"),  Decimal("0.19"), Decimal("0")),
    (Decimal("1700"),   Decimal("4100"),  Decimal("0.28"), Decimal("116")),
    (Decimal("4100"),   Decimal("8670"),  Decimal("0.33"), Decimal("788")),
    (Decimal("8670"),   Decimal("18970"), Decimal("0.35"), Decimal("2296")),
    (Decimal("18970"),  Decimal("31000"), Decimal("0.37"), Decimal("6901")),
    (Decimal("31000"),  None,             Decimal("0.39"), Decimal("11352")),
]

# Límite de rentas exentas y deducciones de la cédula general (artículo 336 E.T.).
LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE = Decimal("0.40")
TOPE_RENTA_EXENTA_DEDUCCIONES_UVT          = Decimal("1340")

# Renta exenta laboral — 25% de pagos laborales (artículo 206 numeral 10 E.T.).
PORCENTAJE_RENTA_EXENTA_LABORAL   = Decimal("0.25")
TOPE_RENTA_EXENTA_LABORAL_UVT     = Decimal("790")

# Tarifa de renta presuntiva (Ley 2277 de 2022 la fijó en 0% desde año gravable 2022).
TARIFA_RENTA_PRESUNTIVA = Decimal("0.00")

# Exclusiones de la base de renta presuntiva, en UVT (art. 189 E.T.).
TOPE_VIVIENDA_HABITACION_UVT          = Decimal("8000")
TOPE_ACTIVOS_SECTOR_AGROPECUARIO_UVT  = Decimal("19000")

# Límite de descuentos tributarios (artículos 255, 256, 257, 257-1 E.T.)
# sobre el impuesto básico de renta.
LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE = Decimal("0.30")

# Umbral de saldo a pagar que obliga a cancelar en una sola cuota (en UVT).
TOPE_PAGO_UNICA_CUOTA_UVT = Decimal("41")

# ── Ganancias ocasionales (artículos 299 a 317 E.T.) ─────────────────────────

TARIFA_GANANCIA_OCASIONAL_GENERAL  = Decimal("0.15")
TARIFA_GANANCIA_OCASIONAL_LOTERIAS = Decimal("0.20")

TOPE_EXENTO_VENTA_CASA_HABITACION_UVT = Decimal("5000")

PORCENTAJE_EXENTO_HERENCIA_GENERAL    = Decimal("0.20")
TOPE_EXENTO_HERENCIA_GENERAL_UVT      = Decimal("1625")
TOPE_EXENTO_HERENCIA_VIVIENDA_UVT     = Decimal("3250")

TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO = Decimal("0.03")

# Factores de ajuste fiscal art. 73 E.T. — informativos, no entran al motor de reglas.
# Se dejan como float porque no participan en cálculos de Decimal.
FACTORES_AJUSTE_ART73_POR_ANIO = {
    2015: 1.727, 2016: 1.629, 2017: 1.550, 2018: 1.500,
    2019: 1.452, 2020: 1.412, 2021: 1.376, 2022: 1.246,
    2023: 1.147, 2024: 1.063, 2025: 1.000,
}

# ── Cédula de dividendos (art. 242 E.T., modificado por Ley 2277/2022) ───────

TABLA_TARIFA_DIVIDENDOS_UVT = [
    (Decimal("0"),    Decimal("1090"), Decimal("0.00"), Decimal("0")),
    (Decimal("1090"), None,            Decimal("0.15"), Decimal("0")),
]

TARIFA_DIVIDENDOS_NO_GRAVADOS_SOCIEDAD = Decimal("0.35")

# ── Deducciones con tope (cédula general) ─────────────────────────────────────

TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT  = Decimal("1200")
TOPE_DEDUCCION_SALUD_UVT_MENSUAL       = Decimal("16")

PORCENTAJE_DEDUCCION_DEPENDIENTES         = Decimal("0.10")
TOPE_DEDUCCION_DEPENDIENTES_UVT_MENSUAL   = Decimal("32")
MAXIMO_DEPENDIENTES_RECONOCIDOS           = 4          # entero — no es operando Decimal

# ── Descuentos tributarios ────────────────────────────────────────────────────

TARIFA_DESCUENTO_DONACIONES = Decimal("0.25")

# ── Sanciones e intereses de mora ─────────────────────────────────────────────

SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL                  = Decimal("0.05")
SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO            = Decimal("1.00")
SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS   = Decimal("0.005")
SANCION_MINIMA_UVT                                          = Decimal("10")
SANCION_CORRECCION_ANTES_EMPLAZAMIENTO_PORCENTAJE           = Decimal("0.10")
SANCION_CORRECCION_DESPUES_EMPLAZAMIENTO_PORCENTAJE         = Decimal("0.20")

# Tasa de mora referencial — informativa, no entra al motor en esta versión.
TASA_INTERES_MORA_DIARIA_REFERENCIAL = 0.00073  # float informativo

# ── Anticipo de renta (art. 807 E.T.) ────────────────────────────────────────

ANTICIPO_PORCENTAJE_PRIMERA_VEZ              = Decimal("0.25")
ANTICIPO_PORCENTAJE_SEGUNDA_VEZ              = Decimal("0.50")
ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE  = Decimal("0.75")

# ── Compensación de pérdidas fiscales ────────────────────────────────────────

LIMITE_ANIOS_COMPENSACION_PERDIDAS = 12  # int informativo

# ── Renta exenta cesantías (art. 206 num. 4 E.T.) ────────────────────────────

TABLA_EXENCION_CESANTIAS_UVT_MENSUAL = [
    (Decimal("0"),   Decimal("350"), Decimal("1.00")),
    (Decimal("350"), Decimal("410"), Decimal("0.90")),
    (Decimal("410"), Decimal("470"), Decimal("0.80")),
    (Decimal("470"), Decimal("530"), Decimal("0.60")),
    (Decimal("530"), Decimal("590"), Decimal("0.40")),
    (Decimal("590"), Decimal("650"), Decimal("0.20")),
    (Decimal("650"), None,           Decimal("0.00")),
]