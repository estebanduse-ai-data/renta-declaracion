import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.usuario import RolUsuario


class CrearUsuario(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, description="Mínimo 8 caracteres")
    rol: RolUsuario = RolUsuario.AUXILIAR


class ActualizarUsuario(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    rol: RolUsuario | None = None
    activo: bool | None = None


class RespuestaUsuario(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    nombre: str
    rol: RolUsuario
    activo: bool