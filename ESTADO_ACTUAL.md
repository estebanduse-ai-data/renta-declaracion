# Estado actual del proyecto — léeme primero

Este documento existe para que cualquiera (tú en unas semanas, otro desarrollador, u
otra sesión de Claude sin memoria de esta conversación) pueda retomar el proyecto sin
tener que reconstruir el contexto desde cero. Se actualiza en cada entrega importante.

**Última actualización:** sesión jul-2026 — migraciones consolidadas, dependencias
completas verificadas en ambiente local, `alembic upgrade head` + `alembic check`
corriendo limpios.

---

## Historial de cambios por sesión

### Sesión 1 — Correcciones de arranque y validación del ambiente

**Problemas resueltos:**

- **`type "rolusuario" already exists`** — doble creación del ENUM PostgreSQL entre
  la migración Alembic y el evento `before_create` de SQLAlchemy. Resuelto con:
  - `create_type=False` + `values_callable=lambda e: [m.value for m in e]` en el
    modelo `Usuario`.
  - Bloque `DO $$ BEGIN CREATE TYPE … EXCEPTION WHEN duplicate_object THEN NULL;
    END $$` en `0001_inicial.py` en lugar de `checkfirst=True`.
- **`invalid input value for enum rolusuario: "ADMIN"`** — SQLAlchemy enviaba el
  nombre del miembro Python (`"ADMIN"`) en vez del valor (`"admin"`). Resuelto con
  `values_callable`.
- **`alembic check`** corrió limpio contra Postgres real — migración escrita a mano
  coincide exactamente con los modelos.
- **Setup idempotente confirmado** — todos los pasos del `setup.sh` son seguros de
  re-ejecutar; la siembra de datos verifica existencia antes de insertar.

---

### Sesión 2 — Wizard conectado a la API, panel de cartera, panel de administración y carga masiva

**Gaps del wizard corregidos:**

- **Gap 1 — Declarante ya existía (409):** al crear con un NIT ya registrado, ahora
  recupera el ID del declarante existente desde el listado filtrado por NIT.
- **Gap 2 — Periodo existente no se recuperaba:** `useEffect` carga el `periodoId`
  del año 2025 al abrir el wizard; avanzar el paso de patrimonio con periodo ya
  creado hace `PATCH` en lugar de `POST`.
- **Gap 3 — Liquidación no se persistía:** el wizard envía `periodo_id` en el
  payload; el backend guarda el resultado en `resultado_liquidacion` (JSONB) y
  responde `persistido: true`.

**Ampliaciones del wizard:**

- Patrimonio paso 2: desglose completo de activos (efectivo/bancos, inversiones,
  cuentas por cobrar, inventarios, propiedades, vehículos, otros) y pasivos (deudas
  bancarias, deudas con personas, otros pasivos). Subtotales automáticos por bloque.
  Campos de totales manuales (casillas 72/73) disponibles con prioridad sobre la suma.
- Rentas cedulares paso 3: fondo de pensiones voluntarias y AFC separados con
  subtotal y tope informativo (3.800 UVT); medicina prepagada y seguros
  complementarios separados con subtotal y tope (192 UVT); bloque de otras
  deducciones (intereses hipotecarios, ICETEX, dependientes, donaciones). Tres
  métricas al pie: total ingresos brutos, total retenciones, total deducciones.

**Backend nuevo:**

| Archivo | Qué hace |
|---|---|
| `migrations/versions/0002_resultado_liquidacion.py` | Agrega columna `resultado_liquidacion` (JSONB) a `periodo_gravable` |
| `app/models/declarante.py` | `PeriodoGravable` con campo `resultado_liquidacion` |
| `app/schemas/declarante.py` | `RespuestaPeriodoGravable` expone `resultado_liquidacion` |
| `app/api/routes_liquidacion.py` | Acepta `periodo_id` opcional; persiste resultado en BD |
| `app/api/routes_admin.py` | `GET /admin/plantilla-declarantes` y `POST /admin/importar-declarantes` |
| `app/main.py` | Registra `router_admin`; versión `0.4.0` |
| `scripts/importar_declarantes.py` | Script CLI para carga masiva inicial vía API REST |

**Nuevas dependencias instaladas:**

