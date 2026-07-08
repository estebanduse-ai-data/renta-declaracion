# ADR 0001 — Arquitectura en tres capas desacopladas

**Estado:** Aceptada
**Fecha:** 2026-07-08

## Contexto

El producto debe servir hoy a un contador (Fase 1, servidor local, ~200 declarantes) y en
el futuro a clientes finales a través de un portal de autoservicio (Fase 3). Construir dos
sistemas separados duplicaría la lógica tributaria — el activo más crítico y de mayor
riesgo del proyecto — y generaría divergencias peligrosas entre ambos.

## Decisión

Separar el sistema en tres capas independientes desde el primer commit:

1. **Motor de reglas tributarias** — funciones puras en Python, sin dependencias de
   framework web ni de base de datos, parametrizadas por año gravable.
2. **API** — orquesta autenticación, validación y persistencia, pero delega todo cálculo
   tributario al motor de reglas.
3. **Interfaz de usuario** — hoy el panel del contador; en Fase 3, se añade el portal de
   clientes como una segunda interfaz que consume la misma API, sin duplicar lógica.

## Consecuencias

**Positivas**
- Un cambio normativo (UVT, tarifa, tope) se aplica en un solo lugar y beneficia a todas las
  interfaces presentes y futuras.
- El motor de reglas se puede probar exhaustivamente de forma aislada, sin necesidad de
  levantar base de datos ni servidor web.
- Migrar de servidor local a nube en Fase 3 (si se decide) no requiere tocar la lógica
  tributaria, solo la capa de despliegue.

**Negativas / costos aceptados**
- Mayor esfuerzo de diseño inicial frente a construir todo acoplado en un solo módulo.
- Requiere disciplina del equipo para no "atajar" metiendo lógica tributaria dentro de la
  capa de API por conveniencia — se mitiga con revisión de código y pruebas obligatorias en
  `backend/tests`.
