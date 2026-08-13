# Guía de cambios implementados — renta-declaracion_app

**Última actualización:** sesión 6 — jul-2026  
**Alcance:** todas las actividades implementadas desde el análisis senior (sesiones 4–6).  
**Cómo usar este documento:** cada sección describe exactamente qué cambió, en qué archivo,
por qué, y cómo verificarlo. Para cada actividad se indica la instrucción de despliegue si aplica.

> Este documento **no reemplaza** `docs/PLAN_DE_ACTIVIDADES.md` (el qué y el orden) ni
> `ESTADO_ACTUAL.md` (el historial de sesiones). Es la referencia técnica para quien
> aplica los cambios al repositorio o revisa un PR.

---

## Estado general de implementación

| Fase | Actividad | Estado | Sesión |
|---|---|---|---|
| Bloque 0 | Act. 0.1 — Rotar JWT + `.gitignore` | ⚙️ Guía entregada (acción manual) | 6 |
| Bloque 0 | Act. 0.4 — `datetime.utcnow()` | ✅ Código aplicado | 6 |
| Bloque 0 | Act. 0.5 — `float` → `Decimal` en schemas | ✅ Código aplicado | 6 |
| Sprint 4 | Act. 4.6 — Botón "Ir a cartera" en PanelAdmin | ✅ Código aplicado | 6 |
| Sprint 1 | Act. 1.2 — Modelos `ingreso_cedular` y `deduccion` | ✅ Código aplicado | 6 |
| Sprint 1 | Act. 1.1 — Tabla `documento_checklist` | ⏳ Próxima | — |
| Sprint 1 | Act. 1.3 — Paginación `GET /declarantes` | ⏳ Próxima | — |
| Sprint 1 | Act. 1.4 — Tarifa desde `/configuracion` | ⏳ Próxima | — |

---

## Act. 0.1 — Rotar `JWT_SECRET_KEY` y asegurar `.env` fuera de git

**Problema:** `backend/.env` tenía `JWT_SECRET_KEY=cambiar-en-produccion` — un secreto
conocido públicamente. Cualquier token firmado con ese valor es falsificable.

**Estado del `.gitignore`:** la regla `.env` ya existía antes de esta sesión. El archivo
no estaba siendo rastreado por git. No se requiere `git rm --cached`.

### Acción manual requerida en el servidor

```bash
# 1. Verificar que .env no está en git (debe dar error si está bien)
git ls-files --error-unmatch backend/.env
# Esperado: error: pathspec 'backend/.env' did not match any file(s)

# 2. Generar un secreto seguro
openssl rand -hex 32
# Ejemplo de output (no usar este):
# a3f8c2e1d7b94f6a0e5c3d2b1a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0

# 3. Reemplazar en backend/.env
# Antes: JWT_SECRET_KEY=cambiar-en-produccion
# Después: JWT_SECRET_KEY=<valor generado arriba>

# 4. Reiniciar el servidor (todos los tokens anteriores quedan inválidos)
docker compose restart api
# o: uvicorn app.main:app --reload
```

### Archivos afectados

| Archivo | Acción | Va en git |
|---|---|---|
| `backend/.env` | Reemplazar valor de `JWT_SECRET_KEY` | ❌ No |
| `backend/.env.example` | Sin cambios — placeholder correcto | ✅ Sí |
| `.gitignore` | Sin cambios — regla ya existía | ✅ Sí |

---

## Act. 0.4 — `datetime.utcnow()` → `datetime.now(timezone.utc)`

**Problema:** `datetime.utcnow()` está deprecado en Python 3.12 y será error en 3.14.
El análisis inicial estimaba 2 archivos; la revisión del código encontró **7 instancias
en 5 archivos**.

### Archivos modificados

#### `backend/app/models/usuario.py`
```python
# ANTES
from datetime import datetime
creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# DESPUÉS
from datetime import datetime, timezone
creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
```

#### `backend/app/models/declarante.py`
Mismo cambio: import + `default=lambda: datetime.now(timezone.utc)`.