| Librería | Versión | Por qué |
|---|---|---|
| `openpyxl` | `3.1.5` | Leer y generar archivos `.xlsx` en `routes_admin.py` |
| `python-multipart` | `0.0.9` | Requerida por FastAPI para recibir `UploadFile` (`multipart/form-data`). Sin ella el endpoint `POST /admin/importar-declarantes` responde 422 aunque el archivo se envíe correctamente |

**Frontend nuevo:**

| Archivo | Qué hace |
|---|---|
| `frontend/src/admin/PanelAdmin.jsx` | Panel Admin: dashboard de alertas, cartera, checklist docs, importar Excel |
| `frontend/src/wizard/DeclaracionRentaWizard.jsx` | Wizard reescrito con gaps resueltos y campos ampliados |
| `frontend/src/main.jsx` | Enrutamiento por rol (Admin → PanelAdmin; Contador/Auxiliar → Cartera) |
| `frontend/src/api.js` | `importarDeclarantes()` y `descargarPlantilla()` agregadas |

---

### Sesión 3 — Consolidación de migraciones y dependencias verificadas

**Problema resuelto: `Multiple head revisions`**

Al aplicar `alembic upgrade head` apareció:
```
ERROR: Multiple head revisions are present for given argument 'head'
```

**Causa:** en algún momento anterior se ejecutó `alembic revision --autogenerate`
que generó `33827e5c8222_ajuste_post_inicial.py`. Esta migración también apuntaba a
`0001_inicial` como `down_revision`, creando dos ramas paralelas:

```
<base>
  └── 0001_inicial (branchpoint)
        ├── 0002_resultado_liquidacion  (head)   ← nuestra migración
        └── 33827e5c8222               (head)   ← generada automáticamente
```

La `33827e5c8222` ya estaba aplicada en la BD — eliminó el constraint
`uq_periodo_por_declarante_anio` de `periodo_gravable` (comportamiento correcto
para el flujo de importación masiva).

**Solución aplicada:** fusión de las dos ramas con:

```bash
alembic merge -m "merge_0002_y_ajuste_post_inicial" \
  0002_resultado_liquidacion 33827e5c8222
alembic upgrade head
```

Esto generó un archivo `xxxx_merge_0002_y_ajuste_post_inicial.py` con
`down_revision = ("0002_resultado_liquidacion", "33827e5c8222")` — sin cambios en
la BD, solo une las dos ramas en un único head.

**Cadena de migraciones resultante (estado final):**

```
<base>
  └── 0001_inicial
        ├── 0002_resultado_liquidacion
        └── 33827e5c8222
              └── xxxx_merge_0002_y_ajuste_post_inicial  ← head único
```

**Dependencia faltante descubierta en ambiente real:**

`python-multipart` no estaba en `requirements.txt`. FastAPI la necesita para
procesar `UploadFile` (multipart/form-data). Sin ella, el endpoint
`POST /admin/importar-declarantes` respondía 422 aunque el archivo se enviara
correctamente desde el frontend. Instalada con:

```bash
pip install python-multipart==0.0.9 --break-system-packages
```

Agregada a `requirements.txt` con comentario explicativo.

---

## 2. Estado actual del ambiente local

| Paso | Estado |
|---|---|
| Setup completo (`setup.sh`) | ✅ Ejecutado y validado |
| Migraciones Alembic | ✅ Un solo head, `alembic check` limpio |
| Dependencias Python | ✅ Completas incluyendo `openpyxl` y `python-multipart` |
| Dependencias Node | ✅ `npm install` ejecutado |
| Backend corriendo | ✅ `uvicorn app.main:app --reload` |
| Frontend corriendo | ✅ `npm run dev` |
| Prueba de flujo completa en wizard | ✅ Validada |
| Carga masiva desde Excel | 🔲 Pendiente prueba con Excel real del contador |

---

## 3. Qué existe y en qué estado

