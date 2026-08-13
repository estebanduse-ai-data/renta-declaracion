# Renta Declaración — Asistente de Declaración de Renta (Colombia)

Herramienta para automatizar el flujo de preparación de la Declaración de Renta de
Personas Naturales (Formulario 210 – DIAN), pensada inicialmente como herramienta
interna para un contador que gestiona una cartera de declarantes, con arquitectura
preparada para evolucionar a un portal de autoservicio para clientes finales.

> **Estado del proyecto:** Fase 1 en curso — ambiente local validado, wizard conectado
> a la API, panel de administración y carga masiva implementados. Motor de reglas
> tributarias con 60 pruebas unitarias. Pendiente: pruebas de paridad vs. Excel actual
> y migración de los 200 declarantes.
>
> **👉 Si vas a retomar este proyecto — en esta sesión o en otra — lee primero
> [`ESTADO_ACTUAL.md`](ESTADO_ACTUAL.md).** Resume qué está verificado, qué cambió en
> cada sesión y los próximos pasos concretos en orden.

---

## Estructura del repositorio

```
.
├── backend/
│   ├── app/
│   │   ├── api/            Endpoints REST (auth, usuarios, declarantes,
│   │   │                   liquidacion, configuracion, admin)
│   │   ├── core/           Seguridad, permisos, configuración
│   │   ├── db/             Sesión SQLAlchemy, base declarativa
│   │   ├── models/         Modelos ORM (declarante, usuario, configuracion, auditoria)
│   │   ├── rules_engine/   Motor de reglas tributarias — funciones puras
│   │   ├── schemas/        Schemas Pydantic de entrada/salida
│   │   └── services/       Servicios (parámetros vigentes, auditoría)
│   ├── migrations/         Alembic — versiones de esquema de BD
│   ├── scripts/            Scripts CLI (sembrar datos, importar declarantes)
│   └── tests/              Pruebas unitarias del motor de reglas
├── frontend/
│   └── src/
│       ├── main.jsx        App root — enrutamiento por rol
│       ├── api.js          Cliente HTTP centralizado
│       ├── admin/          Panel de administración (solo rol Admin)
│       └── wizard/         Wizard de captura paso a paso
├── docs/                   Plan de trabajo, arquitectura, riesgos, ADR
├── data/                   Backlog CSV, labels, milestones
├── infra/                  Configuración de despliegue (Nginx, etc.)
├── docker-compose.yml
└── scripts/setup.sh        Setup completo del ambiente local
```

---

## Documentación clave

| Documento | Contenido |
|---|---|
| [`ESTADO_ACTUAL.md`](ESTADO_ACTUAL.md) | Estado real del proyecto, cambios por sesión, próximos pasos |
| [`docs/PLAN_DE_TRABAJO.md`](docs/PLAN_DE_TRABAJO.md) | Fases, cronograma, alcance, equipo y presupuesto |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Arquitectura técnica, modelo de datos, decisiones de diseño |
| [`docs/FALTANTES.md`](docs/FALTANTES.md) | Brecha entre el estado actual y producción, priorización |
| [`docs/RIESGOS.md`](docs/RIESGOS.md) | Matriz de riesgos y mitigaciones |
| [`docs/adr/`](docs/adr) | Registro de decisiones de arquitectura (ADR) |

---

## Requisitos previos

- Docker y Docker Compose
- Python 3.11+ (desarrollo local del backend)
- Node.js 20+ (desarrollo local del frontend)

---

## Arranque rápido (ambiente local)

```bash
git clone <url-del-repositorio>
cd renta-declaracion
bash scripts/setup.sh
```

El script hace todo: crea el contenedor de PostgreSQL, instala dependencias Python y
Node, copia `.env`, aplica migraciones Alembic, ejecuta pytest y siembra el usuario
Admin y los parámetros tributarios 2025.

Si el setup ya fue ejecutado antes (idempotente — se puede volver a correr):

```bash
cd backend
alembic upgrade head   # aplica migraciones nuevas si las hay
```

- **Backend:** `http://localhost:8000` (documentación interactiva en `/docs`)
- **Frontend:** `http://localhost:5173`

---

## Acceso inicial

Tras el setup, iniciar sesión con las credenciales configuradas en `backend/.env`
(campo `ADMIN_EMAIL` / `ADMIN_PASSWORD`). El rol Admin accede al panel de
administración; los roles Contador y Auxiliar acceden al panel de cartera y al wizard.

---

## Carga masiva de declarantes

**Opción A — Desde la app (recomendada):**
1. Iniciar sesión como Admin.
2. Ir a la pestaña **Importar Excel** del panel de administración.
3. Descargar la plantilla, completarla y adjuntarla.

**Opción B — Script CLI (carga inicial o lotes grandes):**

```bash
# Obtener token Admin
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresa.com","password":"clave"}' | jq -r .access_token)

# Importar
cd backend
python scripts/importar_declarantes.py ../data/declarantes.xlsx --token "$TOKEN"
```

La plantilla estándar tiene estas columnas:

| Columna | Obligatorio |
|---|---|
| `nit` | ✅ |
| `digito_verificacion` | ✅ |
| `primer_apellido` | ✅ |
| `primer_nombre` | ✅ |
| `actividad_economica` (`empleado` / `independiente` / `rentista` / `otro`) | ✅ |
| `patrimonio_bruto_2025` | No |
| `pasivos_2025` | No |
| `patrimonio_bruto_2024` | No |
| `pasivos_2024` | No |

Los NIT ya registrados se omiten sin error — la importación es acumulativa y segura.

---

## Módulo de configuración

Ningún valor normativo está fijo en el código. Un usuario Admin administra desde
`/configuracion`:

| Endpoint | Qué administra | Frecuencia |
|---|---|---|
| `POST /configuracion/parametros-tributarios` | UVT, tabla de tarifa, topes (vivienda, salud, dependientes), sanciones, anticipo… | Anual |
| `POST /configuracion/trm` | Tasa Representativa del Mercado | Diaria |
| `POST /configuracion/tasa-interes-mora` | Tasa de mora certificada por la Superintendencia Financiera | Trimestral |

---

## Desarrollo sin Docker

```bash
# Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

---

## Gestión del proyecto (GitHub Issues + Projects)

```bash
gh auth login
python3 scripts/configurar_github.py <usuario>/renta-declaracion
python3 scripts/crear_issues.py <usuario>/renta-declaracion
./scripts/configurar_proyecto.sh <usuario> <usuario>/renta-declaracion
```

Ver guía completa en [`docs/GESTION_PROYECTO.md`](docs/GESTION_PROYECTO.md).

---

## Convenciones de trabajo

- **Ramas:** `main` (estable) · `develop` (integración) · `feature/<nombre>` · `fix/<nombre>`
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- **Versionado:** Semantic Versioning (`MAJOR.MINOR.PATCH`) — versión actual `0.4.0`
- **Parámetros tributarios:** solo en `backend/app/rules_engine/parametros_2025.py`;
  nunca hardcodeados en lógica de negocio.

---

## Licencia

Pendiente de definir por el propietario del producto.