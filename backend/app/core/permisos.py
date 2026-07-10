from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import TokenInvalidoError, decodificar_token_acceso
from app.db.session import get_db
from app.models.usuario import RolUsuario, Usuario

_oauth2_esquema = OAuth2PasswordBearer(tokenUrl="/auth/login")


def obtener_usuario_actual(
    token: str = Depends(_oauth2_esquema), db: Session = Depends(get_db)
) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión. Inicia sesión de nuevo.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token_acceso(token)
    except TokenInvalidoError:
        raise credenciales_invalidas

    email = payload.get("sub")
    if email is None:
        raise credenciales_invalidas

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not usuario.activo:
        raise credenciales_invalidas
    return usuario


def requiere_rol(*roles_permitidos: RolUsuario):
    """
    Dependencia parametrizable: `Depends(requiere_rol(RolUsuario.ADMIN))`
    restringe el endpoint a ese rol. Se puede pasar más de uno, ej.
    `Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR))`.
    """

    def _verificar(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Esta acción requiere uno de estos roles: "
                    f"{', '.join(r.value for r in roles_permitidos)}."
                ),
            )
        return usuario

    return _verificar
