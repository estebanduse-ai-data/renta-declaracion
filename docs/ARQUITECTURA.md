# Arquitectura técnica

## 1. Vista general

Arquitectura en tres capas independientes, para que la interfaz del contador (Fase 1) y el
futuro portal de clientes (Fase 3) compartan el mismo motor de cálculo y la misma API, sin
duplicar lógica de negocio.

```
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   Frontend — Panel Admin     │   │  Frontend — Panel Contador  │
│   src/admin/PanelAdmin.jsx   │   │  src/main.jsx (Cartera)     │
│   (solo rol Admin)           │   │  src/wizard/Wizard.jsx      │
└──────────────┬───────────────┘   └──────────────┬───────────────┘
               │                                    │
               └──────────────────┬─────────────────┘
                                   │  HTTP REST (JSON)
                        ┌──────────▼───────────┐
                        │   API — FastAPI       │
                        │   /auth  /usuarios    │
                        │   /declarantes        │
                        │   /liquidacion        │
                        │   /admin              │
                        │   /configuracion      │
                        └──────────┬────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                                     │
      ┌──────────▼───────────┐          ┌─────────────▼─────────────┐
      │  Motor de reglas      │          │   Base de datos            │
      │  tributarias (Python) │          │   PostgreSQL                │
      │  — puro, sin estado   │          │   declarante               │
      │  — parametrizado      │          │   periodo_gravable          │
      └────────────────────────┘          │   usuario                   │
                                          │   parametro_tributario      │
                                          │   trm_diaria                │
                                          │   tasa_interes_mora         │
                                          │   auditoria_cambio          │
                                          └─────────────────────────┘
```

## 2. Componentes

### 2.1 Motor de reglas tributarias (`backend/app/rules_engine`)
Funciones puras (sin efectos secundarios, sin acceso a BD) que replican las fórmulas del
Formulario 210: UVT, tabla progresiva art. 241 E.T., renta presuntiva, límite del 40% de
rentas exentas y deducciones, sanciones, intereses, anticipo, compensaciones, moneda
extranjera. 60 pruebas unitarias ejecutadas.

Los parámetros de cada año gravable viven en un módulo de datos separado
(`parametros_2025.py`) — actualizar el año solo implica agregar un nuevo archivo.

### 2.2 API (`backend/app/api`)

| Router | Prefijo | Roles autorizados |
|---|---|---|
| `routes_auth.py` | `/auth` | Público (login) |
| `routes_usuarios.py` | `/usuarios` | Admin |
| `routes_declarantes.py` | `/declarantes` | Admin, Contador, Auxiliar |
| `routes_liquidacion.py` | `/liquidacion` | Admin, Contador, Auxiliar |
| `routes_configuracion.py` | `/configuracion` | Admin |
| `routes_admin.py` | `/admin` | Admin exclusivo |
| `routes_ganancias_ocasionales.py` | `/ganancias-ocasionales` | Admin, Contador, Auxiliar |

`routes_admin.py` expone dos endpoints:
- `GET /admin/plantilla-declarantes` — descarga la plantilla Excel estándar.
- `POST /admin/importar-declarantes` — carga masiva desde `.xlsx`; valida fila a fila,
  crea `Declarante` y opcionalmente `PeriodoGravable` 2025 si hay datos de patrimonio,
  registra auditoría por cada registro importado.

### 2.3 Base de datos (PostgreSQL)

| Tabla | Propósito | Novedades v0.4 |
|---|---|---|
| `usuario` | Email, hash bcrypt, rol (admin/contador/auxiliar) | ENUM `rolusuario` con `create_type=False` + `values_callable` |
| `declarante` | NIT, nombre, actividad económica, contador asignado | — |
| `periodo_gravable` | Año, estado, patrimonio bruto/pasivos, resultado liquidación | Nueva columna `resultado_liquidacion` (JSONB) — migración `0002` |
| `parametro_tributario` | JSON versionado por año con todos los parámetros tributarios | — |
| `trm_diaria` | Serie de tiempo diaria TRM | — |
| `tasa_interes_mora` | Vigencias desde/hasta, tasa certificada | — |
| `auditoria_cambio` | Quién cambió qué y cuándo, con valores anteriores/nuevos | Ahora incluye acción `importar_masivo` |

**Pendiente próxima iteración:** tabla `documento_checklist` (hoy en `localStorage`),
modelos `ingreso_cedular` y `deduccion` por periodo.

### 2.4 Frontend (`frontend/src`)

```
src/
├── main.jsx                  App root — enrutamiento por rol
│                             Admin → PanelAdmin
│                             Contador/Auxiliar → PantallaCartera → Wizard
├── api.js                    Cliente HTTP centralizado (fetch + manejo de errores)
├── admin/
│   └── PanelAdmin.jsx        Panel exclusivo Admin: dashboard, cartera,
│                             checklist docs, importar Excel
└── wizard/
    └── DeclaracionRentaWizard.jsx   Wizard de captura paso a paso
```

El wizard no contiene lógica tributaria propia — usa cálculos locales solo para
feedback inmediato en pantalla; el valor que se persiste siempre viene del backend.

## 3. Decisiones de diseño clave

