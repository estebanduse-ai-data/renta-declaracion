# Gestión del proyecto en GitHub

Este documento explica cómo llevar todo el backlog (`data/backlog.csv`) a GitHub Issues y a
un tablero de GitHub Projects, y cómo se trabaja el flujo día a día una vez configurado.

## 1. Configuración inicial (una sola vez)

### 1.1 Requisitos

- Tener el repositorio ya creado en GitHub (ver `README.md`, sección de arranque rápido) y
  el código de este scaffold subido con `git push`.
- Instalar [GitHub CLI](https://cli.github.com/) (`gh`) y autenticarte:

```bash
gh auth login
gh auth refresh -s project   # necesario para poder crear/editar Projects (v2)
```

### 1.2 Crear labels y milestones

```bash
cd renta-declaracion
python3 scripts/configurar_github.py <usuario>/renta-declaracion
```

Esto crea, a partir de `data/labels.csv` y `data/milestones.csv`:

- **19 labels** organizados en 4 familias: `fase:*`, `area:*`, `prioridad:*`, `tipo:*`
- **3 milestones**: Fase 1 — MVP interno, Fase 2 — Robustecimiento, Fase 3 — Portal de clientes

### 1.3 Crear todas las issues del backlog

```bash
python3 scripts/crear_issues.py <usuario>/renta-declaracion
```

Esto crea una issue por cada fila de `data/backlog.csv` (46 tareas), ya asignada a su
milestone y con sus labels correspondientes. Si quieres cargar solo una fase primero:

```bash
python3 scripts/crear_issues.py <usuario>/renta-declaracion --solo-fase "Fase 1 — MVP interno"
```

### 1.4 Crear el tablero (GitHub Projects v2)

```bash
./scripts/configurar_proyecto.sh <usuario> <usuario>/renta-declaracion
```

Esto crea el proyecto **"Renta Declaración — Roadmap"** y agrega automáticamente todas las
issues abiertas del repositorio. La primera vez, entra al tablero en GitHub y:

1. Deja la vista por defecto agrupada por el campo **Status** (columnas: Todo, In Progress, Done — puedes renombrarlas a Por hacer, En progreso, Hecho).
2. Crea una segunda vista de tipo tablero agrupada por el label `fase:*` para ver el avance por fase.
3. Crea una tercera vista de tipo tabla, filtrada por `label:prioridad:critica`, como radar de lo bloqueante.

## 2. Cómo se organiza el backlog

| Dimensión | Dónde vive | Valores |
|---|---|---|
| Fase | Milestone | Fase 1 — MVP interno · Fase 2 — Robustecimiento · Fase 3 — Portal de clientes |
| Área técnica | Label `area:*` | motor-reglas, backend, frontend, datos, seguridad, infraestructura, documentacion, qa |
| Prioridad | Label `prioridad:*` | critica, alta, media, baja |
| Tipo | Label `tipo:*` | feature, bug, deuda-tecnica, riesgo |
| Estado al momento de cargar | Columna `estado` en `data/backlog.csv` | hecho, parcial, en_progreso, pendiente |

`area:motor-reglas` es intencionalmente la más numerosa en Fase 1: es la capa de mayor
riesgo del proyecto (ver `docs/RIESGOS.md`, riesgo #1), y las issues de esa área usan la
plantilla `.github/ISSUE_TEMPLATE/regla_tributaria.md`, que obliga a documentar el
fundamento normativo y los casos de prueba antes de cerrarse.

La columna `estado` de `data/backlog.csv` refleja el avance real del código en este
repositorio al momento de cargar el backlog — no es solo planeación. `scripts/crear_issues.py`
la usa así:

- **hecho** → la issue se crea y se cierra automáticamente, con un comentario indicando que
  ya estaba resuelta (incluye la nota de qué módulo la implementa, en `nota_estado`).
- **parcial** / **en_progreso** → la issue se crea abierta, con la nota de estado en el
  cuerpo para que quien la tome sepa exactamente qué falta.
- **pendiente** → la issue se crea abierta, sin nota adicional.

Al día de esta versión, 17 de las 50 tareas del backlog ya están cerradas (12 de
`motor-reglas`, 4 de `backend`, 1 nueva de configuración administrable) y 1 está
parcial. Si sigues avanzando en local antes de cargar a GitHub, actualiza `estado` y
`nota_estado` en el CSV antes de correr el script, para que el historial de issues
nazca ya reflejando la realidad.

## 3. Flujo de trabajo día a día

1. **Tomar una issue** del tablero, moverla a "En progreso" y asignártela.
2. Crear una rama siguiendo la convención de `CONTRIBUTING.md`: `feature/<issue>-descripcion`
   o `fix/<issue>-descripcion`.
3. Al abrir el Pull Request, referenciar la issue con `Closes #<numero>` en la descripción —
   así el tablero mueve la tarjeta a "Hecho" automáticamente al hacer merge.
4. Si la issue es de `area:motor-reglas`, el PR necesita revisión funcional del contador
   antes de aprobarse (ver `CONTRIBUTING.md`).
5. Mover la tarjeta a "En revisión" al abrir el PR, y a "Hecho" cuando se mezcla.

## 4. Mantenimiento del backlog

- Nuevas tareas que surjan durante el desarrollo: crear la issue directamente en GitHub con
  la plantilla correspondiente (`tarea.md`, `regla_tributaria.md` o `bug.md`), no es
  necesario pasar por `data/backlog.csv`.
- `data/backlog.csv` queda como el registro histórico de la planeación inicial; no hace
  falta mantenerlo sincronizado con el estado real de GitHub una vez cargado.
- Si se re-prioriza una fase completa, es más simple editar los labels/milestone
  directamente en GitHub que regenerar el CSV.

## 5. Métricas sugeridas para seguimiento

- **Issues abiertas por `prioridad:critica`** dentro del milestone activo — deben tender a
  cero antes de cerrar la fase.
- **Issues de `area:motor-reglas` sin pruebas asociadas** — ninguna debería cerrarse sin
  casos de prueba (ver `CONTRIBUTING.md`).
- **Avance del milestone** (`gh issue list --milestone "Fase 1 — MVP interno" --state all`)
  como proxy simple de porcentaje de avance de la fase.

---

## 6. Plan de actividades y sincronización con GitHub Issues

### 6.1 Relación entre documentos y GitHub

El flujo de planeación tiene tres capas:

```
docs/PLAN_DE_ACTIVIDADES.md   ← fuente de verdad operativa (semana a semana)
         │
         ▼
data/backlog.csv               ← representación CSV del backlog (para los scripts)
         │
         ▼
GitHub Issues + Projects       ← tablero de trabajo diario del equipo
```

Al completar una actividad de `PLAN_DE_ACTIVIDADES.md`:
1. Actualizar `estado` en `data/backlog.csv` → `hecho` (si tiene fila correspondiente).
2. Cerrar la issue en GitHub (o crearla y cerrarla si no existía).
3. Actualizar `ESTADO_ACTUAL.md` sección "Qué existe y en qué estado".

### 6.2 Actividades nuevas sin fila en backlog.csv

Los hallazgos técnicos de la sesión 4 (Act. 0.1, 0.4, 0.5, 1.3, 1.4, 3.3, 3.4, 3.5)
no tienen fila en `data/backlog.csv` porque surgieron del análisis del código, no de
la planeación inicial. Para cargarlos a GitHub, crear las issues manualmente:

```bash
# Ejemplo: crear issue para Act. 0.1
gh issue create \
  --title "Act. 0.1 — Rotar JWT_SECRET_KEY y excluir .env de git" \
  --label "prioridad:critica,area:seguridad,fase:1" \
  --milestone "Fase 1 — MVP interno" \
  --body "El secreto JWT está commitado en backend/.env. Ver docs/PLAN_DE_ACTIVIDADES.md Act. 0.1"
```

### 6.3 Vista recomendada en GitHub Projects

Agregar una cuarta vista al tablero (además de las tres de la sección 1.4):

- **Vista "Plan de actividades"**: tipo tabla, ordenada por campo `prioridad:*` y
  filtrada por milestone activo. Permite ver de un vistazo qué actividades del plan
  están abiertas, en progreso y cerradas, en el mismo orden que `PLAN_DE_ACTIVIDADES.md`.