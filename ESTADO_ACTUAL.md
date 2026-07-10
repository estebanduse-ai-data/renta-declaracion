# Estado actual del proyecto — léeme primero

Este documento existe para que cualquiera (tú en unas semanas, otro desarrollador, u
otra sesión de Claude sin memoria de esta conversación) pueda retomar el proyecto sin
tener que reconstruir el contexto desde cero. Se actualiza en cada entrega importante;
si no lo has tocado en tu último commit, probablemente deberías.

**Última actualización:** tag `v0.5.0-backend-configuracion`.

## 1. Restricción importante del entorno en que se construyó esto

Todo este repositorio se escribió en un entorno de desarrollo **sin acceso a red**. Eso
tiene una consecuencia concreta que cualquiera que siga debe saber:

- **El motor de reglas tributarias** (`backend/app/rules_engine/`) es Python puro sin
  dependencias externas, así que **sí se ejecutó y se verificó de verdad**: sus 60
  pruebas unitarias corrieron con un runner manual (sin pytest instalado) y todas
  pasan. Confianza alta.
- **El resto del backend** (FastAPI, SQLAlchemy, Alembic, Pydantic, passlib, jose)
  **nunca se ejecutó**, porque esas librerías no se pudieron instalar sin red. Todo se
  verificó únicamente con `python3 -m py_compile` (sintaxis correcta) y, en las partes
  más críticas, con revisión manual cuidadosa. Confianza media — sintácticamente
  correcto, pero **nadie ha levantado la API todavía contra una base de datos real.**

**Primer paso obligatorio en cualquier entorno con red**, antes de construir nada
encima de esto:

```bash
cd backend
pip install -r requirements.txt
pytest -v                     # confirma que el motor de reglas + esquemas + adaptador
                               # pasan de verdad, no solo que compilan
docker compose up --build     # desde la raíz del repo, para probar la API completa
```

Si `pytest -v` o el arranque de Docker fallan, es la primera vez que ese código corre
de verdad — trátalo como el punto de partida de la siguiente sesión de trabajo, no
como un bug inesperado.

## 2. Gotchas ya encontrados y corregidos (para no repetirlos)

Estos tres se encontraron por revisión manual, sin poder ejecutar el código. Vale la
pena que quien siga sepa que existieron, por si algo similar se coló sin detectar:

1. **`UniqueConstraint("anio", "activo")` en `ParametroTributario`** habría bloqueado
   tener más de un registro histórico inactivo por año, rompiendo el propósito de
   conservar el historial. Se corrigió con un índice único **parcial** (solo sobre
   `activo=true`) — ver `backend/app/models/configuracion.py` y ADR 0002.
2. **`requirements.txt` pineaba `pydantic` dos veces** (`pydantic==2.9.2` y
   `pydantic[email]==2.9.2` como líneas separadas) — inofensivo para pip pero
   redundante y confuso. Se unificó en una sola línea.
3. **`passlib[bcrypt]==1.7.4` sin pinear `bcrypt`** — passlib 1.7.4 tiene una
   incompatibilidad conocida con `bcrypt>=4.1` (lee un atributo `__about__` que se
   eliminó en versiones nuevas de `bcrypt`, y lanza error al hashear contraseñas). Se
   fijó `bcrypt==4.0.1` explícitamente.
4. **`docker-compose.yml` apuntaba `env_file` a `backend/.env.example`** en vez de
   `backend/.env` — la instrucción del README de copiar el archivo no tenía ningún
   efecto real, porque Docker seguía leyendo el `.example` sin importar qué hubiera en
   `.env`. Corregido.

Ninguno de estos se habría detectado sin ejecutar el código de verdad — es la razón
por la que el paso 1 de esta sección no es opcional.

## 3. Qué existe y en qué estado (resumen ejecutivo)

| Pieza | Estado | Confianza |
|---|---|---|
| Motor de reglas tributarias 2025 (liquidación, ganancias ocasionales, dividendos, deducciones, descuentos, sanciones, anticipo, compensaciones, moneda extranjera) | Completo para Fase 1 | Alta — 60 pruebas ejecutadas de verdad |
| Adaptador `ParametrosVigentes` (traduce BD ↔ motor de reglas) | Completo | Alta — verificado manualmente, produce resultados idénticos al módulo estático |
| Autenticación (JWT, roles) | Escrito | Media — no ejecutado |
| CRUD declarantes/periodos | Escrito | Media — no ejecutado |
| Módulo de configuración (parámetros anuales, TRM, tasa de mora) | Escrito | Media — no ejecutado |
| Migraciones Alembic | Escrita a mano (no autogenerada) | Media-baja — correr `alembic check` contra Postgres real antes de confiar en ella |
| Persistencia del resultado de liquidación | **No existe todavía** | — |
| Wizard (frontend) | Prototipo navegable, sin conectar a la API | — |
| Carga masiva desde Excel | **No existe todavía** | — |
| Panel de cartera del contador | **No existe todavía** | — |
| Pruebas de paridad contra el Excel actual | **No existe todavía** — es el paso más importante antes de decomisionar el Excel (ver `docs/RIESGOS.md`) | — |

## 4. Próximos pasos recomendados, en orden

1. **Ejecutar el paso 1 de este documento** en un entorno con red — validar que todo
   lo escrito realmente funciona antes de seguir agregando encima.
2. Si `alembic upgrade head` falla contra Postgres real, corregir la migración a mano
   o regenerarla con `alembic revision --autogenerate` una vez el modelo esté probado.
3. Persistencia del cálculo: modelos de `ingreso_cedular` y `deduccion` por periodo, y
   que `/liquidacion/calcular` guarde su resultado en vez de solo devolverlo.
4. Conectar el wizard (`frontend/src/wizard/DeclaracionRentaWizard.jsx`) a la API real
   — hoy sigue funcionando con estado local del prototipo.
5. Carga masiva desde el Excel actual + panel de cartera del contador.
6. Pruebas de paridad declarante por declarante contra el Excel — sin esto no debería
   presentarse ninguna declaración real con el sistema nuevo (ver `docs/RIESGOS.md`,
   riesgo #9).

## 5. Mapa de documentación (qué leer según la pregunta)

| Pregunta | Documento |
|---|---|
| ¿Cuál es el plan completo y el cronograma? | `docs/PLAN_DE_TRABAJO.md` |
| ¿Cómo está armada la arquitectura y por qué? | `docs/ARQUITECTURA.md` + `docs/adr/` |
| ¿Qué falta exactamente, con detalle? | `docs/FALTANTES.md` |
| ¿Qué puede salir mal y cómo se mitiga? | `docs/RIESGOS.md` |
| ¿Cómo cargo el backlog a GitHub Issues/Projects? | `docs/GESTION_PROYECTO.md` |
| ¿Qué tareas están hechas vs. pendientes, en detalle? | `data/backlog.csv` (columna `estado`) |
| ¿Qué pasó en cada entrega? | `git log --oneline --tags` — cada tag tiene un mensaje de commit largo explicando el porqué, no solo el qué |
