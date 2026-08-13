# Errores encontrados y lecciones aprendidas

**Propósito:** registro técnico de errores reales ocurridos durante el desarrollo,
con causa raíz, fix aplicado y regla derivada. Evita repetir los mismos errores
en migraciones futuras y sirve de referencia para nuevos desarrolladores.

> Actualizar este documento cada vez que un error requiera más de un intento de fix.
> La fecha y la sesión en que ocurrió permiten rastrear el contexto.

---

## ERR-001 — Migraciones Alembic: creación de ENUMs con psycopg3

**Sesión:** 7 (jul-2026)
**Migraciones afectadas:** `0003_ingreso_cedular_y_deduccion`, `0004_documento_checklist`
**Stack:** Python 3.13 · SQLAlchemy 2.x · Alembic · psycopg 3.x · PostgreSQL 16

### Cronología de intentos

#### Intento 1 — `sa.Enum.create(checkfirst=True)`

```python
# Lo que se escribió (v1)
tipo = sa.Enum(*VALORES, name="tipoingresocedular")
tipo.create(op.get_bind(), checkfirst=True)
```

**Error:**
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.DuplicateObject)
type "tipoingresocedular" already exists
```

**Causa:** con psycopg3, `sa.Enum.create(checkfirst=True)` ejecuta una consulta
de introspección a `pg_type` en una conexión/transacción separada que no refleja
el estado actual, y luego emite `CREATE TYPE` sin `IF NOT EXISTS`. El resultado
es que en una segunda ejecución (después de un fallo parcial) el tipo ya existe
y la migración falla.

---

#### Intento 2 — `CREATE TYPE IF NOT EXISTS` (SQL directo)

```python
# Lo que se escribió (v2)
conn.execute(sa.text(
    "CREATE TYPE IF NOT EXISTS tipoingresocedular AS ENUM (...)"
))
```

**Error:**
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.SyntaxError)
syntax error at or near "NOT"
LINE 1: CREATE TYPE IF NOT EXISTS tipoingresocedular ...
```

**Causa:** `CREATE TYPE IF NOT EXISTS` **no existe en PostgreSQL**. Es sintaxis
de MySQL que nunca fue portada a PostgreSQL. El manual de PostgreSQL solo define
`CREATE TYPE nombre AS ENUM (...)` sin cláusula `IF NOT EXISTS`.

---

#### Intento 3 — `DO $$ ... IF NOT EXISTS` (v3) — funcionó parcialmente

```python
# Lo que se escribió (v3)
op.execute(sa.text("""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipoingresocedular') THEN
            CREATE TYPE tipoingresocedular AS ENUM (...);
        END IF;
    END $$
"""))
# Pero la tabla se creaba con op.create_table() usando sa.Enum(create_type=False)
op.create_table("ingreso_cedular",
    sa.Column("tipo", sa.Enum(*VALORES, name="tipoingresocedular", create_type=False), ...),
    ...
)
```

**Error:** el mismo `DuplicateObject` de antes.

**Causa:** con psycopg3 + SQLAlchemy 2.x, `op.create_table()` con una columna
`sa.Enum(..., create_type=False)` **ignora `create_type=False`** y emite su propio
`CREATE TYPE` adicional antes de crear la tabla. El `DO $$` anterior funcionaba,
pero SQLAlchemy generaba un segundo `CREATE TYPE` por su cuenta al procesar
`op.create_table`.

---

#### Intento 4 — DDL 100% puro via `op.execute()` ✅

```python
# Fix definitivo (v4)
def upgrade() -> None:
    # 1. ENUM idempotente con DO $$
    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipoingresocedular') THEN
                CREATE TYPE tipoingresocedular AS ENUM (...);
            END IF;
        END $$
    """))

    # 2. Tabla con DDL puro — sin op.create_table(), sin sa.Enum
    op.execute(sa.text("""
        CREATE TABLE ingreso_cedular (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            periodo_id UUID NOT NULL REFERENCES periodo_gravable(id) ON DELETE CASCADE,
            tipo       tipoingresocedular NOT NULL,
            ...
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX ix_ingreso_cedular_periodo_id ON ingreso_cedular (periodo_id)"
    ))

def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS ingreso_cedular"))
    op.execute(sa.text("DROP TYPE IF EXISTS tipoingresocedular"))
    # Nota: DROP TYPE IF EXISTS SÍ existe en PostgreSQL (a diferencia de CREATE)
```