| Pieza | Estado | Confianza |
|---|---|---|
| Motor de reglas tributarias 2025 | Completo | Alta — 60 pruebas |
| Autenticación JWT por roles | Validado en local | Alta |
| CRUD declarantes / periodos | Validado en local | Alta |
| Migración `0001_inicial` | Aplicada | Alta |
| Migración `0002_resultado_liquidacion` | Aplicada (via merge) | Alta |
| Migración `33827e5c8222_ajuste_post_inicial` | Aplicada | Alta |
| Migración `merge_0002_y_ajuste_post_inicial` | Aplicada — head único | Alta |
| Wizard conectado a la API | Gaps resueltos, validado | Alta |
| Patrimonio desglosado | Implementado | Alta |
| Rentas cedulares ampliadas | Implementado | Alta |
| Persistencia de liquidación | Implementado (JSONB) | Alta |
| Panel de administración | Implementado | Alta |
| Carga masiva desde Excel (endpoint + CLI) | Implementado | Media — falta prueba con Excel real |
| Checklist de documentos en BD | **Pendiente** — hoy solo `localStorage` | — |
| Pruebas de paridad vs. Excel actual | **Pendiente** — bloquea producción | — |
| Reporte PDF / casillas Formulario 210 | **Pendiente** | — |

---

## 4. Próximos pasos en orden

1. Solicitar el Excel actual del contador para probar el importador con datos reales.
2. Correr la prueba de paridad declarante por declarante vs. el Excel existente.
3. Migrar el checklist de documentos de `localStorage` a BD (migración `0003`).
4. Modelar `ingreso_cedular` y `deduccion` por periodo para guardar el desglose.
5. Generar reporte de casillas del Formulario 210 (JSON → PDF o CSV).

---

## 5. Comandos de verificación del estado actual

```bash
cd renta-declaracion/backend
source .venv/bin/activate

# Migraciones
alembic current        # debe mostrar el head del merge
alembic heads          # debe mostrar un solo (head)
alembic check          # debe mostrar: No new upgrade operations detected

# Dependencias
pip show openpyxl python-multipart | grep -E "Name|Version"
# Name: openpyxl        Version: 3.1.5
# Name: python-multipart  Version: 0.0.9
```

---

## 6. Mapa de documentación

| Pregunta | Documento |
|---|---|
| ¿Cuál es el plan completo y el cronograma? | `docs/PLAN_DE_TRABAJO.md` |
| ¿Cómo está armada la arquitectura y por qué? | `docs/ARQUITECTURA.md` + `docs/adr/` |
| ¿Qué falta exactamente, con detalle y priorización? | `docs/FALTANTES.md` |
| ¿Qué puede salir mal y cómo se mitiga? | `docs/RIESGOS.md` |
| ¿Cómo cargo el backlog a GitHub Issues/Projects? | `docs/GESTION_PROYECTO.md` |
| ¿Qué archivos reemplazar y en qué orden? | `docs/GUIA_ACTUALIZACION.md` |
---

### Sesión 4 — Análisis senior y plan de actividades integrado

**Análisis realizado:**

Revisión completa del código fuente como dev senior: motor de reglas, 7 routers de API,
modelos ORM, schemas Pydantic, wizard (1 013 líneas), PanelAdmin, migraciones Alembic,
CI, pruebas unitarias y documentación existente.

**Hallazgos críticos resueltos en este documento (pendientes de implementar en código):**

| Hallazgo | Archivo afectado | Actividad |
|---|---|---|
| `JWT_SECRET_KEY` commitado en `.env` | `backend/.env` + `.gitignore` | Act. 0.1 |
| `datetime.utcnow()` deprecated Python 3.12+ | `models/usuario.py`, `models/declarante.py` | Act. 0.4 |
| `float` en lugar de `Decimal` para cálculos tributarios | `app/schemas/declarante.py` (SolicitudLiquidacion) | Act. 0.5 |
| Tabla de tarifa duplicada frontend/backend | `wizard/DeclaracionRentaWizard.jsx` | Act. 1.4 |
| `GET /declarantes` sin paginación | `api/routes_declarantes.py` | Act. 1.3 |
| Checklist en `localStorage` (no persistente) | `admin/PanelAdmin.jsx` | Act. 1.1 |

**Nuevo documento creado:**

| Documento | Ruta | Qué contiene |
|---|---|---|
| Plan de actividades | `docs/PLAN_DE_ACTIVIDADES.md` | 34 actividades priorizadas en 4 sprints (Fase 1) + Fases 2 y 3; incluye bloqueos declarados, dependencias entre actividades y referencias cruzadas a todos los docs del proyecto |

**Actualizaciones a documentos existentes en esta sesión:**

