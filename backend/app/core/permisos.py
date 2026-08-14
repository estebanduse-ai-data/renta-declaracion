"""
permisos.py — dependencias de autenticación y autorización.

Cambios en DT-4
────────────────
`requiere_rol()` ahora evalúa `usuario.todos_los_roles` (propiedad del
modelo que hace UNION del rol primario + roles adicionales de usuario_rol)
en lugar de `usuario.rol` (solo el rol primario).

Impacto en los routers existentes
───────────────────────────────────
Cero. La firma de `requiere_rol()` es idéntica — recibe RolUsuario enums,
devuelve el objeto Usuario. Todos los routers siguen funcionando sin cambios.

El único comportamiento diferente es que ahora un usuario con rol=ADMIN
y una fila usuario_rol(rol=CONTADOR) puede acceder a endpoints que antes
le devolvían 403. Ese era exactamente el objetivo de DT-4.

Ejemplo post-DT-4
──────────────────
  usuario: { rol="admin", roles_adicionales=[UsuarioRol(rol="contador")] }
  todos_los_roles → {"admin", "contador"}

  requiere_rol(RolUsuario.ADMIN)            → OK (estaba antes)
  requiere_rol(RolUsuario.CONTADOR)         → OK (nuevo)
  requiere_rol(RolUsuario.AUXILIAR)         → 403 (correcto)
  requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR) → OK (ya era OK)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import TokenInvalidoError, decodificar_token_acceso
from app.db.session import get_db
from app.models.usuario import RolUsuario, Usuario

_oauth2_esquema = OAuth2PasswordBearer(tokenUrl="/auth/login")


def obtener_usuario_actual(
    token: str = Depends(_oauth2_esquema),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Decodifica el JWT, verifica que el usuario existe y está activo,
    y devuelve el objeto Usuario con sus roles_adicionales cargados.

    Los roles_adicionales se cargan automáticamente por la relación
    lazy="select" en Usuario. La primera vez que se accede a
    `usuario.todos_los_roles` o `usuario.roles_adicionales` SQLAlchemy
    emite el SELECT de usuario_rol. En la práctica esto ocurre dentro
    de la misma request, mientras la sesión está abierta.
    """
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión. Inicia sesión de nuevo.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token_acceso(token)
    except TokenInvalidoError:
        raise credenciales_invalidas

    email: str | None = payload.get("sub")
    if email is None:
        raise credenciales_invalidas

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not usuario.activo:
        raise credenciales_invalidas

    return usuario


def requiere_rol(*roles_permitidos: RolUsuario):
    """
    Dependencia parametrizable de autorización por rol.

    Uso (sin cambios respecto a la versión anterior):
        @router.post("/admin/algo", dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))])
        def mi_endpoint(usuario: Usuario = Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.CONTADOR))):
            ...

    Post DT-4: la verificación usa `usuario.todos_los_roles` (set de strings)
    en lugar de `usuario.rol` (enum escalar). El resultado para usuarios
    con un solo rol es idéntico al anterior.
    """
    valores_permitidos = {r.value for r in roles_permitidos}

    def _verificar(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
        # todos_los_roles devuelve un set[str] con el rol primario + adicionales
        if not (usuario.todos_los_roles & valores_permitidos):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Esta acción requiere uno de estos roles: "
                    f"{', '.join(sorted(valores_permitidos))}."
                ),
            )
        return usuario

    return _verificar