1. **El backend es la única fuente de verdad del cálculo tributario.** El frontend
   puede mostrar cálculos preliminares para feedback inmediato, pero el resultado que
   se persiste siempre viene del endpoint `/liquidacion/calcular`.

2. **Parámetros tributarios como datos, no como código.** Cada año gravable es un
   registro nuevo en `parametro_tributario`, nunca una modificación de fórmulas.

3. **Multi-año desde el día uno.** El modelo soporta histórico completo por declarante,
   necesario para renta presuntiva, anticipo y comparación patrimonial.

4. **El ENUM `rolusuario` lo gestiona la migración, no el ORM.** `create_type=False`
   en el modelo evita que SQLAlchemy intente crearlo automáticamente al hacer
   `CREATE TABLE`, lo que causaba `DuplicateObject` en re-ejecuciones del setup.

5. **La persistencia de la liquidación es opcional y no destructiva.** El endpoint
   acepta `periodo_id` de forma opcional; si se provee y el estado del periodo no es
   `presentado`, sobreescribe `resultado_liquidacion`. Si el periodo ya fue presentado,
   el campo no se toca — el resultado histórico queda inmutable.

6. **Importación masiva con auditoría por registro.** Cada declarante importado genera
   un registro en `auditoria_cambio` con `accion = "importar_masivo"` y el nombre del
   archivo de origen, lo que permite reconstruir qué llegó de dónde.

7. **Enrutamiento por rol en el frontend.** Al hacer login, si el rol es `admin` la app
   va directamente a `PanelAdmin`; si es `contador` o `auxiliar`, va a `PantallaCartera`.
   Ambas vistas comparten el wizard de declaración.

8. **El motor de reglas nunca importa SQLAlchemy.** El servicio de parámetros hace los
   imports de forma diferida para que el motor se pueda probar sin el ORM instalado.

## 4. Flujo de datos — liquidación con persistencia

```
Wizard (paso 5)
  │  POST /liquidacion/calcular
  │  { ...inputs, periodo_id: "uuid" }
  ▼
routes_liquidacion.py
  │  obtener_parametros_vigentes(db, 2025)
  │  liquidar(inputs, parametros)
  │  if periodo_id and estado != "presentado":
  │      periodo.resultado_liquidacion = { resultado }
  │      db.commit()
  │      respuesta.persistido = True
  ▼
Wizard muestra resultado + badge "guardado en BD"
```

## 5. Ver también
- [`docs/adr/0001-arquitectura-tres-capas.md`](adr/0001-arquitectura-tres-capas.md)
- [`docs/adr/0002-configuracion-administrable.md`](adr/0002-configuracion-administrable.md)
- [`docs/FALTANTES.md`](FALTANTES.md)
- [`docs/RIESGOS.md`](RIESGOS.md)
---

## 6. Deuda técnica conocida y plan de resolución

Esta sección documenta las decisiones de implementación que deben evolucionar antes
de que el sistema escale. Ver `docs/PLAN_DE_ACTIVIDADES.md` para la actividad asignada.

| Deuda | Estado actual | Estado objetivo | Actividad |
|---|---|---|---|
| Lógica de negocio en routers | Validaciones y upserts directamente en `routes_*.py` | `DeclaranteService` y `LiquidacionService` en `app/services/` | Act. 3.3 |
| Wizard monolítico (1013 líneas) | Un solo componente con múltiples `useState` | `PatrimonioStep`, `IngresosStep`, `LiquidacionStep` con estado local | Act. 3.5 |
| Schemas sin capa para liquidación | `routes_liquidacion.py` usa modelos ORM directamente | `schemas/liquidacion.py` con request/response Pydantic separados | Sprint 3 |
| ✅ `float` en cálculos monetarios | `SolicitudLiquidacion` acepta `float` de Python | `Decimal` en schemas; función `_redondear()` con `ROUND_HALF_UP` — **resuelto sesión 6** | Act. 0.5 |
| ✅ Checklist en `localStorage` | Datos de UI guardados en el navegador | Tabla `documento_checklist` en PostgreSQL + `routes_checklist.py` + API en `api.js` — **resuelto sesión 7** | Act. 1.1 |
| ✅ Sin paginación en listado de declarantes | `db.query(Declarante).all()` cargaba todo a memoria | `RespuestaListaDeclarantes` paginada con `count()` + `offset()` + `limit()` + filtro `busqueda` — **resuelto sesión 7** | Act. 1.3 |
| ✅ (parche) / ⏳ (estructural) Rol único por usuario (`Enum` escalar en BD) | `usuario.rol` es un solo valor; un `admin` no puede acceder a la cartera ni al wizard | Parche: botón "Ir a cartera" en `PanelAdmin` — **resuelto sesión 6**. Estructural: tabla `usuario_rol` muchos-a-muchos en Act. 2F.2 | Act. 4.6 ✅ → Act. 2F.2 ⏳ |
| Router de navegación por estado en memoria | `pantalla` y `declaranteActivo` en `useState` de `App`; refrescar el navegador vuelve al login; el admin no puede navegar al wizard por URL | Migrar a `react-router-dom` con rutas reales (`/cartera`, `/declarantes/:id/wizard`, `/admin`) | Act. 4.3 (login) → Sprint posterior |