# Plan de actividades — renta-declaracion_app

**Última actualización:** jul-2026 — plan generado tras análisis senior del estado del
proyecto (sesiones 1-3). Integra el backlog de `data/backlog.csv`, los faltantes de
`docs/FALTANTES.md` y las recomendaciones de arquitectura derivadas del análisis del
código fuente.

> **Cómo usar este documento:**
> - Es la fuente de verdad operativa semana a semana, complemento del cronograma
>   estratégico de `docs/PLAN_DE_TRABAJO.md`.
> - Cada actividad tiene su área, prioridad y bloqueos declarados explícitamente.
> - Marcar una actividad como completada implica actualizar también `data/backlog.csv`
>   (`estado` → `hecho`) y `ESTADO_ACTUAL.md` (sección "Qué existe y en qué estado").
> - Las actividades con 🔒 **bloquea producción** no son negociables antes de poner
>   datos reales de clientes en el sistema.

---

## Resumen ejecutivo

| Indicador | Valor |
|---|---|
| Actividades totales (3 fases) | 35 |
| Críticas / bloqueantes Fase 1 | 12 |
| Implementadas (sesiones 4-7) | 9 — Act. 0.1 (guía), 0.4, 0.5, 4.6, 1.2, 1.1, 1.3, 1.4 + 3 fixes de migración |
| Pendientes Fase 1 | 26 |
| Fecha objetivo MVP (Fase 1) | +14 semanas desde inicio del proyecto |

---

## Fase 1 — MVP interno (prioridad inmediata)

### Semana 0 — Desbloqueos críticos (hacer antes de cualquier dato real)

Estas cinco actividades no esperan sprint. Son correcciones de seguridad y
alineamiento con el experto tributario que desbloquean todo lo demás.

| # | Actividad | Área | Prioridad | Bloquea |
|---|---|---|---|---|
| 0.1 | ✅ **Rotar `JWT_SECRET_KEY` y excluir `.env` de git** — el secreto está commitado en el repositorio. Guía entregada sesión 6: `.env` ya estaba en `.gitignore`; reemplazar `cambiar-en-produccion` con `openssl rand -hex 32` en el servidor. | Seguridad | 🔴 Crítica | Confidencialidad de sesiones activas |
| 0.2 | **Reunión de paridad con el contador — mapeo hojas AY_ del Excel** — sesión de trabajo presencial o remota para documentar todos los casos especiales que el contador ya maneja hoy en el archivo. Sin esto, el motor de reglas no puede validarse contra la realidad. | Definición funcional | 🔴 Crítica 🔒 | Validación del motor de reglas |
| 0.3 | **Recibir el Excel actual del contador y correr el importador** — prueba del endpoint `POST /admin/importar-declarantes` con los ~200 declarantes reales; documentar discrepancias de columnas. | Datos | 🔴 Crítica 🔒 | Migración de los 200 declarantes |
| 0.4 | ✅ **Corregir `datetime.utcnow()` → `datetime.now(timezone.utc)`** — implementado sesión 6. Corregidas 7 instancias en 5 archivos: `models/usuario.py`, `models/declarante.py`, `models/auditoria.py`, `models/configuracion.py` (×3), `api/routes_admin.py`. | Backend | 🟠 Alta | Compatibilidad futura |
| 0.5 | ✅ **Reemplazar `float` por `Decimal` en schemas monetarios** — implementado sesión 6. Afectaba 4 archivos: `schemas/declarante.py`, `api/routes_liquidacion.py`, `api/routes_ganancias_ocasionales.py`, `api/routes_declarantes.py`. Función `_redondear()` como capa de conversión al motor de reglas. | Backend | 🟠 Alta | Precisión de cálculos |

---

### Sprint 1 — Persistencia y datos completos (sem 1–2)

Objetivo: que el sistema guarde toda la información de una declaración, no solo totales.

