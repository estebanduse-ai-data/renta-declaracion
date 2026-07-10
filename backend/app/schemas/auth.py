from pydantic import BaseModel, EmailStr


class SolicitudLogin(BaseModel):
    email: EmailStr
    password: str


class RespuestaToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str
