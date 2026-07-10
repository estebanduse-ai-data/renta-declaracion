from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import crear_token_acceso, verificar_password
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import RespuestaToken, SolicitudLogin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=RespuestaToken)
def login(solicitud: SolicitudLogin, db: Session = Depends(get_db)) -> RespuestaToken:
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

    token = crear_token_acceso(subject=usuario.email, rol=usuario.rol.value)
    return RespuestaToken(access_token=token, rol=usuario.rol.value, nombre=usuario.nombre)