#### `backend/app/models/auditoria.py`
Mismo cambio: import + `default=lambda: datetime.now(timezone.utc)`.

#### `backend/app/models/configuracion.py`
Mismo cambio aplicado a **3 clases**: `ParametroTributario`, `TRMDiaria`, `TasaInteresMora`.
```python
from datetime import date, datetime, timezone  # date ya estaba
```

#### `backend/app/api/routes_admin.py`
Llamada directa (no referencia), diferente tratamiento:
```python
# ANTES
from datetime import datetime
creado_en=datetime.utcnow(),

# DESPUÉS
from datetime import datetime, timezone
creado_en=datetime.now(timezone.utc),
```

### Por qué `lambda:` en los modelos y no en `routes_admin`

En los modelos SQLAlchemy, `default=datetime.utcnow` (sin paréntesis) se evalúa
**una sola vez** al cargar el módulo. Con `lambda:` se garantiza que se evalúa en cada
inserción. En `routes_admin.py` era una llamada directa dentro de una función, por lo
que se reemplaza directamente sin lambda.

### Verificación

```bash
# Debe retornar vacío
grep -rn "utcnow" backend/

# El servidor debe arrancar sin DeprecationWarning
cd backend && uvicorn app.main:app --reload 2>&1 | grep -i deprecat
```

---

## Act. 0.5 — `float` → `Decimal` en schemas monetarios

**Problema:** los schemas de request y response usaban `float` de Python para valores
en pesos colombianos. `float` tiene errores de punto flotante IEEE 754 que son
inaceptables en cálculos tributarios presentados a la DIAN.

El análisis inicial estimaba 1 archivo; la revisión encontró **4 archivos** afectados.

### Estrategia de conversión

```
Cliente JSON  →  Schema Pydantic (Decimal)  →  Motor de reglas (float)
                                                        ↓
Cliente JSON  ←  Schema Pydantic (Decimal)  ←  _redondear() (ROUND_HALF_UP)
```

La función `_redondear()` usa `Decimal(str(valor))` (no `Decimal(valor)`) para evitar
heredar el error de representación binaria del `float`.

### Archivos modificados

#### `backend/app/schemas/declarante.py`
```python
from decimal import Decimal

# CrearPeriodoGravable y ActualizarPeriodoGravable:
patrimonio_bruto: Decimal = Field(ge=0, default=Decimal("0"), decimal_places=2)
pasivos: Decimal = Field(ge=0, default=Decimal("0"), decimal_places=2)

# RespuestaPeriodoGravable:
patrimonio_bruto: Decimal
pasivos: Decimal
```

#### `backend/app/api/routes_liquidacion.py`
- Todos los campos de `SolicitudLiquidacion` y `RespuestaLiquidacion` → `Decimal`.
- Nueva función auxiliar:
```python
from decimal import Decimal, ROUND_HALF_UP
_COP = Decimal("1")

def _redondear(valor: float) -> Decimal:
    return Decimal(str(valor)).quantize(_COP, rounding=ROUND_HALF_UP)
```
- Al persistir en JSONB, los valores se guardan como `str(decimal)` para evitar pérdida de precisión en JSON.

#### `backend/app/api/routes_ganancias_ocasionales.py`
- Todos los campos de precio/costo/valor → `Decimal`.
- `porcentaje_participacion_vendida` **se mantiene `float`** — es una proporción 0–1, no un valor en pesos.
- `tarifa_aplicada` usa 4 decimales (`Decimal("0.0001")`): es un coeficiente (ej. `0.1500`), no un monto.

#### `backend/app/api/routes_declarantes.py`
- Eliminados los `float(periodo.patrimonio_bruto)` y `float(periodo.pasivos)` explícitos en el log de auditoría.
- Reemplazados por `str(periodo.patrimonio_bruto)` — Pydantic con `Decimal` serializa correctamente.

### Lo que se dejó en `float` intencionalmente

`schemas/configuracion.py` tiene campos `float` para tarifas, porcentajes y factores
(ej. `0.35`, `0.10`). Son coeficientes normativos, no montos en pesos. Migrarlos a
`Decimal` requiere también migrar el motor de reglas — queda para Act. 3.3 (service layer).

