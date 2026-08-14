"""
schemas/liquidacion.py — schemas Pydantic del endpoint de liquidación.

Por qué existe este archivo (DT-7)
────────────────────────────────────
En DT-1, `SolicitudLiquidacion` y `RespuestaLiquidacion` se definieron
inline en `routes_liquidacion.py`. Eso era suficiente para el refactor
inicial, pero tiene dos problemas a medida que el proyecto crece:

  1. Si otro router necesita referenciar `RespuestaLiquidacion`
     (por ejemplo, el futuro mapper del Formulario 210 que leerá el
     resultado persistido en JSONB), tiene que importar desde un módulo
     de rutas — acoplamiento incorrecto.

  2. Los schemas de la API deben vivir en `schemas/` para que la
     documentación automática de FastAPI los agrupe correctamente en
     Swagger UI.

Cambio en routes_liquidacion.py
─────────────────────────────────
Reemplazar las definiciones inline por:
    from app.schemas.liquidacion import SolicitudLiquidacion, RespuestaLiquidacion

El contrato HTTP no cambia en absoluto.
"""

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from app.rules_engine import parametros_2025 as _DEFAULTS


class SolicitudLiquidacion(BaseModel):
    anio_gravable: int = Field(
        default=_DEFAULTS.ANIO_GRAVABLE,
        ge=2000,
        le=2100,
        description="Año gravable a liquidar.",
    )
    total_ingresos_brutos_pesos: Decimal = Field(
        ge=0,
        decimal_places=2,
        description="Suma de todos los ingresos brutos cedulares del año.",
    )
    deducciones_imputables_pesos: Decimal = Field(
        ge=0,
        default=Decimal("0"),
        decimal_places=2,
        description="Total de deducciones imputables a la cédula general (art. 331 E.T.).",
    )
    ingreso_salarios_pesos: Decimal = Field(
        ge=0,
        default=Decimal("0"),
        decimal_places=2,
        description="Ingresos por salarios y pagos laborales — base de la renta exenta laboral.",
    )
    total_retenciones_pesos: Decimal = Field(
        ge=0,
        default=Decimal("0"),
        decimal_places=2,
        description="Suma de retenciones en la fuente practicadas durante el año.",
    )
    patrimonio_liquido_anterior_pesos: Decimal = Field(
        default=Decimal("0"),
        decimal_places=2,
        description="Patrimonio líquido del año gravable anterior — base de renta presuntiva.",
    )
    periodo_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Si se provee, el resultado de la liquidación se persiste en el campo "
            "`resultado_liquidacion` (JSONB) del periodo gravable indicado."
        ),
    )


class RespuestaLiquidacion(BaseModel):
    renta_liquida_gravable_pesos: Decimal
    impuesto_uvt:                 Decimal
    impuesto_a_cargo_pesos:       Decimal
    total_retenciones_pesos:      Decimal
    saldo_pesos:                  Decimal
    es_saldo_a_pagar:             bool
    anio_gravable:                int
    uvt_utilizada:                Decimal
    persistido:                   bool = False

    model_config = {"json_encoders": {Decimal: str}}