# Faltantes — Brecha entre el prototipo actual y un producto de producción

Este documento lista, honestamente, lo que el prototipo de wizard (`frontend/src/wizard`)
y este esqueleto de repositorio **no cubren todavía**, para que quede explícito qué falta
antes de decomisionar el Excel actual.

## 1. Cobertura funcional tributaria

- [ ] **Ganancias ocasionales completas**: venta de casa de habitación anterior a 1987,
  venta de inmuebles con ajuste art. 73 E.T., venta de acciones (en bolsa y fuera de bolsa),
  herencias, loterías/rifas, indemnizaciones de seguros de vida — el prototipo solo tiene un
  campo agregado, el Excel actual tiene ~15 hojas de detalle para esto.
- [ ] **Ajustes fiscales por año de adquisición (art. 73 E.T.)** para actualizar costos de
  bienes raíces y acciones — hoy vive en la hoja `ajustes art. 73` del Excel, no está
  modelado en el motor de reglas nuevo.
- [ ] **Cédula de dividendos y participaciones** con su tarifa especial y tabla propia.
- [ ] **Deducciones específicas**: vivienda (intereses hipotecarios), salud, ICETEX,
  cesantías, donaciones, becas, inversión en cine/obras audiovisuales/librerías —
  cada una con su propio tope legal, hoy solo hay dos campos genéricos en el prototipo.
- [ ] **Descuentos tributarios** (art. 254, 255, 256, 257, 257-1 E.T.) con el límite del 30%
  del impuesto básico de renta.
- [ ] **Compensaciones** (rentas líquidas negativas de años anteriores).
- [ ] **Bienes y deudas en moneda extranjera** con conversión por TRM diaria (hoy existe la
  hoja `TRM_diaria` en el Excel; no está integrada al motor nuevo).
- [ ] **Sanciones e intereses de mora** con las reglas de gradualidad del art. 640 E.T. —
  hoy es un módulo completo en el Excel (`Sanciones (2)`), no portado.
- [ ] **Anticipo de renta año siguiente** con las dos metodologías de ley (individual y
  promedio) y su lógica de primera/segunda/tercera vez.

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

1. **Bloqueante para MVP:** ganancias ocasionales, deducciones específicas con topes reales,
   sanciones/intereses, carga masiva, panel de cartera, pruebas de paridad.
2. **Importante pero no bloqueante:** moneda extranjera, compensaciones, historial de
   versiones — pueden entrar en una iteración temprana de Fase 2 si no son casos frecuentes
   en la cartera actual de 200 declarantes.
3. **Antes de Fase 3 (portal de clientes):** autenticación robusta, auditoría completa,
   política de datos personales formalizada — son bloqueantes para exponer el sistema a los
   clientes finales, no para el uso interno del contador.

> Recomendación: antes de estimar el cronograma final de Fase 1, revisar con el contador
> qué porcentaje real de sus 200 declarantes usa cada uno de los conceptos listados arriba,
> para no invertir esfuerzo en casos que no aplican a la cartera actual.
