"""
Convierte el módulo estático `parametros_2025.py` (usado hoy por las pruebas
unitarias del motor de reglas, que deben poder correr sin base de datos) al
formato de diccionario que exige `app/schemas/configuracion.py`.

Se usa una sola vez por año gravable, al sembrar el primer
`ParametroTributario` en base de datos (ver `scripts/sembrar_parametros.py`
más abajo en este mismo directorio de servicios). A partir de ahí, la base
de datos es la fuente de verdad y este módulo estático queda como respaldo
de solo lectura para pruebas y para el caso de que la base de datos no tenga
todavía un registro para el año consultado.
"""

from app.rules_engine import parametros_2025 as P


def _tabla_tarifa_a_dict(tabla: list[tuple]) -> list[dict]:
    return [
        {
            "limite_inferior": t[0],
            "limite_superior": t[1],
            "tarifa": t[2],
            "base_uvt": t[3],
        }
        for t in tabla
    ]


def _tabla_exencion_a_dict(tabla: list[tuple]) -> list[dict]:
    return [
        {"limite_inferior": t[0], "limite_superior": t[1], "porcentaje_exento": t[2]}
        for t in tabla
    ]


def construir_payload_parametros_2025() -> dict:
    """
    Devuelve un diccionario con exactamente los campos que espera
    `ParametrosTributariosPayload`, poblado con los valores del año 2025.
    """
    return {
        "anio_gravable": P.ANIO_GRAVABLE,
        "uvt": P.UVT,
        "tabla_tarifa": _tabla_tarifa_a_dict(P.TABLA_TARIFA_UVT),
        "limite_renta_exenta_deducciones_porcentaje": P.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE,
        "tope_renta_exenta_deducciones_uvt": P.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT,
        "porcentaje_renta_exenta_laboral": P.PORCENTAJE_RENTA_EXENTA_LABORAL,
        "tope_renta_exenta_laboral_uvt": P.TOPE_RENTA_EXENTA_LABORAL_UVT,
        "tarifa_renta_presuntiva": P.TARIFA_RENTA_PRESUNTIVA,
        "tope_vivienda_habitacion_uvt": P.TOPE_VIVIENDA_HABITACION_UVT,
        "tope_activos_sector_agropecuario_uvt": P.TOPE_ACTIVOS_SECTOR_AGROPECUARIO_UVT,
        "limite_descuentos_tributarios_porcentaje": P.LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE,
        "tope_pago_unica_cuota_uvt": P.TOPE_PAGO_UNICA_CUOTA_UVT,
        "tarifa_ganancia_ocasional_general": P.TARIFA_GANANCIA_OCASIONAL_GENERAL,
        "tarifa_ganancia_ocasional_loterias": P.TARIFA_GANANCIA_OCASIONAL_LOTERIAS,
        "tope_exento_venta_casa_habitacion_uvt": P.TOPE_EXENTO_VENTA_CASA_HABITACION_UVT,
        "porcentaje_exento_herencia_general": P.PORCENTAJE_EXENTO_HERENCIA_GENERAL,
        "tope_exento_herencia_general_uvt": P.TOPE_EXENTO_HERENCIA_GENERAL_UVT,
        "tope_exento_herencia_vivienda_uvt": P.TOPE_EXENTO_HERENCIA_VIVIENDA_UVT,
        "tope_participacion_acciones_bolsa_no_gravado": P.TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO,
        "factores_ajuste_art73_por_anio": P.FACTORES_AJUSTE_ART73_POR_ANIO,
        "tabla_tarifa_dividendos": _tabla_tarifa_a_dict(P.TABLA_TARIFA_DIVIDENDOS_UVT),
        "tarifa_dividendos_no_gravados_sociedad": P.TARIFA_DIVIDENDOS_NO_GRAVADOS_SOCIEDAD,
        "tope_deduccion_intereses_vivienda_uvt": P.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT,
        "tope_deduccion_salud_uvt_mensual": P.TOPE_DEDUCCION_SALUD_UVT_MENSUAL,
        "porcentaje_deduccion_dependientes": P.PORCENTAJE_DEDUCCION_DEPENDIENTES,
        "tope_deduccion_dependientes_uvt_mensual": P.TOPE_DEDUCCION_DEPENDIENTES_UVT_MENSUAL,
        "maximo_dependientes_reconocidos": P.MAXIMO_DEPENDIENTES_RECONOCIDOS,
        "tabla_exencion_cesantias_uvt_mensual": _tabla_exencion_a_dict(
            P.TABLA_EXENCION_CESANTIAS_UVT_MENSUAL
        ),
        "tarifa_descuento_donaciones": P.TARIFA_DESCUENTO_DONACIONES,
        "sancion_extemporaneidad_porcentaje_mensual": P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL,
        "sancion_extemporaneidad_tope_porcentaje_impuesto": P.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO,
        "sancion_extemporaneidad_porcentaje_mensual_sobre_ingresos": (
            P.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS
        ),
        "sancion_minima_uvt": P.SANCION_MINIMA_UVT,
        "sancion_correccion_antes_emplazamiento_porcentaje": P.SANCION_CORRECCION_ANTES_EMPLAZAMIENTO_PORCENTAJE,
        "sancion_correccion_despues_emplazamiento_porcentaje": P.SANCION_CORRECCION_DESPUES_EMPLAZAMIENTO_PORCENTAJE,
        "anticipo_porcentaje_primera_vez": P.ANTICIPO_PORCENTAJE_PRIMERA_VEZ,
        "anticipo_porcentaje_segunda_vez": P.ANTICIPO_PORCENTAJE_SEGUNDA_VEZ,
        "anticipo_porcentaje_tercera_vez_en_adelante": P.ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE,
        "limite_anios_compensacion_perdidas": P.LIMITE_ANIOS_COMPENSACION_PERDIDAS,
    }
