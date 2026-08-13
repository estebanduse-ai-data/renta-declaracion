# Faltantes — Brecha entre el estado actual y un producto de producción

**Última actualización:** sesión jul-2026. Refleja el estado tras conectar el wizard
a la API, implementar el panel de administración y la carga masiva desde Excel.

---

## 1. Cobertura funcional tributaria

- [x] Ganancias ocasionales (venta inmuebles art. 73, acciones, herencias, loterías).
  **Pendiente:** indemnizaciones de seguros de vida y vivienda adquirida antes de 1987.
- [x] Ajustes fiscales por año de adquisición (art. 73 E.T.) — tabla de factores en
  `parametros_2025.py`. **Pendiente:** ampliar y confirmar contra el decreto vigente.
- [x] Cédula de dividendos y participaciones.
- [x] Deducciones específicas con tope real — vivienda, salud, dependientes, ICETEX,
  cesantías, becas. **Pendiente:** donaciones como deducción directa de renta de trabajo
  y deducción por inversión en cine/audiovisual/librerías.
- [x] Descuentos tributarios — donaciones art. 257 E.T. y límite art. 259 E.T.
  **Pendiente:** descuentos arts. 255 y 256 E.T. (investigación, energía).
- [x] Compensaciones (rentas líquidas negativas años anteriores).
  **Pendiente:** control de vigencia 12 años y separación por cédula requieren
  histórico completo por declarante — no modelado en BD todavía.
- [x] Bienes y deudas en moneda extranjera con conversión por TRM.
  **Pendiente:** integrar fuente automática de TRM (API Banco de la República).
- [x] Sanciones e intereses de mora. **Pendiente:** régimen de sanción reducida por
  gradualidad (art. 640 E.T.) y tasa de mora referencial — debe sustituirse por la
  tasa certificada por la Superintendencia Financiera antes de uso en producción.
- [x] Anticipo de renta año siguiente (ambas metodologías).
- [x] Wizard con patrimonio desglosado (efectivo, inversiones, cuentas por cobrar,
  inventarios, propiedades, vehículos, otros activos; deudas bancarias, deudas con
  personas, otros pasivos).
- [x] Rentas cedulares con fondo de pensiones y AFC separados; medicina prepagada y
  seguros complementarios separados; totales visibles por bloque.

---

## 2. Producto y experiencia

- [x] Wizard conectado a la API real (los tres gaps corregidos).
- [x] Persistencia del resultado de liquidación en `periodo_gravable.resultado_liquidacion`.
- [x] Panel de administración con dashboard de alertas, cartera, checklist de
  documentos e importación masiva desde Excel.
- [x] Carga masiva desde Excel (endpoint `POST /admin/importar-declarantes` + script CLI).
- [ ] **Checklist de documentos persistido en BD** — hoy se guarda en `localStorage`
  del navegador; si el contador cambia de equipo o limpia el navegador, se pierde.
  Requiere tabla nueva `documento_checklist` y migración `0003`.
- [ ] Generación del reporte final en el formato de casillas del Formulario 210, listo
  para transcribir en los Servicios Informáticos Electrónicos (SIE) de la DIAN.
- [ ] Historial de versiones por declaración (borrador / versión presentada /
  correcciones posteriores).
- [ ] Modo de revisión donde el contador aprueba o devuelve observaciones — prepara la
  Fase 3 de autoservicio sin cambios estructurales de modelo.
- [ ] Importador con mapeo de columnas personalizadas — hoy exige la plantilla estándar;
  una vez el contador entregue su Excel actual, evaluar si conviene mapeo flexible.
