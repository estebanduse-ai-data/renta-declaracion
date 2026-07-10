from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
_contexto_password = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password_plano: str) -> str:
    return _contexto_password.hash(password_plano)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    return _contexto_password.verify(password_plano, password_hash)


def crear_token_acceso(*, subject: str, rol: str) -> str:
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiracion_minutos)
    payload = {"sub": subject, "rol": rol, "exp": expiracion}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algoritmo)


class TokenInvalidoError(Exception):
    pass


def decodificar_token_acceso(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algoritmo])
    except JWTError as e:
        raise TokenInvalidoError(str(e)) from e
