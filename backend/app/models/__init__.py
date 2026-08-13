"""
Importa todos los modelos para que se registren en `Base.metadata` — necesario
para que Alembic los detecte al generar migraciones y para que
`Base.metadata.create_all()` funcione en entornos de prueba con SQLite.
"""

from app.models.declarante import Declarante, PeriodoGravable  # noqa: F401
from app.models.usuario import Usuario, RolUsuario  # noqa: F401
from app.models.configuracion import ParametroTributario, TRMDiaria, TasaInteresMora  # noqa: F401
from app.models.auditoria import AuditoriaCambio  # noqa: F401
from app.models.ingreso_deduccion import IngresoCedular, Deduccion  # noqa: F401  — Act. 1.2
from app.models.checklist import DocumentoChecklist, TipoDocumento  # noqa: F401  — Act. 1.1