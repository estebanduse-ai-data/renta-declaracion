"""
security.py — utilidades de hashing y JWT.

Cambios en DT-4
────────────────
`crear_token_acceso()` ahora recibe `roles: list[str]` además de `rol: str`.
El payload del JWT incluye ambos:

  {
    "sub":   "contador@empresa.com",
    "rol":   "admin",          ← rol primario (ya existía — compatibilidad)
    "roles": ["admin", "contador"],  ← todos los roles (DT-4)
    "exp":   ...
  }

El frontend sigue leyendo `rol` para el flujo de login (sin cambios).
`roles` está disponible para la versión futura del frontend que necesite
mostrar capacidades de ambos roles simultáneamente.

Compatibilidad
──────────────
Los tokens emitidos antes de DT-4 (que no tienen `roles`) siguen siendo
válidos — `decodificar_token_acceso()` los acepta y los routers usan
`permisos.py` que lee `usuario.todos_los_roles` desde la BD, no desde
el token. Por lo tanto, un token viejo sin `roles` sigue funcionando
correctamente hasta que expire.
"""

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


def crear_token_acceso(*, subject: str, rol: str, roles: list[str] | None = None) -> str:
    """
    Genera un JWT firmado con el subject (email), rol primario y lista de roles.

    `roles` es opcional para compatibilidad con llamadas antiguas que solo
    pasan `rol`. Si se omite, el payload incluirá solo `rol` (comportamiento
    idéntico al pre-DT-4).
    """
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiracion_minutos)
    payload: dict = {"sub": subject, "rol": rol, "exp": expiracion}
    if roles is not None:
        payload["roles"] = sorted(roles)   # ordenados para comparación determinista
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algoritmo)


class TokenInvalidoError(Exception):
    pass


def decodificar_token_acceso(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algoritmo])
    except JWTError as e:
        raise TokenInvalidoError(str(e)) from e