| Documento | Sección actualizada |
|---|---|
| `ESTADO_ACTUAL.md` (este archivo) | Sesión 4 agregada; tabla de próximos pasos actualizada |
| `docs/PLAN_DE_TRABAJO.md` | Sección 3 (Cronograma) — referencia al nuevo plan de actividades |
| `docs/FALTANTES.md` | Sección 5 (Priorización) — sincronizada con numeración del plan |
| `docs/GESTION_PROYECTO.md` | Sección 1.3 — instrucción de sincronizar con `PLAN_DE_ACTIVIDADES.md` |

---

## 4. Próximos pasos en orden (actualizado sesión 4)

> Ver `docs/PLAN_DE_ACTIVIDADES.md` para el detalle completo con bloqueos y dependencias.

1. **[Act. 0.1]** Rotar `JWT_SECRET_KEY` y agregar `.env` a `.gitignore` — hacer hoy.
2. **[Act. 0.2]** Reunión de paridad con el contador (mapeo hojas AY_ del Excel).
3. **[Act. 0.3]** Recibir Excel del contador y correr el importador con datos reales.
4. **[Act. 0.4 / 0.5]** Corregir `datetime.utcnow()` y `float` → `Decimal` en schemas.
5. **[Act. 1.1]** Migración 0003 — tabla `documento_checklist` en BD.
6. **[Act. 1.2]** Modelos `ingreso_cedular` y `deduccion` por periodo.
7. **[Act. 2.1]** Plan y ejecución de pruebas de paridad declarante × declarante.
8. **[Act. 2.2 / 2.3]** Backups automáticos + política de Habeas Data (bloquean producción).
9. **[Act. 3.1 / 3.2]** Mapper Formulario 210 → PDF.
10. **[Act. 4.1]** Despliegue Docker Compose en hardware definitivo del contador.

---

### Sesión 5 — Análisis de roles y navegación del wizard

**Consulta:** el wizard de declaración no era visible; se identificó la causa raíz y
se descubrió un problema estructural relacionado con el modelo de roles.

**Hallazgos registrados:**

| # | Hallazgo | Archivos afectados | Documento actualizado |
|---|---|---|---|
| 1 | El wizard no tiene URL propia — el acceso es por estado en memoria (`pantalla === "wizard"`); refrescar el navegador vuelve al login | `main.jsx` | `ARQUITECTURA.md` §6, `FALTANTES.md` §6 |
| 2 | Un usuario con rol `admin` nunca llega a la cartera ni al wizard — el dispatch en `handleLogin` es binario (`rol === "admin" ? "admin" : "cartera"`) sin salida para el admin que también liquida | `main.jsx` líneas 533 y 549, `models/usuario.py` campo `rol: Enum` | `FALTANTES.md` §6, `ARQUITECTURA.md` §6 |
| 3 | El modelo de BD no soporta múltiples roles por usuario — `usuario.rol` es un `Enum` escalar; no hay tabla de roles ni relación muchos-a-muchos | `models/usuario.py` | `ARQUITECTURA.md` §6 |
| 4 | Asimetría backend/frontend: `requiere_rol()` acepta lista de roles por endpoint pero el modelo no permite que un usuario tenga más de uno | `core/permisos.py`, `models/usuario.py` | `ARQUITECTURA.md` §6 |

**Actividades agregadas al plan:**

| Actividad | Sprint | Tipo |
|---|---|---|
| **Act. 4.6** — Botón "Ir a cartera" en `PanelAdmin` (parche admin-contador, 3 líneas) | Sprint 4 Fase 1 | Parche inmediato |
| **Act. 2F.2** (ya existía) — Permisos granulares y roles múltiples | Fase 2 | Solución estructural |

**Documentos actualizados en esta sesión:**

| Documento | Cambio |
|---|---|
| `docs/PLAN_DE_ACTIVIDADES.md` | Act. 4.6 agregada en Sprint 4; dependencia `4.6 → 2F.2` en mapa; total actualizado a 35 actividades |
| `docs/FALTANTES.md` | Fila nueva en §6: rol único bloquea al admin-contador |
| `docs/ARQUITECTURA.md` | Dos filas nuevas en §6: rol único por usuario y router por estado en memoria |
| `ESTADO_ACTUAL.md` | Esta sesión (sesión 5) |

---

## 4. Próximos pasos en orden (actualizado sesión 5)

> Ver `docs/PLAN_DE_ACTIVIDADES.md` para el detalle completo con bloqueos y dependencias.

