"""
Esquema de validación del documento `ParametroTributario.valores`.

Este esquema es, deliberadamente, un espejo 1:1 de las constantes de
`app/rules_engine/parametros_2025.py` — mismo nombre de campo, mismo
significado. Así, cargar los valores por defecto de un año nuevo es tan
simple como convertir el módulo Python a dict, y el motor de reglas puede
recibir indistintamente el módulo estático (en pruebas unitarias, sin base
de datos) o una instancia de este esquema (en producción, vía la API) sin
cambiar ni una línea de `app/rules_engine/*.py`.
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class TramoTarifa(BaseModel):
    limite_inferior: Decimal = Field(ge=0)
    limite_superior: Decimal | None = Field(default=None, ge=0)
    tarifa: Decimal = Field(ge=0, le=1)
    base_uvt: Decimal = Field(ge=0)

    @field_validator("limite_superior")
    @classmethod
    def limite_superior_mayor_que_inferior(cls, v, info):
        limite_inferior = info.data.get("limite_inferior")
        if v is not None and limite_inferior is not None and v <= limite_inferior:
            raise ValueError("limite_superior debe ser mayor que limite_inferior")
        return v


class TramoExencion(BaseModel):
    limite_inferior: Decimal = Field(ge=0)
    limite_superior: Decimal | None = Field(default=None, ge=0)
    porcentaje_exento: Decimal = Field(ge=0, le=1)


class ParametrosTributariosPayload(BaseModel):
    anio_gravable: int = Field(ge=2000, le=2100)
    uvt: Decimal = Field(gt=0, description="Valor de la UVT en pesos para el año gravable")

    tabla_tarifa: list[TramoTarifa] = Field(min_length=1)

    limite_renta_exenta_deducciones_porcentaje: Decimal = Field(ge=0, le=1)
    tope_renta_exenta_deducciones_uvt: Decimal = Field(gt=0)

    porcentaje_renta_exenta_laboral: Decimal = Field(ge=0, le=1)
    tope_renta_exenta_laboral_uvt: Decimal = Field(gt=0)

    tarifa_renta_presuntiva: Decimal = Field(ge=0, le=1)
    tope_vivienda_habitacion_uvt: Decimal = Field(gt=0)
    tope_activos_sector_agropecuario_uvt: Decimal = Field(gt=0)

    limite_descuentos_tributarios_porcentaje: Decimal = Field(ge=0, le=1)
    tope_pago_unica_cuota_uvt: Decimal = Field(gt=0)

    tarifa_ganancia_ocasional_general: Decimal = Field(ge=0, le=1)
    tarifa_ganancia_ocasional_loterias: Decimal = Field(ge=0, le=1)
    tope_exento_venta_casa_habitacion_uvt: Decimal = Field(gt=0)

    porcentaje_exento_herencia_general: Decimal = Field(ge=0, le=1)
    tope_exento_herencia_general_uvt: Decimal = Field(gt=0)
    tope_exento_herencia_vivienda_uvt: Decimal = Field(gt=0)
    tope_participacion_acciones_bolsa_no_gravado: Decimal = Field(ge=0, le=1)

    factores_ajuste_art73_por_anio: dict[int, float] = Field(default_factory=dict)

    tabla_tarifa_dividendos: list[TramoTarifa] = Field(min_length=1)
    tarifa_dividendos_no_gravados_sociedad: Decimal = Field(ge=0, le=1)

    # Deducción combinada vivienda + ICETEX (art. 119 E.T.) — ver nota en
    # app/rules_engine/deducciones.py sobre por qué comparten un solo tope.
    tope_deduccion_intereses_vivienda_uvt: Decimal = Field(
        gt=0, description="Tope anual COMBINADO de intereses de vivienda + ICETEX (art. 119 E.T.)"
    )
    tope_deduccion_salud_uvt_mensual: Decimal = Field(gt=0)

    porcentaje_deduccion_dependientes: Decimal = Field(ge=0, le=1)
    tope_deduccion_dependientes_uvt_mensual: Decimal = Field(gt=0)
    maximo_dependientes_reconocidos: int = Field(gt=0)

    tabla_exencion_cesantias_uvt_mensual: list[TramoExencion] = Field(min_length=1)

    tarifa_descuento_donaciones: Decimal = Field(ge=0, le=1)

    sancion_extemporaneidad_porcentaje_mensual: Decimal = Field(ge=0, le=1)
    sancion_extemporaneidad_tope_porcentaje_impuesto: Decimal = Field(ge=0, le=2)
    sancion_extemporaneidad_porcentaje_mensual_sobre_ingresos: Decimal = Field(ge=0, le=1)
    sancion_minima_uvt: Decimal = Field(gt=0)
    sancion_correccion_antes_emplazamiento_porcentaje: Decimal = Field(ge=0, le=1)
    sancion_correccion_despues_emplazamiento_porcentaje: Decimal = Field(ge=0, le=1)

    anticipo_porcentaje_primera_vez: Decimal = Field(ge=0, le=1)
    anticipo_porcentaje_segunda_vez: Decimal = Field(ge=0, le=1)
    anticipo_porcentaje_tercera_vez_en_adelante: Decimal = Field(ge=0, le=1)

    limite_anios_compensacion_perdidas: int = Field(gt=0)

    model_config = {
        "json_schema_extra": {
            "description": (
                "Espejo validado de app/rules_engine/parametros_2025.py. "
                "Ver docs/GESTION_PROYECTO.md y ARQUITECTURA.md para el porqué "
                "de este diseño."
            )
        }
    }