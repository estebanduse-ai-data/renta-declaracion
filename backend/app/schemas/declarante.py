import uuid

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
    patrimonio_bruto: float = Field(ge=0, default=0)
    pasivos: float = Field(ge=0, default=0)


class ActualizarPeriodoGravable(BaseModel):
    estado: str | None = Field(default=None, pattern=r"^(borrador|en_revision|presentado)$")
    patrimonio_bruto: float | None = Field(default=None, ge=0)
    pasivos: float | None = Field(default=None, ge=0)


class RespuestaPeriodoGravable(BaseModel):
    id: uuid.UUID
    declarante_id: uuid.UUID
    anio: int
    estado: str
    patrimonio_bruto: float
    pasivos: float

    class Config:
        from_attributes = True
