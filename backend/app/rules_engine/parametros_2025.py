"""
Parámetros tributarios — Año gravable 2025.

Este módulo NO contiene lógica de cálculo, solo datos. Cada año gravable nuevo
debe crear un archivo `parametros_<anio>.py` propio (ej. `parametros_2026.py`)
en vez de modificar este archivo, para conservar el histórico y permitir volver
a calcular declaraciones de años anteriores con sus parámetros originales.

Fuente de referencia obligatoria antes de publicar: resolución vigente de la
DIAN para el año gravable correspondiente. Los valores aquí son referenciales
y deben confirmarse antes de un despliegue a producción.
"""

ANIO_GRAVABLE = 2025

# Valor de la Unidad de Valor Tributario (UVT) para el año gravable.
UVT = 49_799

# Tabla progresiva del impuesto de renta — cédula general (artículo 241 E.T.).
# Cada tramo: (limite_inferior_uvt, limite_superior_uvt, tarifa_marginal, impuesto_base_uvt)
TABLA_TARIFA_UVT = [
    (0, 1_090, 0.00, 0),
    (1_090, 1_700, 0.19, 0),
    (1_700, 4_100, 0.28, 116),
    (4_100, 8_670, 0.33, 788),
    (8_670, 18_970, 0.35, 2_296),
    (18_970, 31_000, 0.37, 6_901),
    (31_000, None, 0.39, 11_352),  # None = sin límite superior
]

# Límite de rentas exentas y deducciones de la cédula general (artículo 336 E.T.).
LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE = 0.40
TOPE_RENTA_EXENTA_DEDUCCIONES_UVT = 1_340

# Renta exenta laboral (25% de pagos laborales, artículo 206 numeral 10 E.T.).
PORCENTAJE_RENTA_EXENTA_LABORAL = 0.25
TOPE_RENTA_EXENTA_LABORAL_UVT = 790

# Tarifa de renta presuntiva (Ley 2277 de 2022 la fijó en 0% desde el año gravable 2022).
TARIFA_RENTA_PRESUNTIVA = 0.00

# Exclusiones de la base de renta presuntiva, en UVT (art. 189 E.T.).
TOPE_VIVIENDA_HABITACION_UVT = 8_000
TOPE_ACTIVOS_SECTOR_AGROPECUARIO_UVT = 19_000

# Límite de descuentos tributarios (artículos 255, 256, 257, 257-1 E.T.)
# sobre el impuesto básico de renta.
LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE = 0.30

# Umbral de saldo a pagar que obliga a cancelar en una sola cuota (en UVT).
TOPE_PAGO_UNICA_CUOTA_UVT = 41
