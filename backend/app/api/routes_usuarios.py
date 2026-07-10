import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permisos import requiere_rol
from app.core.security import hashear_password
from app.db.session import get_db
from app.models.usuario import RolUsuario, Usuario
from app.schemas.usuario import ActualizarUsuario, CrearUsuario, RespuestaUsuario

router = APIRouter(
    prefix="/usuarios", tags=["usuarios"], dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))]
)


@router.get("", response_model=list[RespuestaUsuario])
def listar_usuarios(db: Session = Depends(get_db)) -> list[Usuario]:
    return db.query(Usuario).order_by(Usuario.nombre).all()


@router.post("", response_model=RespuestaUsuario, status_code=status.HTTP_201_CREATED)
def crear_usuario(solicitud: CrearUsuario, db: Session = Depends(get_db)) -> Usuario:
    existente = db.query(Usuario).filter(Usuario.email == solicitud.email).first()
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese correo."
        )

    usuario = Usuario(
        email=solicitud.email,
        nombre=solicitud.nombre,
        password_hash=hashear_password(solicitud.password),
        rol=solicitud.rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}", response_model=RespuestaUsuario)
def actualizar_usuario(
    usuario_id: uuid.UUID, solicitud: ActualizarUsuario, db: Session = Depends(get_db)
) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    datos = solicitud.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(usuario, campo, valor)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
