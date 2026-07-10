# Renta Declaración — Asistente de Declaración de Renta (Colombia)

Herramienta para automatizar el flujo de preparación de la Declaración de Renta de
Personas Naturales (Formulario 210 – DIAN), pensada inicialmente como herramienta interna
para un contador que gestiona una cartera de declarantes, con arquitectura preparada para
evolucionar a un portal de autoservicio para clientes finales.

> Estado del proyecto: **Fase 1 en curso.** Motor de reglas tributarias completo,
> backend con autenticación/CRUD/configuración administrable escrito (no ejecutado
> todavía contra una base de datos real — ver por qué en
> [`ESTADO_ACTUAL.md`](ESTADO_ACTUAL.md)), prototipo de wizard sin conectar.
>
> **👉 Si vas a retomar este proyecto — en esta sesión o en otra — lee primero
> [`ESTADO_ACTUAL.md`](ESTADO_ACTUAL.md).** Resume qué está verificado de verdad, qué
> solo se revisó por sintaxis, y los próximos pasos concretos en orden.

## Estructura del repositorio

```
.
├── backend/          API en FastAPI + motor de reglas tributarias (Python)
├── frontend/          Interfaz web (React) — wizard de captura
├── docs/              Plan de trabajo, arquitectura, riesgos, decisiones (ADR)
├── infra/             Configuración de despliegue (Nginx, etc.)
├── docker-compose.yml Orquestación local (backend + frontend + base de datos)
└── .github/workflows/ Integración continua
```

## Documentación clave

| Documento | Contenido |
|---|---|
| [`docs/PLAN_DE_TRABAJO.md`](docs/PLAN_DE_TRABAJO.md) | Fases, cronograma, alcance por hito, equipo y presupuesto estimado |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Arquitectura técnica, modelo de datos, decisiones de diseño |
| [`docs/FALTANTES.md`](docs/FALTANTES.md) | Brecha entre el prototipo actual y un producto de producción |
| [`docs/RIESGOS.md`](docs/RIESGOS.md) | Matriz de riesgos y mitigaciones |
| [`docs/adr/`](docs/adr) | Registro de decisiones de arquitectura (ADR) |

## Requisitos previos

- Docker y Docker Compose
- Python 3.11+ (desarrollo local del backend sin Docker)
- Node.js 20+ (desarrollo local del frontend sin Docker)

## Arranque rápido (entorno local)

```bash
git clone <url-del-repositorio>
cd renta-declaracion
cp backend/.env.example backend/.env
docker compose up --build
```

- Backend disponible en `http://localhost:8000` (documentación interactiva en `/docs`)
- Frontend disponible en `http://localhost:5173`

El backend aplica las migraciones de Alembic automáticamente al arrancar (ver
`backend/docker-entrypoint.sh`). Lo único que falta después de `docker compose up`
es sembrar el primer usuario Admin y los parámetros tributarios 2025:

```bash
docker compose exec backend python3 scripts/sembrar_datos_iniciales.py \
  --admin-email admin@tuempresa.com \
  --admin-password "una-clave-segura" \
  --admin-nombre "Tu Nombre"
```

Con eso ya puedes iniciar sesión en `POST /auth/login` y usar el token que devuelve
como `Bearer` para el resto de endpoints (el resto de usuarios —Contador, Auxiliar—
se crean desde `/usuarios` una vez autenticado como Admin).

## Módulo de configuración (parámetros que cambian con el tiempo)

Ningún valor normativo está fijo en el código en producción. Un usuario Admin
administra tres tipos de configuración desde `/configuracion`, cada uno con la
frecuencia de cambio real que le corresponde (ver `docs/ARQUITECTURA.md`):

| Endpoint | Qué administra | Frecuencia típica |
|---|---|---|
| `POST /configuracion/parametros-tributarios` | UVT, tabla de tarifa, topes de deducciones (vivienda, salud, dependientes), tarifas de ganancia ocasional, sanciones, anticipo, etc. — un conjunto completo por año gravable | Anual (resolución DIAN / reforma tributaria) |
| `POST /configuracion/trm` | Tasa Representativa del Mercado, un valor por fecha | Diaria |
| `POST /configuracion/tasa-interes-mora` | Tasa de interés de mora, con vigencia desde/hasta | Trimestral |

El payload de `parametros-tributarios` se valida contra `ParametrosTributariosPayload`
(`backend/app/schemas/configuracion.py`) antes de guardarse — un UVT en cero o una
tarifa de 150% se rechazan ahí mismo, no llegan a afectar el cálculo de los 200
declarantes de la cartera. Cada cambio queda en `AuditoriaCambio` con quién lo hizo.

## Desarrollo del backend sin Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Desarrollo del frontend sin Docker

```bash
cd frontend
npm install
npm run dev
```

## Gestión del proyecto (Issues, Milestones, Project board)

Todo el backlog inicial (49 tareas) vive en [`data/backlog.csv`](data/backlog.csv), listo
para cargarse a GitHub Issues y a un tablero de GitHub Projects con un par de scripts. Ver
la guía completa en [`docs/GESTION_PROYECTO.md`](docs/GESTION_PROYECTO.md).

Resumen rápido:

```bash
gh auth login
python3 scripts/configurar_github.py <usuario>/renta-declaracion   # labels + milestones
python3 scripts/crear_issues.py <usuario>/renta-declaracion        # 49 issues del backlog
./scripts/configurar_proyecto.sh <usuario> <usuario>/renta-declaracion  # tablero Project
```

## Convenciones de trabajo

- **Ramas:** `main` (estable) · `develop` (integración) · `feature/<nombre>` · `fix/<nombre>`
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- **Versionado:** [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`)
- **Parámetros tributarios** (UVT, tarifas, topes): viven únicamente en
  `backend/app/rules_engine/parametros_2025.py` — nunca hardcodeados en la lógica de negocio,
  para que la actualización anual sea un cambio de datos, no de código.

## Licencia

Pendiente de definir por el propietario del producto (ver `LICENSE`).