**Por qué funciona:** al usar `op.execute(sa.text(...))` SQLAlchemy solo envía
el SQL exacto al servidor sin interpretarlo. No hay introspección, no hay emisión
automática de `CREATE TYPE`. El control es total.

---

### Regla derivada — migraciones con ENUMs en PostgreSQL + psycopg3

> **Regla ERR-001:** en proyectos con SQLAlchemy 2.x + psycopg3 + Alembic,
> **nunca usar `sa.Enum` ni `op.create_table()` para crear ENUMs**.
> Usar siempre DDL puro con `op.execute(sa.text(...))` para toda la migración.

Checklist para migraciones con ENUMs:

```python
# ✅ Correcto — todo DDL puro
def upgrade() -> None:
    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mienum') THEN
                CREATE TYPE mienum AS ENUM ('val1', 'val2');
            END IF;
        END $$
    """))
    op.execute(sa.text("""
        CREATE TABLE mitabla (
            id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tipo mienum NOT NULL
        )
    """))

def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS mitabla"))
    op.execute(sa.text("DROP TYPE IF EXISTS mienum"))

# ❌ Incorrecto — causa DuplicateObject con psycopg3
def upgrade() -> None:
    sa.Enum('val1', 'val2', name='mienum').create(op.get_bind(), checkfirst=True)
    op.create_table('mitabla',
        sa.Column('tipo', sa.Enum('val1', 'val2', name='mienum', create_type=False)),
    )
```

### Estado de la BD al fallar la migración parcialmente

Cuando una migración falla a mitad, Alembic **no revierte** los DDL ejecutados
antes del error (PostgreSQL no soporta DDL transaccional para `CREATE TYPE`).
El resultado es una BD en estado inconsistente:

```
✅ tipoingresocedular ENUM creado
✅ tipodeduccion ENUM creado
❌ tabla ingreso_cedular NO creada (fallo aquí)
❌ tabla deduccion NO creada
❌ alembic_version NO actualizada (sigue en la revisión anterior)
```

**Procedimiento de limpieza antes de reintentar:**

```bash
# 1. Verificar estado Alembic
alembic current
# Debe mostrar la revisión anterior, no la fallida

# 2. Limpiar residuos en PostgreSQL
psql -d renta_declaracion -c "DROP TYPE IF EXISTS tipoingresocedular CASCADE;"
psql -d renta_declaracion -c "DROP TYPE IF EXISTS tipodeduccion CASCADE;"
psql -d renta_declaracion -c "DROP TYPE IF EXISTS tipodocumento CASCADE;"

# 3. Reemplazar el archivo de migración con el fix y ejecutar
alembic upgrade head
```

---

## ERR-002 — Import incorrecto: `obtener_usuario_actual` en `routes_checklist.py`

**Sesión:** 7 (jul-2026)
**Archivo afectado:** `backend/app/api/routes_checklist.py`

### Error

```
ImportError: cannot import name 'obtener_usuario_actual'
from 'app.core.security'
```

### Causa

`obtener_usuario_actual` está definida en `app.core.permisos`, no en
`app.core.security`. La separación de responsabilidades es:

| Módulo | Contenido |
|---|---|
| `app.core.security` | Utilidades JWT puras: `crear_token_acceso()`, `decodificar_token_acceso()`, `hashear_password()`. Sin dependencias de FastAPI. |
| `app.core.permisos` | Dependencies de FastAPI: `obtener_usuario_actual`, `requiere_rol()`. Dependen de `Depends`, `get_db`, y `security`. |

### Fix

```python
# ❌ Incorrecto
from app.core.permisos import requiere_rol
from app.core.security import obtener_usuario_actual

# ✅ Correcto
from app.core.permisos import requiere_rol, obtener_usuario_actual
```

### Regla derivada — ERR-002

> En este proyecto, **todos los `Depends(...)` de autenticación y autorización
> vienen de `app.core.permisos`**, no de `app.core.security`.
> `security.py` no importa FastAPI y no tiene ningún `Depends`.

---

## Plantilla para nuevos errores

```markdown
## ERR-XXX — Título descriptivo del error

**Sesión:** N (mes-año)
**Archivo(s) afectado(s):** ruta/al/archivo.py

### Error
\`\`\`
Traceback o mensaje de error exacto
\`\`\`

### Causa
Explicación de la causa raíz.

### Fix
\`\`\`python
# ❌ Incorrecto
...
# ✅ Correcto
...
\`\`\`

### Regla derivada
> Regla concisa para evitar repetir el error.
```