# Riesgos y recomendaciones

## 1. Matriz de riesgos

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| 1 | Errores de cálculo tributario no detectados a tiempo (el costo de un error aquí es una declaración mal presentada ante la DIAN) | Media | Muy alto | Suite de pruebas unitarias del motor de reglas contra casos reales del Excel actual + fase obligatoria de "pruebas de paridad" declarante por declarante antes de decomisionar el Excel (ver `docs/PLAN_DE_TRABAJO.md`) |
| 2 | Cambios normativos anuales (UVT, tarifas, topes) mal actualizados | Alta (ocurre cada año) | Alto | Parámetros tributarios aislados en módulos de datos versionados por año (`parametros_2025.py`, `parametros_2026.py`, …); checklist anual de actualización documentado en este repositorio |
| 3 | Pérdida o corrupción de datos en el servidor local (falla de hardware, error humano) | Media | Muy alto | Backups automatizados diarios + prueba periódica de restauración; considerar réplica cifrada fuera de sitio |
| 4 | Alcance del MVP subestimado (el Excel actual cubre casos que el equipo no conoce hasta que aparecen en producción) | Alta | Medio-Alto | Sesión de validación funcional con el contador antes de estimar cronograma final (semanas 1-2 del plan); usar `docs/FALTANTES.md` como checklist vivo |
| 5 | Resistencia al cambio del contador/auxiliares acostumbrados al Excel | Media | Medio | Migración gradual por módulos, no todo de una vez; conservar exportación a formato similar al Excel actual durante la transición |
| 6 | Exposición de datos personales sensibles (NIT, patrimonio) si el servidor local no está bien asegurado | Baja-Media | Muy alto | Cifrado en reposo y en tránsito, acceso solo por red interna en Fase 1, política de tratamiento de datos formalizada antes de Fase 3 |
| 7 | Dependencia de una sola persona para mantenimiento (bus factor) | Media | Alto | Documentación técnica obligatoria (este repositorio), código con pruebas automatizadas, evitar lógica "solo en la cabeza" del desarrollador original |
| 8 | Desviación de cronograma por subestimar la complejidad de portar las ~140 hojas del Excel actual | Alta | Medio | Priorización explícita en `docs/FALTANTES.md`; cronograma con checkpoint de re-estimación después de la fase de definición funcional |
| 9 | Presentar una declaración con el sistema nuevo antes de validar completamente la paridad con el Excel | Baja si se sigue el plan | Muy alto | Regla dura de gobierno: ninguna declaración se presenta ante la DIAN usando el sistema nuevo hasta pasar la fase de pruebas de paridad |

## 2. Recomendaciones generales

1. **No decomisionar el Excel actual de inmediato.** Operar ambos sistemas en paralelo
   durante al menos un ciclo de declaraciones (o una muestra representativa de declarantes)
   antes de depender exclusivamente del sistema nuevo.
2. **Empezar por el motor de reglas, no por la interfaz.** El mayor riesgo del proyecto es
   tributario, no de experiencia de usuario; priorizar pruebas exhaustivas del cálculo antes
   de invertir tiempo en pulir la interfaz más allá del prototipo ya construido.
3. **Tratar los parámetros tributarios como un proceso, no solo como código.** Definir desde
   ahora quién es responsable cada año de verificar UVT, tarifas y topes contra la
   resolución vigente de la DIAN, y dejarlo documentado en este repositorio.
4. **Formalizar la política de datos personales desde Fase 1**, aunque el sistema no esté
   expuesto a internet todavía — es más barato hacerlo ahora que retroactivamente cuando ya
   haya 200 declarantes con datos cargados.
5. **Medir antes de prometer.** Usar la Fase 1 para capturar métricas reales de tiempo de
   preparación por declarante; esas cifras son las que justificarán (o no) la inversión en
   Fase 2 y Fase 3 ante quien financie el proyecto.
6. **Mantener el motor de reglas desacoplado del framework web.** Si en el futuro se decide
   cambiar de FastAPI a otro framework, o de React a otra librería de frontend, el motor de
   reglas tributarias (funciones puras, sin dependencias de framework) debe poder migrarse
   sin reescribirse.
