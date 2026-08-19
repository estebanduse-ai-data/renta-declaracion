"""
json_encoder.py — Encoder JSON global para FastAPI.

Por qué existe este módulo
────────────────────────────
Python's `json.dumps` no sabe serializar `decimal.Decimal` ni `uuid.UUID`
de forma nativa. FastAPI usa `jsonable_encoder` internamente, pero cuando
Uvicorn serializa la respuesta final (o cuando SQLAlchemy serializa hacia
un campo JSONB en PostgreSQL), usa el encoder estándar de Python.

Tres puntos donde esto explota con el stack actual:
  1. `liquidacion_service.py` → guarda un dict con valores `Decimal` en un
     campo JSONB. PostgreSQL recibe el dict crudo; el driver psycopg2 llama
     a `json.dumps` y lanza TypeError.
  2. `RespuestaPeriodoGravable.resultado_liquidacion` → FastAPI intenta
     serializar el campo JSONB que viene de la BD. Si el dict tiene `Decimal`
     adentro (leído directamente de la columna), explota al responder.
  3. Cualquier endpoint que devuelva `Decimal` sin pasar por un schema
     Pydantic con `json_encoders` configurado.

Solución
─────────
Un encoder personalizado registrado en dos sitios:
  • `app.main` → `app = FastAPI(default_response_class=DecimalJSONResponse)`
    Cubre TODOS los endpoints sin tocar ningún router.
  • `app.db.session` → `json.dumps` con `decimal_default` para los campos
    JSONB de SQLAlchemy.

Reglas de conversión
─────────────────────
  • `Decimal`  → `str`  (string, no float — preserva precisión, la DIAN lo lee como texto)
  • `UUID`     → `str`  (ya lo maneja jsonable_encoder de FastAPI, lo incluimos por completitud)
  • `datetime` → `str`  ISO 8601 (ídem)
"""

import json
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi.responses import JSONResponse


def _default(obj):
    """Fallback del encoder para tipos no serializables por defecto."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def dumps_decimal(data) -> str:
    """
    `json.dumps` con soporte para Decimal, UUID y datetime.
    Usar en SQLAlchemy para campos JSONB:
        from app.core.json_encoder import dumps_decimal
        Column(JSONB, ...).with_variant(...).cast(...) # no — simplemente:
        periodo.resultado_liquidacion = json.loads(dumps_decimal(data))
    O mejor: pasar directamente como dict con str(Decimal) pre-convertido.
    """
    return json.dumps(data, default=_default)


class DecimalJSONResponse(JSONResponse):
    """
    JSONResponse que serializa Decimal como string.
    Se registra como default_response_class en FastAPI para cubrir
    todos los endpoints automáticamente.
    """

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            default=_default,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")