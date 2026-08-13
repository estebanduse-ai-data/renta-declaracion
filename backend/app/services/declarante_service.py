"""
DeclaranteService — Lógica de negocio de declarantes, periodos e importación masiva.

Por qué existe este servicio
─────────────────────────────
Antes de Act. 3.3, toda la lógica de validación, upsert, auditoría y manejo
de casos edge vivía directamente en los handlers de routes_declarantes.py y
routes_admin.py. Eso generaba tres problemas concretos:

  1. Duplicación: el wizard hacía un fetch directo a /declarantes para buscar
     por NIT cuando recibía un 409 — lógica que el propio router ya tenía que
     conocer pero no exponía como función reutilizable.

  2. Acoplamiento: probar la lógica de "crear declarante con auditoría" requería
     levantar FastAPI + el stack HTTP completo. Con el service basta inyectar
     una Session de SQLAlchemy.

  3. Difícil de extender: al agregar endpoints de ingreso_cedular y deduccion
     (que necesitarán la misma lógica de "buscar o crear periodo"), la única
     opción era duplicar o copiar el código del router.

Convenciones de este módulo
────────────────────────────
• Todas las funciones reciben `db: Session` como primer argumento.
• Las funciones que modifican datos también reciben `usuario_id: uuid.UUID`
  para la auditoría — nunca el objeto Usuario completo (evita acoplamiento
  con la sesión HTTP).
• Las excepciones de negocio usan las clases definidas al final del módulo,
  no HTTPException de FastAPI. Los routers convierten esas excepciones en
  respuestas HTTP apropiadas.
• Ninguna función aquí llama a db.commit() al final — el commit lo hace el
  router, que es quien controla la transacción completa de la request.
  Excepción: importar_declarantes_desde_excel hace commit por fila para
  permitir continuar si una fila falla (comportamiento documentado).

Referencias
───────────
  Act. 3.3  — creación de este módulo (service layer)
  routes_declarantes.py  — thin wrapper que delega a este servicio
  routes_admin.py        — importar_declarantes delega a importar_fila()
  docs/ARQUITECTURA.md §6 — deuda técnica resuelta por esta actividad
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ── Excepciones de dominio ─────────────────────────────────────────────────────

class DeclaranteNoEncontradoError(Exception):
    def __init__(self, declarante_id: uuid.UUID):
        self.declarante_id = declarante_id
        super().__init__(f"Declarante {declarante_id} no encontrado.")


class NITDuplicadoError(Exception):
    def __init__(self, nit: str):
        self.nit = nit
        super().__init__(f"Ya existe un declarante con NIT {nit}.")


class PeriodoNoEncontradoError(Exception):
    def __init__(self, periodo_id: uuid.UUID):
        self.periodo_id = periodo_id
        super().__init__(f"Periodo {periodo_id} no encontrado.")


class PeriodoDuplicadoError(Exception):
    def __init__(self, declarante_id: uuid.UUID, anio: int):
        self.declarante_id = declarante_id
        self.anio = anio
        super().__init__(f"El declarante {declarante_id} ya tiene un periodo gravable {anio}.")


class PeriodoPresentadoError(Exception):
    """Se intenta modificar un periodo en estado 'presentado'."""
    def __init__(self, periodo_id: uuid.UUID):
        self.periodo_id = periodo_id
        super().__init__(
            f"El periodo {periodo_id} ya está presentado y no se puede editar. "
            "Si necesitas corregirlo, créalo como una declaración de corrección."
        )


class ArchivoInvalidoError(Exception):
    """El archivo Excel no tiene el formato esperado."""


# ── Helpers internos ───────────────────────────────────────────────────────────

def _get_declarante_o_error(db: "Session", declarante_id: uuid.UUID):
    """Devuelve el Declarante o lanza DeclaranteNoEncontradoError."""
    from app.models.declarante import Declarante
    declarante = db.query(Declarante).filter(Declarante.id == declarante_id).first()
    if declarante is None:
        raise DeclaranteNoEncontradoError(declarante_id)
    return declarante


def _get_periodo_o_error(db: "Session", declarante_id: uuid.UUID, periodo_id: uuid.UUID):
    """Devuelve el PeriodoGravable validando que pertenece al declarante."""
    from app.models.declarante import PeriodoGravable
    periodo = (
        db.query(PeriodoGravable)
        .filter(
            PeriodoGravable.id == periodo_id,
            PeriodoGravable.declarante_id == declarante_id,
        )
        .first()
    )
    if periodo is None:
        raise PeriodoNoEncontradoError(periodo_id)
    return periodo


# ── Operaciones de Declarante ──────────────────────────────────────────────────

def buscar_declarante_por_nit(db: "Session", nit: str):
    """
    Devuelve el Declarante con ese NIT o None si no existe.
    Útil para el wizard cuando recibe un 409 y necesita recuperar el ID.
    """
    from app.models.declarante import Declarante
    return db.query(Declarante).filter(Declarante.nit == nit).first()


def listar_declarantes(
    db: "Session",
    *,
    skip: int = 0,
    limit: int = 200,
    busqueda: str = "",
) -> tuple[int, list]:
    """
    Devuelve (total, items) con paginación y filtro opcional por apellido o NIT.

    `total` refleja el conteo real con el filtro activo, no el tamaño de página.
    Equivale al comportamiento de Act. 1.3 pero sin acoplamiento con Query params
    de FastAPI — se puede llamar desde pruebas de integración directamente.
    """
    from app.models.declarante import Declarante

    query = db.query(Declarante)
    if busqueda:
        termino = f"%{busqueda.strip()}%"
        query = query.filter(
            Declarante.primer_apellido.ilike(termino)
            | Declarante.nit.ilike(termino)
        )

    total = query.count()
    items = (
        query
        .order_by(Declarante.primer_apellido, Declarante.primer_nombre)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return total, items


def crear_declarante(
    db: "Session",
    *,
    nit: str,
    digito_verificacion: str,
    primer_nombre: str,
    primer_apellido: str,
    actividad_economica: str,
    usuario_id: uuid.UUID,
):
    """
    Crea un Declarante nuevo con auditoría.

    Lanza NITDuplicadoError si el NIT ya existe.
    No hace commit — el router es responsable de la transacción.
    """
    from app.models.declarante import Declarante
    from app.services.auditoria_service import registrar_auditoria

    existente = db.query(Declarante).filter(Declarante.nit == nit).first()
    if existente is not None:
        raise NITDuplicadoError(nit)

    datos = dict(
        nit=nit,
        digito_verificacion=digito_verificacion,
        primer_nombre=primer_nombre,
        primer_apellido=primer_apellido,
        actividad_economica=actividad_economica,
    )
    declarante = Declarante(**datos)
    db.add(declarante)
    db.flush()  # obtener el id antes del commit

    registrar_auditoria(
        db,
        usuario_id=usuario_id,
        entidad="declarante",
        entidad_id=str(declarante.id),
        accion="crear",
        valores_nuevos=datos,
    )
    return declarante


def actualizar_declarante(
    db: "Session",
    *,
    declarante_id: uuid.UUID,
    datos: dict,
    usuario_id: uuid.UUID,
):
    """
    Actualiza los campos indicados en `datos` (PATCH semántico).

    Lanza DeclaranteNoEncontradoError si no existe.
    No hace commit.
    """
    from app.services.auditoria_service import registrar_auditoria

    declarante = _get_declarante_o_error(db, declarante_id)

    valores_anteriores = {
        "primer_nombre": declarante.primer_nombre,
        "primer_apellido": declarante.primer_apellido,
        "actividad_economica": declarante.actividad_economica,
    }
    for campo, valor in datos.items():
        setattr(declarante, campo, valor)

    db.add(declarante)
    registrar_auditoria(
        db,
        usuario_id=usuario_id,
        entidad="declarante",
        entidad_id=str(declarante_id),
        accion="actualizar",
        valores_anteriores=valores_anteriores,
        valores_nuevos=datos,
    )
    return declarante


# ── Operaciones de PeriodoGravable ─────────────────────────────────────────────

def crear_periodo(
    db: "Session",
    *,
    declarante_id: uuid.UUID,
    anio: int,
    patrimonio_bruto: float = 0,
    pasivos: float = 0,
) -> object:
    """
    Crea un PeriodoGravable para el declarante y año indicados.

    Lanza:
      - DeclaranteNoEncontradoError si el declarante no existe.
      - PeriodoDuplicadoError si ya tiene un periodo para ese año.

    No hace commit.
    """
    from app.models.declarante import Declarante, PeriodoGravable

    _get_declarante_o_error(db, declarante_id)

    existente = (
        db.query(PeriodoGravable)
        .filter(
            PeriodoGravable.declarante_id == declarante_id,
            PeriodoGravable.anio == anio,
        )
        .first()
    )
    if existente is not None:
        raise PeriodoDuplicadoError(declarante_id, anio)

    periodo = PeriodoGravable(
        declarante_id=declarante_id,
        anio=anio,
        patrimonio_bruto=patrimonio_bruto,
        pasivos=pasivos,
    )
    db.add(periodo)
    db.flush()
    return periodo


def actualizar_periodo(
    db: "Session",
    *,
    declarante_id: uuid.UUID,
    periodo_id: uuid.UUID,
    datos: dict,
    usuario_id: uuid.UUID,
) -> object:
    """
    Actualiza los campos del periodo (PATCH semántico).

    Lanza:
      - PeriodoNoEncontradoError si el periodo no pertenece al declarante.
      - PeriodoPresentadoError si el periodo ya fue presentado.

    No hace commit.
    """
    from app.services.auditoria_service import registrar_auditoria

    periodo = _get_periodo_o_error(db, declarante_id, periodo_id)

    if periodo.estado == "presentado" and datos:
        raise PeriodoPresentadoError(periodo_id)

    valores_anteriores = {
        "estado": periodo.estado,
        "patrimonio_bruto": str(periodo.patrimonio_bruto),
        "pasivos": str(periodo.pasivos),
    }
    for campo, valor in datos.items():
        setattr(periodo, campo, valor)

    db.add(periodo)
    registrar_auditoria(
        db,
        usuario_id=usuario_id,
        entidad="periodo_gravable",
        entidad_id=str(periodo_id),
        accion="actualizar",
        valores_anteriores=valores_anteriores,
        valores_nuevos=datos,
    )
    return periodo


def listar_periodos(db: "Session", declarante_id: uuid.UUID) -> list:
    """Devuelve los periodos gravables de un declarante, ordenados por año descendente."""
    from app.models.declarante import PeriodoGravable
    return (
        db.query(PeriodoGravable)
        .filter(PeriodoGravable.declarante_id == declarante_id)
        .order_by(PeriodoGravable.anio.desc())
        .all()
    )


# ── Importación masiva desde Excel ─────────────────────────────────────────────

COLUMNAS_OBLIGATORIAS = [
    "nit",
    "digito_verificacion",
    "primer_apellido",
    "primer_nombre",
    "actividad_economica",
]

ACTIVIDADES_VALIDAS = {"empleado", "independiente", "rentista", "otro"}


class FilaResultado:
    """Resultado del procesamiento de una fila del Excel."""
    __slots__ = ("fila", "nit", "nombre", "ok", "mensaje")

    def __init__(self, *, fila: int, nit: str, nombre: str, ok: bool, mensaje: str):
        self.fila = fila
        self.nit = nit
        self.nombre = nombre
        self.ok = ok
        self.mensaje = mensaje


class ResultadoImportacion:
    """Resumen completo de la importación masiva."""
    __slots__ = ("total_filas", "importados", "omitidos", "errores", "detalle")

    def __init__(self, *, total_filas: int, importados: int, omitidos: int, errores: int, detalle: list[FilaResultado]):
        self.total_filas = total_filas
        self.importados = importados
        self.omitidos = omitidos
        self.errores = errores
        self.detalle = detalle


def importar_declarantes_desde_excel(
    db: "Session",
    *,
    contenido: bytes,
    nombre_archivo: str,
    usuario_id: uuid.UUID,
) -> ResultadoImportacion:
    """
    Importa declarantes desde el contenido binario de un archivo .xlsx.

    Estrategia por fila:
      - NIT ya registrado → omitido (no sobreescribe).
      - NIT nuevo y datos válidos → crea Declarante + PeriodoGravable 2025
        si hay datos de patrimonio.
      - Error de validación → registrado como error, continúa con la siguiente.

    Hace commit por fila exitosa para permitir recuperación parcial.
    Si la BD tiene un error en una fila, las anteriores ya quedan persistidas.

    Lanza ArchivoInvalidoError si el archivo no se puede leer o le faltan
    columnas — el router convierte esto en HTTP 422.
    """
    import openpyxl
    from app.models.declarante import Declarante, PeriodoGravable
    from app.services.auditoria_service import registrar_auditoria

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception:
        raise ArchivoInvalidoError("No se pudo leer el archivo. Asegúrate de que es un Excel válido.")

    ws = wb.active
    filas = list(ws.iter_rows(values_only=True))
    if not filas:
        raise ArchivoInvalidoError("El archivo está vacío.")

    # Detectar encabezado (primera fila)
    encabezado = [str(c).strip().lower() if c else "" for c in filas[0]]
    columnas_faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in encabezado]
    if columnas_faltantes:
        raise ArchivoInvalidoError(
            f"Columnas faltantes en el encabezado: {', '.join(columnas_faltantes)}. "
            "Descarga la plantilla estándar."
        )

    idx = {col: encabezado.index(col) for col in COLUMNAS_OBLIGATORIAS}

    def _col_idx(nombre: str) -> int | None:
        try:
            return encabezado.index(nombre)
        except ValueError:
            return None

    idx_pb25 = _col_idx("patrimonio_bruto_2025")
    idx_pa25 = _col_idx("pasivos_2025")

    def _celda(fila: tuple, i: int) -> str:
        return str(fila[i]).strip() if fila[i] is not None else ""

    def _celda_num(fila: tuple, i: int | None) -> float | None:
        if i is None or fila[i] is None:
            return None
        try:
            return float(str(fila[i]).replace(",", "").replace(".", "").replace(" ", ""))
        except ValueError:
            return None

    detalle: list[FilaResultado] = []
    importados = omitidos = errores = 0

    for num_fila, fila in enumerate(filas[1:], start=2):
        if not fila or all(c is None for c in fila):
            continue

        nit      = _celda(fila, idx["nit"])
        dv       = _celda(fila, idx["digito_verificacion"])
        apellido = _celda(fila, idx["primer_apellido"])
        nombre   = _celda(fila, idx["primer_nombre"])
        actividad = _celda(fila, idx["actividad_economica"]).lower()
        nombre_completo = f"{apellido}, {nombre}"

        # Validaciones de negocio
        if not nit or not apellido or not nombre:
            detalle.append(FilaResultado(
                fila=num_fila, nit=nit or "—", nombre=nombre_completo,
                ok=False, mensaje="NIT, primer nombre y primer apellido son obligatorios.",
            ))
            errores += 1
            continue

        if not nit.isdigit() or not (6 <= len(nit) <= 10):
            detalle.append(FilaResultado(
                fila=num_fila, nit=nit, nombre=nombre_completo,
                ok=False, mensaje="NIT inválido: debe tener entre 6 y 10 dígitos numéricos.",
            ))
            errores += 1
            continue

        if actividad not in ACTIVIDADES_VALIDAS:
            actividad = "otro"  # fallback permisivo — igual que el comportamiento anterior

        # ¿Ya existe?
        existente = db.query(Declarante).filter(Declarante.nit == nit).first()
        if existente:
            detalle.append(FilaResultado(
                fila=num_fila, nit=nit, nombre=nombre_completo,
                ok=False, mensaje="NIT ya registrado — omitido.",
            ))
            omitidos += 1
            continue

        # Crear declarante
        declarante = Declarante(
            id=uuid.uuid4(),
            nit=nit,
            digito_verificacion=dv or "0",
            primer_nombre=nombre,
            primer_apellido=apellido,
            actividad_economica=actividad,
            creado_en=datetime.now(timezone.utc),
        )
        db.add(declarante)
        db.flush()

        registrar_auditoria(
            db,
            usuario_id=usuario_id,
            entidad="declarante",
            entidad_id=str(declarante.id),
            accion="importar_masivo",
            valores_nuevos={"nit": nit, "nombre": nombre_completo, "origen": nombre_archivo},
        )

        # Crear periodo 2025 si hay datos de patrimonio
        pb25 = _celda_num(fila, idx_pb25)
        pa25 = _celda_num(fila, idx_pa25)
        if pb25 is not None or pa25 is not None:
            db.add(PeriodoGravable(
                id=uuid.uuid4(),
                declarante_id=declarante.id,
                anio=2025,
                estado="borrador",
                patrimonio_bruto=pb25 or 0,
                pasivos=pa25 or 0,
            ))

        # Commit por fila: permite recuperación parcial si la BD falla en una fila posterior
        db.commit()
        importados += 1
        detalle.append(FilaResultado(
            fila=num_fila, nit=nit, nombre=nombre_completo,
            ok=True, mensaje="Importado correctamente.",
        ))

    return ResultadoImportacion(
        total_filas=len(filas) - 1,
        importados=importados,
        omitidos=omitidos,
        errores=errores,
        detalle=detalle,
    )