1. **[Act. 0.1]** Rotar `JWT_SECRET_KEY` y agregar `.env` a `.gitignore` — hacer hoy.
2. **[Act. 0.2]** Reunión de paridad con el contador (mapeo hojas AY_ del Excel).
3. **[Act. 0.3]** Recibir Excel del contador y correr el importador con datos reales.
4. **[Act. 0.4 / 0.5]** Corregir `datetime.utcnow()` y `float` → `Decimal` en schemas.
5. **[Act. 4.6]** Botón "Ir a cartera" en `PanelAdmin` — desbloquea al admin en 3 líneas.
6. **[Act. 1.1]** Migración 0003 — tabla `documento_checklist` en BD.
7. **[Act. 1.2]** Modelos `ingreso_cedular` y `deduccion` por periodo.
8. **[Act. 2.1]** Plan y ejecución de pruebas de paridad declarante × declarante.
9. **[Act. 2.2 / 2.3]** Backups automáticos + política de Habeas Data (bloquean producción).
10. **[Act. 3.1 / 3.2]** Mapper Formulario 210 → PDF.
11. **[Act. 4.1]** Despliegue Docker Compose en hardware definitivo del contador.

---

### Sesión 6 — Implementación Bloque 0 + Act. 4.6 + Act. 1.2

**Actividades implementadas:**

| Act. | Título | Archivos modificados | Archivos nuevos |
|---|---|---|---|
| 0.1 | Rotar JWT + `.gitignore` | — | — (guía entregada; acción manual en servidor) |
| 0.4 | `datetime.utcnow()` → `datetime.now(timezone.utc)` | `models/usuario.py`, `models/declarante.py`, `models/auditoria.py`, `models/configuracion.py`, `api/routes_admin.py` | — |
| 0.5 | `float` → `Decimal` en schemas monetarios | `schemas/declarante.py`, `api/routes_liquidacion.py`, `api/routes_ganancias_ocasionales.py`, `api/routes_declarantes.py` | — |
| 4.6 | Botón "Ir a cartera" en PanelAdmin | `frontend/src/admin/PanelAdmin.jsx`, `frontend/src/main.jsx` | — |
| 1.2 | Modelos `ingreso_cedular` y `deduccion` + migración 0003 | `models/declarante.py`, `models/__init__.py` | `models/ingreso_deduccion.py`, `migrations/versions/0003_ingreso_cedular_y_deduccion.py` |

**Hallazgos adicionales de implementación:**

- Act. 0.4: el análisis inicial estimaba 2 archivos; la revisión del código encontró 7 instancias en 5 archivos.
- Act. 0.5: el análisis inicial estimaba 1 archivo; la revisión encontró 4 archivos afectados. Se agregó la función `_redondear(valor: float) -> Decimal` como capa de conversión entre el motor de reglas (float) y la API (Decimal).
- Act. 1.2: la migración 0003 encadena correctamente desde `4c32c83f5aa4` (el head anterior). Los ENUMs se crean explícitamente en PostgreSQL antes de las tablas y se eliminan en `downgrade()`.

**Documentos actualizados en esta sesión:**

| Documento | Cambios |
|---|---|
| `docs/PLAN_DE_ACTIVIDADES.md` | Act. 0.1, 0.4, 0.5, 1.2, 4.6 marcadas ✅; resumen ejecutivo actualizado |
| `docs/FALTANTES.md` | Hallazgos de Act. 0.4, 0.5, 4.6 marcados ✅ con nota de sesión |
| `docs/ARQUITECTURA.md` | Deuda técnica de Act. 0.5 y 4.6 marcada ✅; Act. 1.1 y 1.3 marcadas ⏳ |
| `ESTADO_ACTUAL.md` | Esta sesión (sesión 6) |
| `docs/GUIA_DE_CAMBIOS.md` | **Nuevo** — guía técnica completa de todos los cambios implementados |

---

## 4. Próximos pasos en orden (actualizado sesión 6)

> Ver `docs/PLAN_DE_ACTIVIDADES.md` para el detalle completo con bloqueos y dependencias.

