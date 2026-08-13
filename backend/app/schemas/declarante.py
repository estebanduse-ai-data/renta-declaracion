from decimal import Decimal
import uuid
from typing import Any

from pydantic import BaseModel, Field


class CrearDeclarante(BaseModel):
    nit: str = Field(min_length=6, max_length=10, pattern=r"^\d+$")
    digito_verificacion: str = Field(min_length=1, max_length=1, pattern=r"^\d$")
    primer_nombre: str = Field(min_length=1, max_length=100)
    primer_apellido: str = Field(min_length=1, max_length=100)
    actividad_economica: str = Field(min_length=1, max_length=10)


class ActualizarDeclarante(BaseModel):
    primer_nombre: str | None = Field(default=None, min_length=1, max_length=100)
    primer_apellido: str | None = Field(default=None, min_length=1, max_length=100)
    actividad_economica: str | None = Field(default=None, min_length=1, max_length=10)


class RespuestaDeclarante(BaseModel):
    id: uuid.UUID
    nit: str
    digito_verificacion: str
    primer_nombre: str
    primer_apellido: str
    actividad_economica: str

    class Config:
        from_attributes = True


class CrearPeriodoGravable(BaseModel):
    anio: int = Field(ge=2000, le=2100)
    # Decimal para valores monetarios en pesos — evita errores de punto
    # flotante IEEE 754 en cálculos presentados a la DIAN (Act. 0.5).
    patrimonio_bruto: Decimal = Field(ge=0, default=Decimal("0"), decimal_places=2)
    pasivos: Decimal = Field(ge=0, default=Decimal("0"), decimal_places=2)


class ActualizarPeriodoGravable(BaseModel):
    estado: str | None = Field(default=None, pattern=r"^(borrador|en_revision|presentado)$")
    patrimonio_bruto: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    pasivos: Decimal | None = Field(default=None, ge=0, decimal_places=2)


class RespuestaPeriodoGravable(BaseModel):
    id: uuid.UUID
    declarante_id: uuid.UUID
    anio: int
    estado: str
    patrimonio_bruto: Decimal
    pasivos: Decimal
    # Incluido en la respuesta para que el frontend pueda mostrar
    # el resultado de la última liquidación sin recalcular.
    resultado_liquidacion: dict[str, Any] | None = None

    class Config:
        from_attributes = True