from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import crear_token_acceso, verificar_password
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import RespuestaToken, SolicitudLogin

router = APIRouter(prefix="/auth", tags=["auth"])


class RespuestaTokenV2(RespuestaToken):
    """
    Extiende RespuestaToken con la lista completa de roles.

    `roles` es la lista de todos los roles del usuario (primario + adicionales).
    El frontend puede usar esto para mostrar capacidades de ambos roles
    sin necesidad de hacer un fetch adicional.

    `rol` (singular) se mantiene para compatibilidad con el frontend actual
    que lee `respuesta.rol` en el handler de login de main.jsx.
    """
    roles: list[str]


@router.post("/login", response_model=RespuestaTokenV2)
def login(solicitud: SolicitudLogin, db: Session = Depends(get_db)) -> RespuestaTokenV2:
    usuario = db.query(Usuario).filter(Usuario.email == solicitud.email).first()

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contraseña incorrectos.",
    )

    if usuario is None or not verificar_password(solicitud.password, usuario.password_hash):
        raise credenciales_invalidas

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuario está desactivado. Contacta a un Admin.",
        )

    # Obtener todos los roles (primario + adicionales de usuario_rol)
    todos_roles = sorted(usuario.todos_los_roles)

    token = crear_token_acceso(
        subject=usuario.email,
        rol=usuario.rol.value,       # rol primario — para compatibilidad
        roles=todos_roles,            # lista completa — DT-4
    )

    return RespuestaTokenV2(
        access_token=token,
        rol=usuario.rol.value,        # el frontend actual lee esto
        roles=todos_roles,             # disponible para lógica de múltiples roles
        nombre=usuario.nombre,
    )