- [ ] Pruebas de paridad declarante por declarante vs. el Excel actual —
  **bloquea presentar cualquier declaración real con el sistema nuevo**
  (ver `docs/RIESGOS.md`, riesgo #9).

---

## 3. Plataforma y no-funcionales

- [x] Autenticación y control de acceso por rol (JWT, Admin/Contador/Auxiliar).
- [x] Auditoría de cambios (`AuditoriaCambio`), incluyendo importaciones masivas.
- [x] Migraciones Alembic aplicadas y verificadas con `alembic check`.
- [x] Módulo de configuración administrable (parámetros tributarios, TRM, tasa mora).
- [x] Panel de administración exclusivo para rol Admin.
- [ ] **Checklist de documentos en BD** (migración `0003` pendiente).
- [ ] Backups automatizados y prueba de restauración.
- [ ] Suite de pruebas de paridad (ver sección 2).
- [ ] Manejo de errores y observabilidad (logs estructurados, alertas ante fallas).
- [ ] Documentación de usuario final para el contador y sus auxiliares.
- [ ] Política de tratamiento de datos personales (Habeas Data) formalizada —
  obligatoria incluso en Fase 1 por el volumen de datos sensibles de ~200 declarantes.
- [ ] Cifrado en reposo y HTTPS — pendientes para el servidor local definitivo.

---

## 4. Backend — persistencia y CRUD pendiente

- [x] CRUD declarantes y periodos con auditoría.
- [x] Persistencia del resultado de liquidación (JSONB en `periodo_gravable`).
- [x] Importación masiva con auditoría por registro.
- [ ] Modelos y endpoints de `ingreso_cedular` y `deduccion` por periodo — hoy el
  wizard envía los totales ya consolidados; falta guardarlos línea por línea para
  poder recalcular sin volver a capturar.
- [ ] Tabla `documento_checklist` — migración `0003`.
- [ ] Endpoint de exportación de casillas del Formulario 210 (JSON → PDF o CSV).

---

## 5. Priorización actualizada

| Prioridad | Tarea | Bloquea |
|---|---|---|
| 🔴 Crítica | Pruebas de paridad vs. Excel actual | Presentar cualquier declaración real |
| 🔴 Crítica | Obtener Excel del contador + probar importador | Migrar los 200 declarantes |
| 🟠 Alta | Checklist de documentos en BD (migración 0003) | Confiabilidad del checklist |
| 🟠 Alta | Modelos `ingreso_cedular` / `deduccion` por periodo | Recálculo sin re-captura |
| 🟡 Media | Reporte casillas Formulario 210 | Transcripción a SIE DIAN |
| 🟡 Media | Historial de versiones por declaración | Correcciones y auditoría |
| 🟡 Media | Fuente automática TRM (API Banco República) | Precisión en activos en divisas |
| 🟢 Baja | Descuentos arts. 255/256 E.T. | Solo si hay casos en la cartera |
| 🟢 Baja | Mapeo flexible de columnas en el importador | Comodidad del contador |
---

## 6. Hallazgos técnicos adicionales (análisis senior jul-2026)

Estos ítems no estaban en el backlog original pero fueron identificados al analizar
el código fuente. Tienen actividad asignada en `docs/PLAN_DE_ACTIVIDADES.md`.

| Hallazgo | Archivo | Actividad | Impacto |
|---|---|---|---|
| `JWT_SECRET_KEY` commitado en `.env` real | `backend/.env` | Act. 0.1 | 🔴 Seguridad activa |
| ✅ `datetime.utcnow()` deprecated Python 3.12 | `models/usuario.py`, `models/declarante.py`, `models/auditoria.py`, `models/configuracion.py`, `api/routes_admin.py` | Act. 0.4 — **resuelto sesión 6** | 🟠 Error en Python 3.14 |
| ✅ `float` en schemas monetarios (debería ser `Decimal`) | `schemas/declarante.py`, `routes_liquidacion.py`, `routes_ganancias_ocasionales.py`, `routes_declarantes.py` | Act. 0.5 — **resuelto sesión 6** | 🟠 Precisión numérica en cálculos DIAN |
| ✅ Tabla de tarifa duplicada en wizard y en `parametros_2025.py` | `wizard/DeclaracionRentaWizard.jsx` | Act. 1.4 — **resuelto sesión 7** | 🟠 Desincronización al cambiar año |
| `GET /declarantes` sin paginación (`db.query().all()`) | `api/routes_declarantes.py` | Act. 1.3 | 🟠 Escalabilidad |
| Lógica de negocio mezclada en routers (sin service layer) | `api/routes_*.py` | Act. 3.3 | 🟡 Mantenibilidad |
| Wizard de 1013 líneas sin separación por componente | `wizard/DeclaracionRentaWizard.jsx` | Act. 3.5 | 🟡 Mantenibilidad |
| Sin refresh token — sesión de 60 min interrumpe wizard | `src/api.js` | Act. 3.4 | 🟡 UX en sesiones largas |
| CI en Python 3.12 pero runtime local en 3.13 | `.github/workflows/ci.yml` | — | 🟢 Alinear versiones |
| ✅ Usuario con rol único — `admin` bloqueado sin acceso a cartera ni wizard | `models/usuario.py` (campo `rol: Enum`), `main.jsx` (dispatch binario `rol === "admin"`) | Act. 4.6 — **parche resuelto sesión 6**; solución estructural Act. 2F.2 Fase 2 | 🟠 Bloquea al contador-admin en operación diaria |

> **Cómo actualizar esta sección:** al resolver un hallazgo, marcar el ítem con ✅
> y agregar la referencia al commit o PR que lo cierra.