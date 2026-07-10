"""
Usuarios y roles — control de acceso por rol (Admin, Contador, Auxiliar).

En Fase 3 (portal de clientes) se agrega el rol Cliente; el modelo ya queda
preparado para eso sin necesidad de migración estructural (solo agregar el
valor al enum).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RolUsuario(str, enum.Enum):
    ADMIN = "admin"
    CONTADOR = "contador"
    AUXILIAR = "auxiliar"
    # CLIENTE = "cliente"  # se habilita en Fase 3, ver docs/PLAN_DE_TRABAJO.md


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[RolUsuario] = mapped_column(Enum(RolUsuario), default=RolUsuario.AUXILIAR)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
