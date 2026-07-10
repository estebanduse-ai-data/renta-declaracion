# ADR 0002 — Configuración administrable separada por frecuencia de cambio

**Estado:** Aceptada
**Fecha:** 2026-07-09

## Contexto

El motor de reglas necesita varios valores que cambian con el tiempo: UVT, tarifas y
topes (anuales), TRM (diaria) y tasa de interés de mora (trimestral). El pedido
explícito era que estos valores fueran administrables desde un módulo de
configuración en vez de vivir fijos en el código, para que un Admin pudiera
actualizarlos sin depender de un despliegue nuevo.

La pregunta de diseño era si modelar esto como una única tabla genérica de
"configuración" (clave-valor) o como tablas separadas por tipo de parámetro.

## Decisión

Tres tablas separadas, cada una con la forma de dato que le corresponde a su
frecuencia real de cambio:

1. **`parametro_tributario`** — un documento JSON versionado por año gravable,
   validado por `ParametrosTributariosPayload` antes de guardarse. Cambia una vez al
   año (salvo reforma tributaria).
2. **`trm_diaria`** — una fila por fecha. Cambia todos los días hábiles.
3. **`tasa_interes_mora`** — vigencias con fecha de inicio y fin. Cambia
   trimestralmente.

Se descartó una tabla única de configuración clave-valor porque mezclar algo que
cambia 250 veces al año (TRM) con algo que cambia una vez al año (UVT) en la misma
estructura habría obligado a un modelo de "vigencia" genérico e innecesariamente
complejo, y habría dificultado responder con precisión "qué tasa de interés de mora
aplicaba el 15 de marzo de 2025" sin ambigüedad frente a otras claves no relacionadas.

## Consecuencias

**Positivas**
- Cada tabla tiene exactamente la forma de consulta que necesita (`obtener_trm_vigente`,
  `obtener_tasa_interes_mora_vigente`, `obtener_parametros_vigentes`), sin lógica
  condicional para distinguir tipos de parámetro dentro de una tabla genérica.
- El histórico de cambios es natural: los `parametro_tributario` inactivos de años
  anteriores quedan disponibles para volver a calcular declaraciones viejas con sus
  parámetros originales, sin necesitar una tabla de auditoría aparte para eso
  específicamente (aunque `auditoria_cambio` registra además quién hizo cada cambio).
- El motor de reglas (`app/rules_engine/`) no cambia: sigue recibiendo los mismos
  argumentos con nombre que siempre recibió. La clase adaptadora `ParametrosVigentes`
  en `app/services/parametros_service.py` es la única pieza que sabe traducir entre el
  documento JSON de base de datos y esos argumentos.

**Negativas / costos aceptados**
- Tres modelos y tres conjuntos de endpoints en vez de uno solo — más código de
  infraestructura por escribir y mantener.
- El esquema de validación (`ParametrosTributariosPayload`) es un espejo manual del
  módulo estático `parametros_2025.py`; si se agrega un parámetro nuevo al motor de
  reglas, hay que recordar añadirlo en tres lugares (el módulo estático, el esquema, y
  el adaptador `ParametrosVigentes`). Se mitiga parcialmente con
  `test_adaptador_expone_todos_los_atributos_del_modulo_estatico` en
  `backend/tests/test_parametros_service.py`, que falla si alguno de los tres se
  desincroniza.
