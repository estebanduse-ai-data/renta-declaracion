# Arquitectura técnica

## 1. Vista general

Arquitectura en tres capas independientes, para que la interfaz del contador (Fase 1) y el
futuro portal de clientes (Fase 3) compartan el mismo motor de cálculo y la misma API, sin
duplicar lógica de negocio.

```
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   Frontend — Panel contador  │   │  Frontend — Portal cliente   │
│   (React, Fase 1)            │   │  (React, Fase 3 — futuro)    │
└──────────────┬───────────────┘   └──────────────┬───────────────┘
               │                                    │
               └──────────────────┬─────────────────┘
                                   │  HTTPS / REST (JSON)
                        ┌──────────▼───────────┐
                        │   API — FastAPI       │
                        │   (autenticación,     │
                        │    validación,        │
                        │    orquestación)      │
                        └──────────┬────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                                     │
      ┌──────────▼───────────┐          ┌─────────────▼─────────────┐
      │  Motor de reglas      │          │   Base de datos            │
      │  tributarias (Python) │          │   PostgreSQL                │
      │  — puro, sin estado   │          │   (declarantes, periodos,   │
      │  — parametrizado      │          │   parámetros, auditoría)    │
      └────────────────────────┘          └─────────────────────────┘
```

## 2. Componentes

### 2.1 Motor de reglas tributarias (`backend/app/rules_engine`)
- Funciones puras (sin efectos secundarios, sin acceso a base de datos) que replican las
  fórmulas del Formulario 210: UVT, tabla progresiva del art. 241 E.T., renta presuntiva,
  límite del 40% de rentas exentas y deducciones, cálculo de sanciones e intereses.
- Los parámetros de cada año gravable (UVT, tarifas, topes) viven en un módulo de datos
  separado (`parametros_2025.py`), para que actualizar el año solo implique agregar un
  nuevo archivo de parámetros, sin tocar la lógica de cálculo.
- 100% cubierto por pruebas unitarias, incluyendo los casos límite (patrimonio negativo,
  renta líquida cero, tramos exactos de la tabla de tarifas).

### 2.2 API (`backend/app/api`)
- Expone endpoints REST por recurso: `declarantes`, `periodos`, `patrimonio`, `ingresos`,
  `liquidacion`, `parametros`.
- Responsable de autenticación (JWT), autorización por rol, validación de entrada y
  orquestación (llama al motor de reglas, persiste resultados).
- No contiene lógica tributaria propia: siempre delega en el motor de reglas.

### 2.3 Base de datos (PostgreSQL)
Modelo relacional multi-declarante y multi-año:

- `declarante` — identificación, RUT, contador asignado
- `periodo_gravable` — año, estado (borrador / en revisión / presentado)
- `patrimonio` — activos y pasivos por categoría, por periodo
- `ingreso_cedular` — tipo de cédula, valor, retenciones
- `deduccion` / `descuento_tributario`
- `liquidacion` — resultado consolidado del periodo
- `parametro_tributario` — UVT, tarifas y topes por año
- `usuario` / `rol` — control de acceso (Admin, Contador, Auxiliar; extensible a Cliente en Fase 3)
- `auditoria_cambio` — trazabilidad de modificaciones

### 2.4 Frontend (`frontend/`)
- React + Vite. El wizard de captura (`src/wizard`) consume la API vía HTTP; no contiene
  lógica tributaria propia, solo la réplica ligera necesaria para validaciones instantáneas
  en el navegador (que siempre se revalida en el backend antes de persistir).

## 3. Decisiones de diseño clave

1. **El backend es la única fuente de verdad del cálculo tributario.** El frontend puede
   mostrar cálculos preliminares para dar feedback inmediato, pero el valor que se persiste
   y se usa para el resumen final siempre viene del backend.
2. **Parámetros tributarios como datos, no como código.** Cada año gravable es un registro
   nuevo, nunca una modificación de fórmulas existentes. Esto es lo que permite que el
   mantenimiento anual sea de bajo costo (ver `docs/PLAN_DE_TRABAJO.md`, sección 5).
3. **Multi-año desde el día uno.** Aunque Fase 1 solo gestiona el año gravable actual, el
   modelo de datos soporta histórico completo por declarante, necesario para el cálculo de
   renta presuntiva, anticipo y comparación patrimonial.
4. **Despliegue en servidor local vía Docker.** Facilita portabilidad (se puede migrar a
   nube en Fase 3 sin rediseño) y mantiene los datos dentro de la infraestructura del
   contador mientras el volumen de datos es sensible y el equipo de soporte es reducido.

## 4. Ver también
- [`docs/adr/0001-arquitectura-tres-capas.md`](adr/0001-arquitectura-tres-capas.md)
- [`docs/FALTANTES.md`](FALTANTES.md)
- [`docs/RIESGOS.md`](RIESGOS.md)