### Verificación

```bash
# Probar que el endpoint acepta Decimal y responde Decimal (string JSON)
curl -X POST http://localhost:8000/liquidacion/calcular \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"total_ingresos_brutos_pesos": "85000000.00", "anio_gravable": 2025}'

# La respuesta debe tener valores como "12345678" (string numérico, no 12345678.0)
```

---

## Act. 4.6 — Botón "Ir a cartera" en PanelAdmin

**Problema:** un usuario con rol `admin` quedaba bloqueado en `PanelAdmin` sin ninguna
vía de acceso a la cartera ni al wizard. El dispatch de `handleLogin` era binario:
`rol === "admin" ? "admin" : "cartera"`, sin salida para el contador-administrador.

**Solución:** parche de navegación en 3 puntos del frontend. La solución estructural
(tabla `usuario_rol` muchos-a-muchos) queda para Act. 2F.2 en Fase 2.

### Archivos modificados

#### `frontend/src/admin/PanelAdmin.jsx`

**Cambio 1 — firma del componente:**
```jsx
// ANTES
export default function PanelAdmin({ sesion, onCerrarSesion }) {

// DESPUÉS
export default function PanelAdmin({ sesion, onCerrarSesion, onIrACartera }) {
```

**Cambio 2 — botón condicional en el header:**
```jsx
// En la sección de botones del header, antes de "Cerrar sesión":
{onIrACartera && (
  <button onClick={onIrACartera} style={/* mismo estilo que btnSecundario */}>
    Ir a cartera
  </button>
)}
```
El botón es condicional: si `onIrACartera` no se pasa como prop, no aparece.
Esto protege usos futuros del componente en contextos donde el admin no debe ir a cartera.

#### `frontend/src/main.jsx`

**Cambio 3 — nuevo handler y simplificación de `handleVolverAListado`:**
```jsx
// NUEVO
function handleIrACartera() {
  setPantalla("cartera");
}

// SIMPLIFICADO (antes tenía lógica condicional por rol)
function handleVolverAListado() {
  setDeclaranteActivo(null);
  setPantalla("cartera");  // siempre cartera, no depende del rol
}

// ACTUALIZADO — pasar el nuevo prop
if (pantalla === "admin") return (
  <PanelAdmin
    sesion={sesion}
    onCerrarSesion={handleCerrarSesion}
    onIrACartera={handleIrACartera}  // ← nuevo
  />
);
```

### Flujo completo post-cambio

```
Login (rol admin)
  → PanelAdmin  [header: "Ir a cartera" | "Cerrar sesión"]
       │
       └── "Ir a cartera"
                → PantallaCartera
                     │
                     └── clic declarante → Wizard
                                               │
                                               └── onVolver() → PantallaCartera ✓
```

### Por qué `handleVolverAListado` va siempre a `"cartera"`

Antes iba a `"admin"` si el rol era admin: el admin llegaba al wizard (desde la cartera,
por el nuevo botón), terminaba, y volvía al panel admin en lugar de la cartera.
Ahora el flujo es coherente: `cartera → wizard → cartera`, sin importar el rol.

---

## Act. 1.2 — Modelos `ingreso_cedular` y `deduccion` + migración 0003

**Problema:** el wizard enviaba totales consolidados al endpoint `/liquidacion/calcular`.
No era posible recalcular sin volver a capturar, ver el desglose por rubro, ni construir
el mapper del Formulario 210 (Act. 3.1) que necesita valores desagregados por casilla.

### Archivos nuevos

#### `backend/app/models/ingreso_deduccion.py`

Contiene dos enums y dos modelos ORM:

**`TipoIngresoCedular`** — 17 valores que cubren:
- Cédula general (art. 330 E.T.): salarios, honorarios, servicios, comisiones, rendimientos, arrendamientos, regalías, explotación de imagen, compensaciones.
- Cédula de pensiones (art. 337 E.T.): pensiones nacionales y extranjeras.
- Cédula de dividendos (art. 342 E.T.): gravados y no gravados.
- Ingresos no constitutivos, rentas exentas (laboral, cesantías, otro).

