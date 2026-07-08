# Plan de trabajo — Producto de automatización de declaración de renta

## 1. Objetivo del producto

Construir una herramienta que reemplace el archivo Excel/VBA actual para preparar la
Declaración de Renta de Personas Naturales (Formulario 210, DIAN), operada inicialmente
por un contador para una cartera de 200 declarantes, en un servidor local, con arquitectura
lista para evolucionar a un portal de autoservicio para clientes finales.

## 2. Alcance por fase

### Fase 1 — MVP interno para el contador
**Objetivo:** reemplazar el Excel para la operación diaria del contador.

| Entregable | Descripción |
|---|---|
| Motor de reglas tributarias | UVT, tabla del art. 241 E.T., topes de deducciones y rentas exentas, parametrizados por año gravable |
| Módulo Datos generales | Captura y validación de datos del RUT, dependientes económicos |
| Módulo Patrimonio | Activos, pasivos, patrimonio líquido, comparación año anterior |
| Módulo Rentas cedulares | Cédula general (trabajo, capital, no laboral), pensiones, dividendos, ganancias ocasionales |
| Módulo Renta presuntiva | Cálculo automático con exclusiones de ley |
| Módulo Liquidación privada | Impuesto a cargo, descuentos tributarios, anticipo año siguiente |
| Módulo Pagos | Sanciones, intereses de mora, pago total |
| Panel del contador | Gestión de cartera de 200 declarantes, estados, vencimientos |
| Carga masiva inicial | Migración de datos desde los archivos Excel actuales |
| Exportación | PDF de control + reporte estructurado por casilla del Formulario 210 |

**Criterio de salida de Fase 1:** el contador puede gestionar el 100% de su cartera actual
sin volver al archivo Excel, con paridad funcional en los cálculos críticos.

### Fase 2 — Robustecimiento y operación en producción
- Multiusuario avanzado (auxiliares trabajando en paralelo, permisos granulares)
- Reportes de cartera (estado, valor total en impuestos, alertas de vencimiento)
- Panel de administración de parámetros tributarios (actualización anual sin despliegue de código)
- Auditoría completa de cambios por declarante
- Endurecimiento de seguridad (backups automatizados, cifrado, pruebas de recuperación)
- Pruebas de carga con datos reales de los 200 declarantes

### Fase 3 — Portal de autoservicio para clientes finales
- Interfaz para que cada declarante diligencie su propia información
- Flujo de revisión y aprobación por parte del contador antes de presentar
- Autenticación reforzada (2FA), políticas formales de tratamiento de datos personales
- Evaluación de salida del servidor local a hosting con mayor disponibilidad, si el volumen lo justifica

## 3. Cronograma estimado (Fase 1)

| Semana | Hito |
|---|---|
| 1–2 | Definición funcional detallada por módulo, validación con el contador, diseño de modelo de datos |
| 3–5 | Motor de reglas tributarias + pruebas unitarias contra casos reales del Excel actual |
| 6–9 | Backend: API de declarantes, patrimonio, ingresos, liquidación |
| 6–10 | Frontend: wizard completo conectado a la API (en paralelo al backend) |
| 10–11 | Panel del contador + carga masiva de los 200 declarantes existentes |
| 12 | Pruebas de paridad: comparar resultados del sistema nuevo vs. el Excel actual, declarante por declarante |
| 13 | Corrección de hallazgos, documentación de usuario, despliegue en servidor local |
| 14 | Acompañamiento en producción durante el primer cierre de declaraciones con el sistema nuevo |

**Duración total estimada Fase 1: ~14 semanas (3.5 meses)** con el equipo descrito abajo.
Este cronograma es una línea base; debe ajustarse tras la semana 1–2 con el detalle
funcional ya validado.

## 4. Equipo sugerido

| Rol | Dedicación Fase 1 | Responsabilidad principal |
|---|---|---|
| Desarrollador backend (Python/FastAPI) | Tiempo completo | Motor de reglas, API, modelo de datos, seguridad |
| Desarrollador frontend (React) | Tiempo completo | Wizard, panel del contador, validaciones de UI |
| Contador / experto tributario (el mismo usuario o delegado) | Parcial, dedicado en semanas 1–2 y 12 | Validación funcional y de casos reales, pruebas de paridad |
| Líder de proyecto / QA | Parcial | Seguimiento del cronograma, pruebas de aceptación |

Para un equipo más pequeño, backend y frontend pueden ser asumidos por una sola persona
full-stack, extendiendo el cronograma en aproximadamente 30-40%.

## 5. Presupuesto estimado (orden de magnitud)

> Cifras referenciales para dimensionar la inversión; deben ajustarse a tarifas locales
> reales antes de comprometer presupuesto.

| Concepto | Rango estimado |
|---|---|
| Desarrollo Fase 1 (equipo de 2 desarrolladores, ~3.5 meses) | Equivalente a 7 meses-persona de desarrollo |
| Infraestructura servidor local (hardware, si no existe) | Costo único de equipo, sin recurrencia mensual relevante |
| Licencias | Ninguna obligatoria (stack 100% open source: FastAPI, PostgreSQL, React) |
| Mantenimiento anual (actualización de parámetros tributarios, soporte) | Equivalente a 1-2 semanas-persona por año |

## 6. Definición de éxito

- Cero recalculo manual en Excel para la cartera de 200 declarantes.
- Paridad de resultados con el archivo actual en una muestra de auditoría (100% de los casos
  probados antes de decomisionar el Excel).
- Tiempo de preparación por declarante reducido de forma medible frente al proceso actual.
- Cero incidentes de pérdida o exposición de datos sensibles durante la operación en servidor local.
