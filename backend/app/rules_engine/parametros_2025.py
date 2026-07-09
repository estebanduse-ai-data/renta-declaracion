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

# ---------------------------------------------------------------------------
# Ganancias ocasionales (artículos 299 a 317 E.T.)
# ---------------------------------------------------------------------------

# Tarifa general de ganancia ocasional (venta de activos fijos poseídos > 2 años,
# herencias, legados, donaciones, venta de acciones). Ley 2277 de 2022.
TARIFA_GANANCIA_OCASIONAL_GENERAL = 0.15

# Tarifa fija y especial para loterías, rifas, apuestas y similares (art. 317 E.T.).
# No tiene porción exenta.
TARIFA_GANANCIA_OCASIONAL_LOTERIAS = 0.20

# Exención en la venta de la casa o apartamento de habitación (art. 311-1 E.T.),
# aplica solo si es la única vivienda del contribuyente y se cumplen los requisitos
# de depósito en cuenta AFC u otras condiciones de la norma.
TOPE_EXENTO_VENTA_CASA_HABITACION_UVT = 5_000

# Exención general sobre herencias, legados y donaciones (art. 307 num. 1 E.T.):
# el 20% del valor, sin exceder el tope en UVT.
PORCENTAJE_EXENTO_HERENCIA_GENERAL = 0.20
TOPE_EXENTO_HERENCIA_GENERAL_UVT = 1_625

# Exención adicional cuando lo heredado es la única vivienda urbana o rural de
# habitación del causante (art. 307 num. 2 y 3 E.T.).
TOPE_EXENTO_HERENCIA_VIVIENDA_UVT = 3_250

# Venta de acciones inscritas en bolsa: no constituye renta ni ganancia ocasional
# si lo vendido en el año no supera este porcentaje de las acciones en circulación
# de la respectiva sociedad, del mismo beneficiario real (art. 36-1 E.T.).
TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO = 0.03

# Factores de ajuste fiscal por año de adquisición (art. 73 E.T.), usados para
# indexar el costo de bienes raíces y acciones no inscritas en bolsa poseídos
# como activos fijos. Valores REFERENCIALES — deben confirmarse cada año contra
# el decreto de ajuste de costos que expide el Gobierno Nacional antes de usarse
# en producción. Se incluye una muestra de años recientes; ampliar según se
# necesite.
FACTORES_AJUSTE_ART73_POR_ANIO = {
    2015: 1.727,
    2016: 1.629,
    2017: 1.550,
    2018: 1.500,
    2019: 1.452,
    2020: 1.412,
    2021: 1.376,
    2022: 1.246,
    2023: 1.147,
    2024: 1.063,
    2025: 1.000,
}

# ---------------------------------------------------------------------------
# Cédula de dividendos y participaciones (art. 242 E.T., modificado por Ley 2277/2022)
# ---------------------------------------------------------------------------

# Tabla marginal sobre dividendos y participaciones gravados en cabeza del socio
# (dividendos ya gravados a nivel de la sociedad). Formato compatible con
# calcular_impuesto_uvt(): (limite_inferior, limite_superior, tarifa, base_uvt)
TABLA_TARIFA_DIVIDENDOS_UVT = [
    (0, 1_090, 0.00, 0),
    (1_090, None, 0.15, 0),
]

# Tarifa sobre dividendos NO gravados en cabeza de la sociedad (utilidades que no
# pagaron impuesto de renta corporativo) — se aplica antes de pasar por la tabla
# marginal anterior (art. 242 num. 3 E.T.).
TARIFA_DIVIDENDOS_NO_GRAVADOS_SOCIEDAD = 0.35

# ---------------------------------------------------------------------------
# Deducciones con tope (cédula general)
# ---------------------------------------------------------------------------

# Intereses en préstamos para adquisición de vivienda (art. 119 E.T.).
TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT = 1_200

# Pagos por salud (medicina prepagada / pólizas de salud), art. 387 E.T.
TOPE_DEDUCCION_SALUD_UVT_MENSUAL = 16

# Deducción por dependientes económicos (art. 387 E.T.): el menor entre un
# porcentaje del ingreso laboral y un tope mensual en UVT.
PORCENTAJE_DEDUCCION_DEPENDIENTES = 0.10
TOPE_DEDUCCION_DEPENDIENTES_UVT_MENSUAL = 32
MAXIMO_DEPENDIENTES_RECONOCIDOS = 4

