# Portfolio Plan — Renta Declaración

**Objetivo:** llevar el proyecto a GitHub como portafolio profesional que demuestre arquitectura de software, dominio tributario colombiano, y calidad de ingeniería de producción.

---

## Estado de preparación

### ✅ Ya en producción técnica

| Área | Evidencia concreta |
|---|---|
| Motor de reglas puro (Decimal) | 88 pruebas unitarias, 0 dependencias de BD |
| Arquitectura en 3 capas | ADR documentados, service layer separado |
| Migraciones versionadas | Alembic, single head, `alembic check` limpio |
| CI/CD | GitHub Actions: pytest + npm build en cada push |
| Serialización robusta | `DecimalJSONResponse` global + `dumps_decimal` en engine |
| Roles y JWT | `requiere_rol()` en cada endpoint, multi-rol en BD |
| Auditoría completa | `auditoria_cambio` con JSONB en cada escritura |
| Docker Compose | Setup completo en un comando |

### ✅ Limpiezas de portafolio aplicadas en este commit

| Problema | Fix |
|---|---|
| `0002 resultado liquidacion.py` — espacio en nombre | Renombrado a `0002_resultado_liquidacion.py` |
| `POSTGRES_PASSWORD: renta` hardcodeado | Migrado a `${POSTGRES_PASSWORD:-renta}` |
| `data/` con CSVs de backlog interno | Eliminado del repo |
| `scripts/configurar_github.py` y scripts de gestión | Eliminados |
| `ESTADO_ACTUAL.md` con referencias a cliente real | Reemplazado por `CHANGELOG.md` estándar |
| `docs/FALTANTES.md` | Renombrado a `docs/ROADMAP.md` |
| `docs/Plan de actividades.md` con espacio | Renombrado a `docs/PLAN_DE_ACTIVIDADES.md` |
| `LICENSE` pendiente de definir | MIT |
| Versión `0.1.0` en `package.json` vs `0.6.0` en `main.py` | Alineado a `0.6.0` |
| README orientado a uso interno | Reescrito para portafolio en inglés |

---

## Estructura del portafolio en GitHub

```
renta-declaracion/
├── README.md                ← landing del repo: problema, stack, demo, tests
├── CHANGELOG.md             ← historial técnico por versión
├── CONTRIBUTING.md          ← flujo de ramas y PR
├── LICENSE                  ← MIT
├── docker-compose.yml       ← setup completo
│
├── backend/
│   ├── app/
│   │   ├── rules_engine/    ← ⭐ el diferenciador técnico del proyecto
│   │   ├── core/
│   │   │   └── json_encoder.py   ← Decimal global, sin magia oculta
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   └── schemas/
│   ├── migrations/          ← historial completo de esquema
│   └── tests/               ← 88 pruebas, sin BD requerida
│
├── frontend/
│   └── src/
│       ├── wizard/          ← flujo guiado paso a paso
│       └── admin/           ← panel de administración
│
└── docs/
    ├── ARQUITECTURA.md
    ├── ROADMAP.md
    ├── PLAN_DE_ACTIVIDADES.md
    ├── RIESGOS.md
    └── adr/                 ← decisiones de arquitectura documentadas
```

---

## Qué demuestra el proyecto a un evaluador técnico

### 1. Precisión numérica para dominio financiero

```python
# MAL — lo que haría un junior
resultado = ingreso * 0.25

# BIEN — lo que hace este proyecto
resultado = ingreso * Decimal("0.25")
```

Toda la codebase opera con `Decimal` desde la entrada HTTP (Pydantic schema) hasta la salida a PostgreSQL (JSONB con `dumps_decimal`). 10 bugs encontrados y corregidos metódicamente.

### 2. Separación real de responsabilidades

```
HTTP request → Router (validación) → Service (orquestación) → Rules Engine (cálculo puro)
                                   ↘ Repository (persistencia)
```

El motor de reglas **nunca importa SQLAlchemy**. Se puede probar, auditar y reusar sin levantar ningún servicio.

### 3. Parámetros como datos, no como código

