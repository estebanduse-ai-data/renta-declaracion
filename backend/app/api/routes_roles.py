"""
routes_roles.py — gestión de roles adicionales por usuario.

Endpoints
──────────
  GET    /usuarios/{usuario_id}/roles          Lista todos los roles del usuario
  POST   /usuarios/{usuario_id}/roles          Agrega un rol adicional
  DELETE /usuarios/{usuario_id}/roles/{rol}    Quita un rol adicional

Restricciones de negocio
─────────────────────────
  • Solo Admin puede gestionar roles.
  • No se puede quitar el rol primario (usuario.rol) desde aquí —
    ese campo se edita en el panel de usuario general (fuera de scope).
  • No se puede dejar a un usuario sin ningún rol:
    si el usuario solo tiene el rol primario, DELETE devuelve 409.
  • Un admin no puede quitarse a sí mismo el rol ADMIN
    (para evitar quedar sin administrador accidentalmente).

Por qué no se edita usuario.rol aquí
──────────────────────────────────────
`usuario.rol` es el rol "de identidad" que se incluye en el JWT.
Cambiarlo requiere revocar el token activo del usuario, que todavía
no tenemos implementado (Act. 3.4 — refresh token). Hasta entonces,
`usuario.rol` solo se edita al crear el usuario o desde el panel de
admin con un reset de contraseña explícito que invalida la sesión.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permisos import obtener_usuario_actual, requiere_rol
from app.db.session import get_db
from app.models.usuario import RolUsuario, Usuario, UsuarioRol

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios", "roles"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))],
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class RolItem(BaseModel):
    rol: str
    es_primario: bool


class RespuestaRoles(BaseModel):
    usuario_id: uuid.UUID
    nombre: str
    email: str
    rol_primario: str
    roles_adicionales: list[str]
    todos_los_roles: list[str]


class SolicitudAgregarRol(BaseModel):
    rol: RolUsuario


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_usuario_o_404(db: Session, usuario_id: uuid.UUID) -> Usuario:
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {usuario_id} no encontrado.",
        )
    return u


# ── GET /usuarios/{usuario_id}/roles ─────────────────────────────────────────

@router.get("/{usuario_id}/roles", response_model=RespuestaRoles)
def listar_roles(
    usuario_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RespuestaRoles:
    """Lista el rol primario y los roles adicionales de un usuario."""
    u = _get_usuario_o_404(db, usuario_id)
    return RespuestaRoles(
        usuario_id=u.id,
        nombre=u.nombre,
        email=u.email,
        rol_primario=u.rol.value,
        roles_adicionales=[ur.rol for ur in u.roles_adicionales],
        todos_los_roles=sorted(u.todos_los_roles),
    )


# ── POST /usuarios/{usuario_id}/roles ─────────────────────────────────────────

@router.post(
    "/{usuario_id}/roles",
    response_model=RespuestaRoles,
    status_code=status.HTTP_201_CREATED,
)
def agregar_rol(
    usuario_id: uuid.UUID,
    solicitud: SolicitudAgregarRol,
    db: Session = Depends(get_db),
) -> RespuestaRoles:
    """
    Agrega un rol adicional al usuario.

    Si el usuario ya tiene ese rol (primario o adicional), devuelve 409.
    """
    u = _get_usuario_o_404(db, usuario_id)
    rol_str = solicitud.rol.value

    # Verificar que no lo tenga ya
    if rol_str in u.todos_los_roles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario ya tiene el rol '{rol_str}'.",
        )

    nuevo = UsuarioRol(usuario_id=u.id, rol=rol_str)
    db.add(nuevo)
    db.commit()
    db.refresh(u)

    return RespuestaRoles(
        usuario_id=u.id,
        nombre=u.nombre,
        email=u.email,
        rol_primario=u.rol.value,
        roles_adicionales=[ur.rol for ur in u.roles_adicionales],
        todos_los_roles=sorted(u.todos_los_roles),
    )


# ── DELETE /usuarios/{usuario_id}/roles/{rol} ─────────────────────────────────

@router.delete("/{usuario_id}/roles/{rol}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_rol(
    usuario_id: uuid.UUID,
    rol: str,
    db: Session = Depends(get_db),
    admin_actual: Usuario = Depends(obtener_usuario_actual),
) -> None:
    """
    Quita un rol adicional del usuario.

    Restricciones:
      - No se puede quitar el rol primario (usuario.rol) — solo los adicionales.
      - Un admin no puede quitarse a sí mismo el rol ADMIN.
    """
    u = _get_usuario_o_404(db, usuario_id)

    # Validar formato del rol
    roles_validos = {r.value for r in RolUsuario}
    if rol not in roles_validos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Rol '{rol}' no reconocido. Valores válidos: {sorted(roles_validos)}.",
        )

    # No se puede quitar el rol primario por esta vía
    if rol == u.rol.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"'{rol}' es el rol primario de este usuario y no se puede quitar aquí. "
                "Para cambiarlo, edita el usuario desde el panel de administración."
            ),
        )

    # Un admin no puede quitarse a sí mismo el rol ADMIN
    if str(usuario_id) == str(admin_actual.id) and rol == RolUsuario.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes quitarte el rol ADMIN a ti mismo.",
        )

    # Buscar el registro en usuario_rol
    registro = (
        db.query(UsuarioRol)
        .filter(UsuarioRol.usuario_id == usuario_id, UsuarioRol.rol == rol)
        .first()
    )
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario no tiene el rol adicional '{rol}'.",
        )

    db.delete(registro)
    db.commit()