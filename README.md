# Renta Declaración — Asistente de Declaración de Renta (Colombia)

Herramienta para automatizar el flujo de preparación de la Declaración de Renta de
Personas Naturales (Formulario 210 – DIAN), pensada inicialmente como herramienta interna
para un contador que gestiona una cartera de declarantes, con arquitectura preparada para
evolucionar a un portal de autoservicio para clientes finales.

> Estado del proyecto: **Fase 0 — Fundacional.** Este repositorio contiene la arquitectura
> base, el motor de reglas tributarias y el prototipo de interfaz (wizard). Ver
> [`docs/PLAN_DE_TRABAJO.md`](docs/PLAN_DE_TRABAJO.md) para el roadmap completo.

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