**`TipoDeduccion`** — 9 valores: intereses vivienda, ICETEX, medicina prepagada, dependientes, AFC, pensión voluntaria, donaciones, GMF, otra.

**`IngresoCedular`** — campos:
```
id (UUID PK) | periodo_id (FK CASCADE) | tipo (ENUM) | monto_pesos (Numeric 18,2) | descripcion | creado_en
```

**`Deduccion`** — campos:
```
id (UUID PK) | periodo_id (FK CASCADE) | tipo (ENUM) | monto_informado_pesos | monto_efectivo_pesos | tope_aplicado (bool) | tope_valor_pesos | descripcion | creado_en
```

> La separación `monto_informado_pesos` / `monto_efectivo_pesos` en `Deduccion` es
> trazabilidad obligatoria: el contador y la DIAN pueden ver qué informó el contribuyente
> y qué recortó el motor de reglas al tope normativo.

#### `backend/migrations/versions/0003_ingreso_cedular_y_deduccion.py`

- **`down_revision`:** `4c32c83f5aa4` (el head antes de esta migración).
- Crea los tipos ENUM en PostgreSQL **antes** de las tablas (`checkfirst=True`).
- `downgrade()` elimina tablas primero, luego los ENUMs.
- Las FKs usan `ondelete="CASCADE"` para que al eliminar un `PeriodoGravable` se
  eliminen automáticamente sus ingresos y deducciones.

### Archivos modificados

#### `backend/app/models/declarante.py`
```python
# Relaciones agregadas en PeriodoGravable:
ingresos_cedulares: Mapped[list["IngresoCedular"]] = relationship(
    back_populates="periodo",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
deducciones: Mapped[list["Deduccion"]] = relationship(
    back_populates="periodo",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
```

#### `backend/app/models/__init__.py`
```python
# Línea agregada al final:
from app.models.ingreso_deduccion import IngresoCedular, Deduccion  # noqa: F401
```

### Patrón de uso en el wizard (para Act. 3.3 — service layer)

Al recalcular, el LiquidacionService debe:
```python
# 1. Limpiar los rubros anteriores del periodo
db.query(IngresoCedular).filter_by(periodo_id=periodo_id).delete()
db.query(Deduccion).filter_by(periodo_id=periodo_id).delete()

# 2. Insertar los nuevos rubros desde el body del wizard
for rubro in solicitud.ingresos:
    db.add(IngresoCedular(periodo_id=periodo_id, tipo=rubro.tipo, monto_pesos=rubro.monto))
for ded in solicitud.deducciones:
    db.add(Deduccion(periodo_id=periodo_id, tipo=ded.tipo,
                     monto_informado_pesos=ded.monto,
                     monto_efectivo_pesos=min(ded.monto, tope),
                     tope_aplicado=ded.monto > tope))

# 3. Correr el motor de reglas con los totales calculados
resultado = liquidar(...)
```

### Aplicar la migración

```bash
cd backend
alembic upgrade head
# Output esperado:
# Running upgrade 4c32c83f5aa4 -> 0003_ingreso_cedular_y_deduccion

# Verificar en PostgreSQL:
psql -d renta_declaracion -c "\dt ingreso_cedular"
psql -d renta_declaracion -c "\dt deduccion"
psql -d renta_declaracion -c "\dT tipoingresocedular"
psql -d renta_declaracion -c "\dT tipodeduccion"
```

### Rollback si es necesario

```bash
alembic downgrade 4c32c83f5aa4
# Elimina las tablas ingreso_cedular y deduccion y sus ENUMs
```

---

## Cadena de migraciones actualizada

```
0001_inicial
    └──▶ 33827e5c8222_ajuste_post_inicial ──┐
    └──▶ 0002_resultado_liquidacion ─────────┤
                                             ▼
                              4c32c83f5aa4_merge_0002_y_ajuste
                                             │
                                             ▼
                       0003_ingreso_cedular_y_deduccion  ← HEAD actual
```

