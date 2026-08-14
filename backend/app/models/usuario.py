"""
Usuarios y roles — control de acceso multirrol.

Historial de cambios
─────────────────────
  Sprint 1: rol Enum escalar — un usuario, un rol.
  DT-4 (Act. 2F.2): tabla usuario_rol muchos-a-muchos aditiva.
    - La columna `rol` (Enum escalar) se mantiene para compatibilidad
      con el token JWT y el login existente.
    - `UsuarioRol` es la tabla de unión: cada fila es un rol adicional.
    - `Usuario.roles_adicionales` es la relación ORM a esa tabla.
    - `Usuario.todos_los_roles` devuelve la unión de ambas fuentes.

En Fase 3 (portal de clientes) se agrega el rol Cliente; solo hay que
agregar "cliente" al CHECK CONSTRAINT de usuario_rol y al enum RolUsuario.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RolUsuario(str, enum.Enum):
    ADMIN    = "admin"
    CONTADOR = "contador"
    AUXILIAR = "auxiliar"
    # CLIENTE = "cliente"  # se habilita en Fase 3


class UsuarioRol(Base):
    """
    Tabla de roles adicionales por usuario (muchos-a-muchos con string de rol).

    Por qué no usa la FK a una tabla `rol` separada
    ─────────────────────────────────────────────────
    Con solo 3-4 roles posibles, una tabla `rol` sería over-engineering.
    El CHECK CONSTRAINT garantiza integridad referencial a nivel de BD
    sin necesitar una tabla extra. Si los roles crecen a más de 10,
    migrar a tabla `rol` es un ALTER TABLE + INSERT.

    Restricción UNIQUE (usuario_id, rol)
    ─────────────────────────────────────
    Declarada tanto aquí (UniqueConstraint en __table_args__) como en la
    migración (CONSTRAINT uq_usuario_rol). SQLAlchemy no crea el constraint
    dos veces — usa el nombre para deduplicar. La declaración aquí permite
    que las pruebas con SQLite in-memory (sin Alembic) también la respeten.
    """

    __tablename__ = "usuario_rol"
    __table_args__ = (
        CheckConstraint("rol IN ('admin', 'contador', 'auxiliar')", name="ck_usuario_rol_rol_valido"),
    )

    id:         Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    rol:        Mapped[str]       = mapped_column(String(20))
    creado_en:  Mapped[datetime]  = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación inversa
    usuario: Mapped["Usuario"] = relationship(back_populates="roles_adicionales")


class Usuario(Base):
    __tablename__ = "usuario"

    id:            Mapped[uuid.UUID]   = mapped_column(primary_key=True, default=uuid.uuid4)
    email:         Mapped[str]         = mapped_column(String(255), unique=True, index=True)
    nombre:        Mapped[str]         = mapped_column(String(150))
    password_hash: Mapped[str]         = mapped_column(String(255))
    rol:           Mapped[RolUsuario]  = mapped_column(
        Enum(
            RolUsuario,
            values_callable=lambda e: [m.value for m in e],
            create_type=False,  # el tipo lo gestiona Alembic — ver ERR-001
        ),
        default=RolUsuario.AUXILIAR,
    )
    activo:    Mapped[bool]     = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación a la tabla de roles adicionales (DT-4)
    roles_adicionales: Mapped[list[UsuarioRol]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def todos_los_roles(self) -> set[str]:
        """
        Devuelve el conjunto de todos los roles del usuario:
        el rol primario (columna `rol`) más los roles adicionales
        de la tabla `usuario_rol`.

        Uso en permisos.py:
            if rol_requerido in usuario.todos_los_roles: ...

        Por qué un set y no una lista
        ───────────────────────────────
        La verificación de permisos es `valor in colección` — O(1) con set,
        O(n) con lista. Con 3-4 roles no importa en la práctica, pero
        comunicar la intención de "sin duplicados" con un set es más claro.
        """
        base = {self.rol.value}
        adicionales = {ur.rol for ur in self.roles_adicionales}
        return base | adicionales