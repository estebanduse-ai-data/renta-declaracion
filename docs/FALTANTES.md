# Faltantes — Brecha entre el prototipo actual y un producto de producción

Este documento lista, honestamente, lo que el prototipo de wizard (`frontend/src/wizard`)
y este esqueleto de repositorio **no cubren todavía**, para que quede explícito qué falta
antes de decomisionar el Excel actual.

## 1. Cobertura funcional tributaria

- [x] **Ganancias ocasionales** — venta de inmuebles con ajuste art. 73, venta de acciones
  (bolsa/fuera de bolsa), herencias/legados/donaciones, loterías/rifas. Implementado en
  `backend/app/rules_engine/ganancias_ocasionales.py`, expuesto en
  `/ganancias-ocasionales/*`, con 9 pruebas unitarias. **Pendiente:** indemnizaciones de
  seguros de vida y el caso especial de vivienda adquirida antes de 1987.
- [x] **Ajustes fiscales por año de adquisición (art. 73 E.T.)** — implementado como tabla
  de factores en `parametros_2025.py` (`FACTORES_AJUSTE_ART73_POR_ANIO`), consumida por
  `costo_fiscal_ajustado()`. **Pendiente:** los factores incluidos son una muestra de años
  recientes; ampliar y confirmar contra el decreto de ajuste de costos vigente antes de
  producción.
- [x] **Cédula de dividendos y participaciones** — implementada en
  `backend/app/rules_engine/dividendos.py`, con el componente de dividendos gravados
  (tabla marginal) y no gravados en cabeza de la sociedad (tarifa corporativa equivalente).
- [x] **Deducciones específicas con tope real** — intereses de vivienda, salud/medicina
  prepagada y dependientes económicos, implementadas en
  `backend/app/rules_engine/deducciones.py`. Ampliado con **ICETEX** (comparte tope con
  vivienda, art. 119 E.T.), **cesantías e intereses de cesantías** (tabla de exención según
  ingreso promedio) y **becas de estudio** (exención total si no es contraprestación por
  servicios). **Pendiente:** donaciones como deducción específica de renta de trabajo (nota:
  el descuento tributario del 25% ya cubre el caso general de donaciones, ver abajo), y la
  deducción por inversión en cine/obras audiovisuales/librerías.
- [x] **Descuentos tributarios** — donaciones (art. 257 E.T.) y el límite conjunto del 30%
  del impuesto básico (art. 259 E.T.) implementados en
  `backend/app/rules_engine/descuentos_tributarios.py`. **Pendiente:** descuentos
  específicos de los artículos 255 y 256 E.T. (inversión en investigación/tecnología,
  proyectos de energía) — hoy solo se modela el mecanismo genérico del límite, no cada
  descuento particular.
- [x] **Compensaciones** (rentas líquidas negativas de años anteriores). Implementado en
  `backend/app/rules_engine/compensaciones.py`. **Pendiente:** el control de vigencia del
  plazo de 12 años y la separación por cédula requieren el histórico completo por
  declarante — no modelado todavía a nivel de base de datos.
- [x] **Bienes y deudas en moneda extranjera** con conversión por TRM. Implementado en
  `backend/app/rules_engine/moneda_extranjera.py` (TRM de cierre para patrimonio, TRM del
  día para ingresos). **Pendiente:** integrar una fuente real de TRM diaria (equivalente a
  la hoja `TRM_diaria` del Excel actual) — hoy la función recibe la TRM como parámetro, no
  la consulta.
- [x] **Sanciones e intereses de mora** — sanción por extemporaneidad (con y sin impuesto a
  cargo), sanción por corrección, e interés de mora simple diario, implementados en
  `backend/app/rules_engine/sanciones.py`. **Pendiente:** régimen de sanción reducida por
  gradualidad (art. 640 E.T., parágrafos de buen comportamiento del contribuyente) y la
  tasa de interés de mora es referencial — debe sustituirse por la tasa vigente certificada
  por la Superintendencia Financiera antes de un caso real.
- [x] **Anticipo de renta año siguiente** — ambas metodologías (individual y promedio) con
  lógica de primera/segunda/tercera vez, implementado en
  `backend/app/rules_engine/anticipo.py`.

## 2. Producto y experiencia

- [ ] Carga masiva desde el Excel actual (importador con mapeo de columnas y validación de
  consistencia).
- [ ] Panel de gestión de cartera para el contador (listado de 200 declarantes, estados,
  filtros, calendario de vencimientos por NIT).
- [ ] Generación del reporte final en el formato exacto de casillas del Formulario 210,
  listo para transcribir en los Servicios Informáticos Electrónicos.
- [ ] Historial de versiones por declaración (borrador vs. versión presentada vs.
  correcciones posteriores).
- [ ] Modo "revisión" donde el contador aprueba o devuelve observaciones (relevante desde ya
  para preparar la Fase 3 de autoservicio).

## 3. Plataforma y no-funcionales

- [ ] Autenticación y control de acceso por rol (hoy no implementado, solo mencionado en
  la arquitectura).
- [ ] Auditoría de cambios (quién modificó qué dato y cuándo).
- [ ] Backups automatizados y prueba de restauración.
- [ ] Suite de pruebas de paridad: comparar, declarante por declarante, el resultado del
  sistema nuevo contra el Excel actual, antes de decomisionarlo.
- [ ] Manejo de errores y observabilidad (logs estructurados, alertas ante fallas de cálculo).
- [ ] Documentación de usuario final para el contador y sus auxiliares.
- [ ] Política de tratamiento de datos personales (Habeas Data) formalizada — obligatoria
  incluso en Fase 1 por el volumen de datos sensibles de 200 declarantes.

## 4. Priorización sugerida

1. **Bloqueante para MVP, ya cerrado en el motor de reglas (✔ este repositorio):**
   ganancias ocasionales, cédula de dividendos, deducciones específicas con topes reales
   (incluyendo ICETEX, cesantías y becas), descuentos tributarios, sanciones/intereses,
   anticipo, compensaciones y moneda extranjera. Todo con pruebas unitarias — ver
   `backend/tests/` y el changelog en el historial de Git.
2. **Bloqueante para MVP, todavía pendiente:** carga masiva, panel de cartera, pruebas de
   paridad contra el Excel actual, autenticación, persistencia de todo lo anterior en la
   API (hoy el motor de reglas calcula pero solo el endpoint de liquidación y ganancias
   ocasionales están expuestos vía API).
3. **Importante pero no bloqueante:** historial de versiones por declaración, descuentos
   específicos de los artículos 255/256 E.T. — pueden entrar en una iteración temprana de
   Fase 2 si no son casos frecuentes en la cartera actual de 200 declarantes.
4. **Antes de Fase 3 (portal de clientes):** autenticación robusta, auditoría completa,
   política de datos personales formalizada — son bloqueantes para exponer el sistema a los
   clientes finales, no para el uso interno del contador.

> Recomendación: antes de estimar el cronograma final de Fase 1, revisar con el contador
> qué porcentaje real de sus 200 declarantes usa cada uno de los conceptos listados arriba,
> para no invertir esfuerzo en casos que no aplican a la cartera actual.