---

## Checklist de despliegue (orden obligatorio)

```
[ ] 1. Reemplazar JWT_SECRET_KEY en backend/.env (Act. 0.1)
[ ] 2. Copiar archivos de backend modificados al servidor:
        backend/app/models/usuario.py
        backend/app/models/declarante.py
        backend/app/models/auditoria.py
        backend/app/models/configuracion.py
        backend/app/api/routes_admin.py
        backend/app/schemas/declarante.py
        backend/app/api/routes_liquidacion.py
        backend/app/api/routes_ganancias_ocasionales.py
        backend/app/api/routes_declarantes.py
        backend/app/models/ingreso_deduccion.py       ← NUEVO
        backend/app/models/__init__.py
        backend/migrations/versions/0003_ingreso_cedular_y_deduccion.py  ← NUEVO
[ ] 3. Copiar archivos de frontend modificados:
        frontend/src/admin/PanelAdmin.jsx
        frontend/src/main.jsx
[ ] 4. Ejecutar la migración: cd backend && alembic upgrade head
[ ] 5. Reconstruir el frontend: cd frontend && npm run build
[ ] 6. Reiniciar el servicio API
[ ] 7. Verificar: login como admin → botón "Ir a cartera" visible ✓
[ ] 8. Verificar: curl al endpoint /liquidacion/calcular devuelve Decimal (no float) ✓
[ ] 9. Verificar: grep -rn "utcnow" backend/ → vacío ✓
```

---

## Referencias cruzadas

| Documento | Relación |
|---|---|
| `docs/PLAN_DE_ACTIVIDADES.md` | Estado ✅ actualizado para Act. 0.1, 0.4, 0.5, 1.2, 4.6 |
| `docs/FALTANTES.md` §6 | Hallazgos resueltos marcados ✅ |
| `docs/ARQUITECTURA.md` §6 | Deuda técnica resuelta marcada ✅ |
| `ESTADO_ACTUAL.md` sesión 6 | Tabla de actividades implementadas |
| `data/backlog.csv` | Actualizar `estado` → `hecho` para las 5 actividades |

---

## Act. 1.1 — Tabla `documento_checklist` en BD

**Problema:** el estado del checklist vivía en `localStorage` del navegador — se perdía
al limpiar el caché, era invisible para otros usuarios y no tenía auditoría.

### Archivos nuevos

| Archivo | Ruta |
|---|---|
| `checklist.py` | `backend/app/models/checklist.py` |
| `routes_checklist.py` | `backend/app/api/routes_checklist.py` |
| `0004_documento_checklist.py` | `backend/migrations/versions/0004_documento_checklist.py` |

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `models/declarante.py` | Relación `checklist` agregada a `PeriodoGravable` (`cascade=delete-orphan`) |
| `models/__init__.py` | Registro de `DocumentoChecklist` y `TipoDocumento` |
| `main.py` | Import y registro de `router_checklist`; versión `0.4.0 → 0.5.0` |
| `api.js` | Funciones `obtenerChecklist()` y `toggleDocumento()` agregadas |
| `PanelAdmin.jsx` | `localStorage` reemplazado; `cargarTodo` y `toggleDoc` ahora async contra API |

### Endpoints nuevos

```
GET  /declarantes/{did}/periodos/{pid}/checklist        → RespuestaChecklist
PATCH /declarantes/{did}/periodos/{pid}/checklist/{tipo} → ItemChecklist
```

### Nota: migración requirió DDL puro (ver ERR-001)

`op.create_table()` con `sa.Enum(create_type=False)` ignora ese flag con psycopg3
y emite un `CREATE TYPE` adicional. La migración 0004 usa `op.execute(sa.text(...))`
puro para todo el DDL. Ver `docs/ERRORES_Y_LECCIONES.md ERR-001`.

### Aplicar

```bash
alembic upgrade head
# Running upgrade 0003 -> 0004_documento_checklist
```

---

## Act. 1.3 — Paginación en `GET /declarantes`