1. **[Act. 0.1]** Ejecutar `openssl rand -hex 32` y actualizar `JWT_SECRET_KEY` en el servidor — acción manual.
2. **[Act. 0.2]** Reunión de paridad con el contador (mapeo hojas AY_ del Excel).
3. **[Act. 0.3]** Recibir Excel y correr el importador con datos reales.
4. **[Act. 1.1]** Migración tabla `documento_checklist` en BD — próxima implementación.
5. **[Act. 1.3]** Paginación en `GET /declarantes`.
6. **[Act. 1.4]** Tarifa desde `/configuracion` en wizard.
7. **[Act. 2.1]** Plan de pruebas de paridad declarante × declarante.
8. **[Act. 2.2 / 2.3]** Backups automáticos + política de Habeas Data.
9. **[Act. 3.1 / 3.2]** Mapper Formulario 210 → PDF.
10. **[Act. 4.1]** Despliegue Docker Compose en hardware definitivo.

---

### Sesión 7 — Sprint 1 completo: Act. 1.1, 1.3, 1.4 + fixes de migración

**Actividades implementadas:**

| Act. | Título | Archivos nuevos | Archivos modificados |
|---|---|---|---|
| 1.1 | Tabla `documento_checklist` en BD | `models/checklist.py`, `api/routes_checklist.py`, `migrations/versions/0004_documento_checklist.py` | `models/declarante.py`, `models/__init__.py`, `main.py`, `api.js`, `PanelAdmin.jsx` |
| 1.3 | Paginación `GET /declarantes` | — | `api/routes_declarantes.py`, `api.js`, `main.jsx`, `PanelAdmin.jsx` |
| 1.4 | Tarifa desde `/configuracion` en wizard | — | `api/routes_configuracion.py`, `main.py`, `api.js`, `wizard/DeclaracionRentaWizard.jsx` |

**Errores de migración encontrados y resueltos (3 iteraciones):**

Ver `docs/ERRORES_Y_LECCIONES.md` para el registro completo. Resumen:

| Error | Causa | Fix |
|---|---|---|
| `DuplicateObject: type already exists` (v1) | `sa.Enum.create(checkfirst=True)` no emite `IF NOT EXISTS` con psycopg3 | Cambiar a `DO $$ ... IF NOT EXISTS` |
| `SyntaxError: syntax error at or near "NOT"` (v2) | `CREATE TYPE IF NOT EXISTS` no existe en PostgreSQL (es sintaxis MySQL) | Reescribir con `DO $$ ... pg_type` |
| `DuplicateObject` persistente (v3) | `op.create_table()` con `sa.Enum(create_type=False)` igual emite `CREATE TYPE` propio con psycopg3 | Reemplazar toda la migración con DDL puro vía `op.execute(sa.text(...))` |

**Estado del Sprint 1 al cierre:**

| Act. | Título | Estado |
|---|---|---|
| 1.1 | Tabla `documento_checklist` en BD | ✅ |
| 1.2 | Modelos `ingreso_cedular` y `deduccion` | ✅ |
| 1.3 | Paginación `GET /declarantes` | ✅ |
| 1.4 | Tarifa desde `/configuracion` en wizard | ✅ |

**Documentos actualizados en esta sesión:**

| Documento | Cambios |
|---|---|
| `docs/PLAN_DE_ACTIVIDADES.md` | Act. 1.1, 1.3, 1.4 marcadas ✅; resumen actualizado a 9 implementadas |
| `docs/FALTANTES.md` | Hallazgo de Act. 1.4 marcado ✅ |
| `docs/ARQUITECTURA.md` | Deuda técnica de Act. 1.1 y 1.3 marcada ✅ |
| `docs/ERRORES_Y_LECCIONES.md` | **Nuevo** — registro de errores de migraciones Alembic con psycopg3 |
| `docs/GUIA_DE_CAMBIOS.md` | Act. 1.1, 1.3, 1.4 agregadas |
| `ESTADO_ACTUAL.md` | Esta sesión (sesión 7) |

---

## 4. Próximos pasos en orden (actualizado sesión 7)

> Sprint 2 — Calidad, seguridad y pruebas de paridad.

1. **[Act. 0.1]** Rotar `JWT_SECRET_KEY` en el servidor — acción manual pendiente.
2. **[Act. 0.2]** Reunión de paridad con el contador.
3. **[Act. 0.3]** Recibir Excel y correr el importador.
4. **[Act. 2.1]** Plan de pruebas de paridad declarante × declarante.
5. **[Act. 2.2]** Backups automáticos con prueba de restauración.
6. **[Act. 2.3]** Política de Habeas Data (Ley 1581).
7. **[Act. 2.4]** Pruebas de integración HTTP para los 7 routers.
8. **[Act. 2.5]** HTTPS local con certificado autofirmado.