```python
# En vez de esto — hardcoded en lógica
if ingreso > 4000 * uvt:
    tarifa = 0.35

# El proyecto hace esto — parametrizado en BD
P = obtener_parametros_vigentes(db, anio_gravable)
impuesto = calcular_impuesto_uvt(base_uvt, P.TABLA_TARIFA_UVT)
```

El Admin actualiza la UVT, la tabla de tarifas o cualquier tope desde la UI. No hay redeployment para el año siguiente.

### 4. Trazabilidad completa de cambios

Cada escritura genera un registro en `auditoria_cambio` con el usuario, la acción, y los valores anteriores y nuevos en JSONB. Funciona incluso en importaciones masivas.

### 5. Manejo de errores de serialización en profundidad

`Decimal` no es serializable por `json.dumps` estándar. El proyecto resuelve esto en **tres capas**:

```python
# Capa 1: respuesta HTTP (FastAPI)
app = FastAPI(default_response_class=DecimalJSONResponse)

# Capa 2: JSONB en PostgreSQL (psycopg2)
engine = create_engine(url, json_serializer=dumps_decimal)

# Capa 3: dicts de auditoría
datos_auditoria = {k: str(v) if isinstance(v, Decimal) else v for k, v in datos.items()}
```

---

## Roadmap del proyecto (próximos pasos)

Ver [`docs/ROADMAP.md`](ROADMAP.md) para el detalle completo.

### Sprint 2 — Calidad y paridad (prioridad actual)
- [ ] Pruebas de paridad vs. Excel de referencia (bloquea uso en producción)
- [ ] Suite de pruebas de integración HTTP para los 7 routers
- [ ] Backups automáticos con prueba de restauración
- [ ] HTTPS con certificado autofirmado en ambiente local

### Sprint 3 — Producto
- [ ] PDF mapper: Formulario 210 completo con todas las casillas
- [ ] Historial de versiones por declaración (borrador / presentado / corrección)
- [ ] Refresh token (sesión de 60 min interrumpe el wizard en declaraciones complejas)
- [ ] Fuente automática de TRM (API Banco de la República)

### Fase 2 — Plataforma
- [ ] Roles múltiples por usuario (tabla `usuario_rol` M2M — estructura ya en BD)
- [ ] React Router con rutas reales (`/declarantes/:id/wizard`)
- [ ] Logs estructurados y observabilidad
- [ ] Política Habeas Data (Ley 1581) — obligatoria para datos de declarantes

### Fase 3 — Portal de autoservicio
- [ ] Onboarding de declarantes directamente (sin intermediario contador)
- [ ] Módulo de comunicaciones (notificaciones de vencimientos DIAN)
- [ ] API pública con autenticación OAuth2

---

## Cómo ejecutar el proyecto

```bash
git clone https://github.com/YOUR_USER/renta-declaracion.git
cd renta-declaracion

# Configurar variables de entorno
cp backend/.env.example backend/.env
# Editar JWT_SECRET_KEY en backend/.env

# Levantar todo
bash scripts/setup.sh

# Tests
cd backend && pytest -v
# 88 passed in 0.24s
```

- **API + Swagger UI:** `http://localhost:8000/docs`
- **Frontend:** `http://localhost:5173`

---

## Decisiones técnicas destacadas

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| `Decimal` en todo, nunca `float` | `float` con redondeo al final | Error de representación IEEE 754 acumulado en cálculos tributarios — inaceptable ante la DIAN |
| Motor de reglas sin efectos secundarios | Calcular en el service | Permite probar cada regla tributaria de forma aislada, sin BD ni HTTP |
| Parámetros en BD, no en código | `if anio == 2025: uvt = 49799` | El Admin actualiza sin redeployment; soporta multi-año en la misma instancia |
| `json_serializer` en el engine SQLAlchemy | `str()` en cada asignación | Un solo punto de control para todos los campos JSONB; imposible olvidarlo |
| `DecimalJSONResponse` como `default_response_class` | `json_encoders` en cada schema | Cubre todos los endpoints sin anotación adicional en 16+ schemas |
| DDL puro en migraciones Alembic para ENUMs | `sa.Enum` con `checkfirst=True` | psycopg3 no respeta `checkfirst` — la alternativa con `DO $$ ... pg_type` es portable |
