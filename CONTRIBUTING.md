# Guía de contribución

## Flujo de ramas

- `main` — siempre desplegable, protegida contra push directo.
- `develop` — rama de integración, base de las ramas de trabajo.
- `feature/<descripcion-corta>` — nueva funcionalidad, sale de `develop`.
- `fix/<descripcion-corta>` — corrección de errores, sale de `develop` (o de `main` si es un hotfix urgente).

## Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: agrega cálculo de ganancias ocasionales por venta de acciones
fix: corrige límite de renta exenta laboral cuando el ingreso es cero
docs: actualiza plan de trabajo con cronograma revisado
test: agrega casos de prueba para tramos límite de la tabla de tarifa
refactor: separa parámetros 2026 del motor de reglas
chore: actualiza dependencias del backend
```

## Antes de abrir un Pull Request

1. El backend debe pasar `pytest -v` sin fallos.
2. Todo cambio en `app/rules_engine` **debe** venir acompañado de pruebas nuevas o
   actualizadas — es la capa de mayor riesgo del proyecto (ver `docs/RIESGOS.md`).
3. Si el cambio afecta parámetros tributarios de un año gravable ya publicado, crear un
   archivo `parametros_<anio>.py` nuevo en vez de modificar el existente.
4. Actualizar `docs/FALTANTES.md` si el cambio cierra o abre una brecha documentada ahí.

## Revisión de código

Todo Pull Request hacia `main` o `develop` requiere al menos una aprobación. Los cambios en
`app/rules_engine` o en `parametros_*.py` deben ser revisados, en lo posible, por alguien con
conocimiento tributario funcional (el contador o un delegado), no solo por otro desarrollador.
