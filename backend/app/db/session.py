"""
session.py — Sesión SQLAlchemy con soporte nativo para Decimal en JSONB.

Cambio en fix/decimal-float-type-errors
─────────────────────────────────────────
El engine usa `json_serializer` personalizado para que los campos JSONB
(AuditoriaCambio.valores_nuevos, PeriodoGravable.resultado_liquidacion, etc.)
serialicen Decimal como str en vez de lanzar TypeError.

Por qué aquí y no en cada asignación
──────────────────────────────────────
psycopg2 (driver de PostgreSQL) llama internamente a `json.dumps` cuando
detecta que el valor de una columna JSONB es un dict de Python. Configuar
el serializer en el engine es la única forma de interceptar esa serialización
sin tener que envolver cada asignación `modelo.campo_jsonb = {...}` con una
conversión manual.

Alternativa descartada: convertir todos los Decimal a str antes de asignar
al campo. Funciona, pero es frágil — cualquier futuro código que olvide la
conversión rompe silenciosamente en producción.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.json_encoder import dumps_decimal

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    json_serializer=dumps_decimal,   # JSONB → Decimal serializable
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()