| # | Actividad | Área | Prioridad | Bloquea |
|---|---|---|---|---|
| 1.1 | ✅ **Migración 0003: tabla `documento_checklist` en BD** — sacar el checklist de `localStorage`. Estructura: `(id, periodo_id FK, tipo_documento, estado ENUM, usuario_id FK, actualizado_en)`. Incluye endpoint CRUD y actualización del frontend. | Backend + Frontend | 🔴 Crítica 🔒 | Confiabilidad del checklist entre equipos/navegadores |
| 1.2 | ✅ **Modelos `ingreso_cedular` y `deduccion` por periodo** — implementado sesión 6. Nuevos: `models/ingreso_deduccion.py` (enums `TipoIngresoCedular` 17 valores + `TipoDeduccion` 9 valores, modelos ORM con `cascade=delete-orphan`), migración `0003_ingreso_cedular_y_deduccion.py`, relaciones en `declarante.py`, registro en `models/__init__.py`. | Backend | 🔴 Crítica 🔒 | Recálculo sin re-captura; historial |
| 1.3 | ✅ **Paginación en `GET /declarantes`** — `db.query(Declarante).all()` carga todo a memoria. Agregar `?skip=0&limit=50` antes de que la cartera crezca. Impacto: una línea en el router, una en el schema. | Backend | 🟠 Alta | Escalabilidad con más de 200 declarantes |
| 1.4 | ✅ **Eliminar tabla de tarifa hardcodeada del wizard** — `TABLA_TARIFA_DISPLAY` en el wizard duplica `parametros_2025.py`. El frontend debe leer la tabla del endpoint `GET /configuracion`. | Frontend | 🟠 Alta | Consistencia al actualizar parámetros |
| 1.5 | **Completar descuentos tributarios art. 255 y 256 E.T.** — el módulo `descuentos_tributarios.py` cubre donaciones (art. 257) y el límite conjunto del 30% (art. 259). Faltan los descuentos de investigación y energías renovables de los art. 255/256. | Motor de reglas | 🟠 Alta | Declarantes con estos conceptos |

---

### Sprint 2 — Calidad, seguridad y pruebas de paridad (sem 3–4)

Objetivo: que el sistema sea confiable y auditable antes de cualquier dato real de cliente.