# ---------------------------------------------------------------------------
# Descuentos tributarios (créditos directos contra el impuesto, no deducciones)
# ---------------------------------------------------------------------------

# Descuento por donaciones a entidades del régimen especial (art. 257 E.T.):
# un porcentaje del valor donado se resta directamente del impuesto a cargo.
TARIFA_DESCUENTO_DONACIONES = 0.25

# Límite conjunto de todos los descuentos tributarios sobre el impuesto básico
# de renta (art. 259 E.T.) — ya existe como LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE
# arriba; se referencia aquí por completitud documental.

# ---------------------------------------------------------------------------
# Sanciones e intereses de mora (art. 640, 641, 644 y 635 E.T.)
# ---------------------------------------------------------------------------

# Sanción por extemporaneidad: 5% del impuesto a cargo por cada mes o fracción
# de mes de retraso, sin exceder el 100% del impuesto (art. 641 E.T.).
SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL = 0.05
SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO = 1.00

# Si no hay impuesto a cargo, la sanción se calcula sobre los ingresos brutos
# del periodo (0.5% mensual, con tope del 100% de esos ingresos o del doble
# del saldo a favor, lo que sea menor — se simplifica aquí al primer criterio).
SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS = 0.005

# Sanción mínima (art. 639 E.T.), aplica como piso de cualquier sanción.
SANCION_MINIMA_UVT = 10

# Sanción por corrección que aumenta el impuesto o disminuye el saldo a favor
# (art. 644 E.T.).
SANCION_CORRECCION_ANTES_EMPLAZAMIENTO_PORCENTAJE = 0.10
SANCION_CORRECCION_DESPUES_EMPLAZAMIENTO_PORCENTAJE = 0.20

# Tasa de interés de mora diaria. REFERENCIAL — la tasa real la certifica la
# Superintendencia Financiera trimestralmente y varía en el tiempo; debe
# consultarse la tasa vigente antes de liquidar un caso real.
TASA_INTERES_MORA_DIARIA_REFERENCIAL = 0.00073  # equivalente aprox. a 22% E.A.

# ---------------------------------------------------------------------------
# Anticipo de renta para el año gravable siguiente (art. 807 E.T.)
# ---------------------------------------------------------------------------

ANTICIPO_PORCENTAJE_PRIMERA_VEZ = 0.25
ANTICIPO_PORCENTAJE_SEGUNDA_VEZ = 0.50
ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE = 0.75

# ---------------------------------------------------------------------------
# Compensación de pérdidas fiscales de años anteriores (art. 147 E.T., por
# analogía aplicado a la cédula respectiva de personas naturales)
# ---------------------------------------------------------------------------

# Plazo máximo, en años, para compensar una pérdida fiscal contra rentas
# líquidas futuras de la misma cédula. Valor informativo — el motor no valida
# todavía si una pérdida ya venció, eso requiere el histórico completo por
# declarante (ver docs/FALTANTES.md).
LIMITE_ANIOS_COMPENSACION_PERDIDAS = 12

# ---------------------------------------------------------------------------
# Deducción combinada de intereses de vivienda y créditos ICETEX (art. 119 E.T.)
# ---------------------------------------------------------------------------

# El artículo 119 E.T. comparte UN SOLO tope de 1.200 UVT anuales entre los
# intereses de crédito de vivienda y los intereses de créditos educativos
# ICETEX — no son topes independientes. Se reutiliza
# TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT (definido arriba) como el tope
# combinado; se referencia aquí por completitud documental.

# ---------------------------------------------------------------------------
# Renta exenta sobre cesantías e intereses de cesantías (art. 206 num. 4 E.T.)
# ---------------------------------------------------------------------------

# Tabla de porcentaje exento según el promedio mensual de ingresos laborales
# de los últimos 6 meses, en UVT. Formato: (limite_inferior, limite_superior,
# porcentaje_exento). limite_superior = None significa "sin límite superior".
TABLA_EXENCION_CESANTIAS_UVT_MENSUAL = [
    (0, 350, 1.00),
    (350, 410, 0.90),
    (410, 470, 0.80),
    (470, 530, 0.60),
    (530, 590, 0.40),
    (590, 650, 0.20),
    (650, None, 0.00),
]

# ---------------------------------------------------------------------------
# Becas de estudio (art. 206 num. 9 E.T.)
# ---------------------------------------------------------------------------
# Exentas en su totalidad siempre que no constituyan contraprestación por
# servicios prestados por el becario — no tienen tope en UVT, es una
# exención de todo o nada según esa condición.