**Problema:** `db.query(Declarante).all()` cargaba todos los declarantes a memoria
en cada request. Con 200 declarantes funciona; con 2000 colapsa.

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `api/routes_declarantes.py` | Nuevo schema `RespuestaListaDeclarantes { total, skip, limit, items }`; query con `count()` + `offset()` + `limit()`; filtro `busqueda` por apellido o NIT |
| `api.js` | `listarDeclarantes(token, { skip, limit, busqueda })` — acepta opciones de paginación |
| `main.jsx` | Consume `resp.items ?? resp` (compatibilidad defensiva) |
| `PanelAdmin.jsx` | Fetch directo actualizado a `?limit=500`; consume `decResp.items ?? decResp` |

### Compatibilidad

El `?? resp` en ambos frontends garantiza que si el backend aún no está actualizado,
la app sigue funcionando con el array plano. Eliminar ese fallback en Sprint 2
cuando la actualización esté confirmada en producción.

### Verificación

```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/declarantes?skip=0&limit=10&busqueda=garcia"
# { "total": 5, "skip": 0, "limit": 10, "items": [...] }
```

---

## Act. 1.4 — Tarifa tributaria desde `/configuracion` en el wizard

**Problema:** `TABLA_TARIFA_DISPLAY` y `UVT_2025_FALLBACK` en el wizard
eran constantes hardcodeadas que duplicaban `parametros_2025.py` del backend.
Al actualizar los parámetros para 2026 habría que editar dos lugares.

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `api/routes_configuracion.py` | Nuevo `router_publico` con `GET /configuracion/parametros-publicos/{anio}` accesible por Admin, Contador y Auxiliar |
| `main.py` | Import y registro de `router_configuracion_publico` |
| `api.js` | Nueva función `obtenerParametrosPublicos(token, anio)` |
| `wizard/DeclaracionRentaWizard.jsx` | Constantes eliminadas; estado `parametros` cargado en `useEffect` al montar; fallback a `PARAMETROS_FALLBACK` si la API falla |

### Endpoint nuevo

```
GET /configuracion/parametros-publicos/{anio}
→ { anio, uvt, tabla_tarifa_uvt, porcentaje_renta_exenta_laboral,
    tope_renta_exenta_laboral_uvt, limite_renta_exenta_deducciones_porcentaje,
    tope_renta_exenta_deducciones_uvt }
```

**Acceso:** `ADMIN | CONTADOR | AUXILIAR` (el endpoint de admin `/parametros-tributarios/{anio}` sigue siendo solo ADMIN).

### Patrón de fallback en el wizard

```js
// Se inicializa con fallback, se sobreescribe desde la API al montar
const [parametros, setParametros] = useState(PARAMETROS_FALLBACK);
useEffect(() => {
  obtenerParametrosPublicos(sesion.token, ANIO_GRAVABLE)
    .then(p => setParametros(p))
    .catch(() => console.warn("Usando parámetros fallback"));
}, [sesion.token]);
```

El wizard **nunca bloquea** la carga si la API de parámetros falla — muestra
los valores fallback y sigue funcionando. El cálculo real lo hace el backend.

---

## Estado general — cierre Sprint 1

| # | Act. | Estado | Sesión |
|---|---|---|---|
| 1 | 0.1 Rotar JWT | ⚙️ Guía entregada | 6 |
| 2 | 0.4 datetime.utcnow | ✅ | 6 |
| 3 | 0.5 float → Decimal | ✅ | 6 |
| 4 | 4.6 Botón "Ir a cartera" | ✅ | 6 |
| 5 | 1.2 Modelos ingreso/deduccion | ✅ | 6 |
| 6 | 1.1 Checklist en BD | ✅ | 7 |
| 7 | 1.3 Paginación declarantes | ✅ | 7 |
| 8 | 1.4 Tarifa desde API | ✅ | 7 |

**Siguiente:** Sprint 2 — Act. 2.1 (pruebas de paridad), 2.2 (backups), 2.3 (Habeas Data), 2.4 (tests de integración), 2.5 (HTTPS).