| # | Actividad | Área | Prioridad | Bloquea |
|---|---|---|---|---|
| 2.1 | **Plan de pruebas de paridad declarante × declarante vs Excel** — diseñar y ejecutar la comparación del motor de reglas contra el Excel del contador, caso por caso. Documentar variaciones y resolverlas. **Regla dura: ninguna declaración se presenta a la DIAN hasta pasar esta fase** (ver `docs/RIESGOS.md` riesgo #9). | QA | 🔴 Crítica 🔒 | Presentar cualquier declaración real |
| 2.2 | **Configurar backups automáticos diarios con prueba de restauración** — sin backup verificado no hay producción con datos reales. Usar `pg_dump` en cron + copia a ubicación externa cifrada. Documentar el procedimiento de restauración y probarlo. Mitiga riesgo #3 de `RIESGOS.md`. | Infraestructura | 🔴 Crítica 🔒 | Operación en producción |
| 2.3 | **Formalizar política de Habeas Data (Ley 1581/2012)** — obligatorio por el volumen de datos personales sensibles de ~200 declarantes. Documento firmado por el responsable del tratamiento antes de cargar cualquier dato real. Mitiga riesgo #6 de `RIESGOS.md`. | Seguridad / Legal | 🔴 Crítica 🔒 | Cargar datos reales de clientes |
| 2.4 | **Pruebas de integración HTTP para los 7 routers** — `httpx` y `TestClient` ya están disponibles. Un test de ciclo completo por router: login → crear declarante → calcular → verificar en BD. Meta: cobertura API del ~40% actual al ~80%. | QA | 🟠 Alta | Regresiones silenciosas |
| 2.5 | **Configurar HTTPS local con certificado autofirmado** — aplica incluso en red interna. Usar `mkcert` para desarrollo; `certbot` o certificado propio para producción. Mitiga riesgo #6. | Seguridad | 🟠 Alta | Confidencialidad en tránsito |

---

### Sprint 3 — Formulario 210 y refactoring (sem 5–6)

Objetivo: generar el entregable más visible para el contador y mejorar la mantenibilidad del código.

| # | Actividad | Área | Prioridad | Bloquea |
|---|---|---|---|---|
| 3.1 | **Mapper resultado → casillas Formulario 210** — el JSONB de `resultado_liquidacion` ya existe. Implementar `mapper_formulario210(resultado) → {casilla_N: valor}` y el endpoint `GET /declarantes/{id}/periodos/{pid}/formulario-210` que devuelve el JSON estructurado. | Backend | 🟠 Alta | Transcripción a SIE DIAN |
| 3.2 | **Generación de PDF del Formulario 210** — a partir del mapper anterior, generar el PDF con `weasyprint` o `reportlab`. Es el entregable de mayor valor visible para el contador: el documento que entrega al cliente. | Backend | 🟠 Alta | Entrega al cliente declarante |
| 3.3 | **Extraer `DeclaranteService` y `LiquidacionService`** — la lógica de negocio (validación de NIT duplicado, manejo de estado `presentado`, creación de periodo si no existe) vive hoy en los routers. Moverla a clases de servicio hace los routers triviales y la lógica testeable sin HTTP. | Backend | 🟠 Alta | Mantenibilidad a largo plazo |
| 3.4 | **Implementar refresh token silencioso** — si el token expira durante el wizard (60 min), el usuario pierde el estado. Agregar interceptor en `apiFetch` que detecte 401 y use un refresh token, o persistir el estado del wizard en `sessionStorage` como mínimo. | Frontend | 🟡 Media | Experiencia de usuario en sesiones largas |
| 3.5 | **Dividir `DeclaracionRentaWizard.jsx` en componentes por paso** — el archivo de 1013 líneas tiene múltiples `useState` acoplados. Extraer `PatrimonioStep`, `IngresosStep`, `LiquidacionStep` con su estado local; el wizard solo coordina navegación. | Frontend | 🟡 Media | Mantenibilidad al agregar cédulas desglosadas |

---

### Sprint 4 — Despliegue MVP en servidor del contador (sem 7–8)

Objetivo: el contador opera desde el servidor definitivo, no desde el equipo de desarrollo.

| # | Actividad | Área | Prioridad | Bloquea |
|---|---|---|---|---|
| 4.1 | **Desplegar Docker Compose en hardware definitivo del contador** — verificar RAM, disco, Docker instalado, red interna. Probar el flujo completo (login → declarante → wizard → PDF) en el hardware real. | Infraestructura | 🔴 Crítica 🔒 | Inicio de operación real |
| 4.2 | **Checklist anual de actualización de parámetros tributarios** — definir y documentar el proceso: quién actualiza `parametros_XXXX.py` cada enero, contra qué resolución de la DIAN, y cómo se testea antes de ponerlo en producción. Mitiga riesgo #2 de `RIESGOS.md`. | Documentación | 🟠 Alta | Precisión en el siguiente año gravable |
| 4.3 | **Pantalla de login conectada a JWT** — hoy el wizard asume sesión activa. Implementar formulario de login, manejo del token en memoria (no `localStorage`), y redirección por rol (Admin → PanelAdmin, Contador/Auxiliar → Cartera). | Frontend | 🟡 Media | Seguridad de acceso |
| 4.4 | **Manual de usuario para el contador y auxiliares** — guía operativa: cómo crear un declarante, correr el wizard, generar el PDF, importar desde Excel, gestionar el checklist de documentos. | Documentación | 🟡 Media | Adopción del sistema |
| 4.5 | **Calendario de vencimientos por NIT** — portar la lógica de la hoja "plazos" del Excel actual al frontend. Alertas de declarantes próximos a vencer según el calendario DIAN. | Frontend | 🟡 Media | Gestión de la cartera |
| 4.6 | ✅ **Botón "Ir a cartera" en PanelAdmin (parche rol admin-contador)** — implementado sesión 6. Prop `onIrACartera` en `PanelAdmin.jsx`; handler `handleIrACartera` + `handleVolverAListado` simplificado en `main.jsx`; botón condicional `{onIrACartera && ...}` en el header. La solución estructural (roles múltiples) queda para Act. 2F.2. | Frontend | 🟠 Alta | Admin bloqueado sin acceso al wizard |

---

## Fase 2 — Robustecimiento (post-MVP, ~+8 semanas desde cierre Fase 1)

Para iniciar Fase 2, Fase 1 debe estar completamente cerrada: el contador opera sin Excel
y las pruebas de paridad pasaron al 100%.

| # | Actividad | Área | Prioridad |
|---|---|---|---|
| 2F.1 | **Panel de administración de parámetros tributarios sin redeploy** — actualización anual de UVT, tarifas y topes desde la interfaz de admin. Hoy requiere editar `parametros_XXXX.py` y hacer deploy. | Frontend + Backend | 🟠 Alta |
| 2F.2 | **Permisos granulares para auxiliares** — hoy Auxiliar tiene acceso idéntico a Contador. Definir qué puede ver/editar cada auxiliar por declarante asignado. | Backend | 🟠 Alta |
| 2F.3 | **Agregar `mypy` al motor de reglas y `ruff`/`black` al proyecto** — el motor de reglas es el código más crítico; los types ya son claros. Agregar como pasos obligatorios del CI para prevenir regresiones silenciosas. | QA / DevOps | 🟡 Media |
| 2F.4 | **Pruebas de carga con los 200 declarantes reales** — validar rendimiento antes de agregar más usuarios. Usar `k6` o `locust` contra el endpoint de liquidación. | QA | 🟡 Media |
| 2F.5 | **Reportes de cartera: estado global y valor total en impuestos** — panel gerencial para el contador. Gráficos de estado (pendiente/en_proceso/presentado) y totales de impuesto a cargo por cartera. | Frontend + Backend | 🟡 Media |

---

## Fase 3 — Portal de clientes (fecha a definir según resultados Fase 1 y 2)

No iniciar Fase 3 sin que Fase 2 esté operativa y estable.

| # | Actividad | Área | Prioridad |
|---|---|---|---|
| 3F.1 | **Autenticación reforzada con doble factor (2FA)** — obligatorio antes de exponer el sistema a internet. TOTP compatible con Google Authenticator o similar. | Seguridad | 🔴 Crítica 🔒 |
| 3F.2 | **Flujo de revisión y aprobación contador → cliente** — el cliente diligencia su información; el contador revisa, observa o aprueba antes de presentar a la DIAN. | Backend + Frontend | 🔴 Crítica 🔒 |
| 3F.3 | **Interfaz de autoservicio para declarantes finales** — reutiliza la misma API (ADR 0001 — arquitectura tres capas). El declarante ve y aprueba su propia liquidación antes de que el contador la presente. | Frontend | 🟠 Alta |
| 3F.4 | **Evaluar migración de servidor local a hosting cloud** — solo si el volumen de usuarios lo justifica. Comparar VPS con Postgres gestionado vs. serverless vs. infraestructura actual. | Infraestructura | 🟢 Baja |

---

## Dependencias entre actividades

```
0.2 (reunión contador)
  └──▶ 0.3 (Excel real)
         └──▶ 2.1 (pruebas de paridad) ──▶ 4.1 (despliegue producción)

0.1 (rotar JWT)
  └──▶ 2.5 (HTTPS) ──▶ 4.1

2.2 (backups) ──▶ 4.1
2.3 (Habeas Data) ──▶ 4.1 (datos reales de clientes)

1.1 (migración 0003) ──▶ 4.1
1.2 (modelos ingreso/deduccion) ──▶ 3.1 (Formulario 210)

3.1 (mapper 210) ──▶ 3.2 (PDF)

4.6 (botón "Ir a cartera") ──▶ 2F.2 (roles múltiples — solución estructural)
```

---

## Referencias cruzadas

| Documento | Relación con este plan |
|---|---|
| `docs/PLAN_DE_TRABAJO.md` | Cronograma estratégico y alcance por fase — este plan es el detalle operativo |
| `docs/FALTANTES.md` | Lista de brechas funcionales — cada ítem pendiente tiene su actividad aquí |
| `docs/RIESGOS.md` | Riesgos #1, #2, #3, #6, #9 son los que generan actividades 🔒 en este plan |
| `data/backlog.csv` | Fuente original del backlog; sincronizar `estado` al completar actividades |
| `ESTADO_ACTUAL.md` | Actualizar sección "Qué existe y en qué estado" al cerrar cada sprint |
| `docs/GESTION_PROYECTO.md` | Cómo pasar este plan a GitHub Issues y Projects |