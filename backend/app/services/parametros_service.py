"""
Servicio de parámetros tributarios vigentes.

Resuelve, para un año gravable dado, el conjunto de parámetros que debe usar
el motor de reglas: primero busca en base de datos (`ParametroTributario`
activo); si no existe todavía, cae de vuelta al módulo estático
`parametros_2025.py` — útil en desarrollo local antes de sembrar la base de
datos, y explica por qué ese módulo estático se conserva en el repositorio
en vez de borrarse una vez existe este servicio.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from app.rules_engine import parametros_2025 as _DEFAULTS
from app.rules_engine.semilla_parametros import construir_payload_parametros_2025

if TYPE_CHECKING:
    # Solo se importan para chequeo de tipos (mypy/IDE); en tiempo de
    # ejecución las funciones que los usan hacen el import localmente, para
    # que esta clase adaptadora (ParametrosVigentes) se pueda importar y
    # probar sin tener SQLAlchemy instalado — ver docs/GESTION_PROYECTO.md.
    from sqlalchemy.orm import Session

    from app.models.configuracion import ParametroTributario


class ParametrosNoConfiguradosError(Exception):
    def __init__(self, anio: int):
        self.anio = anio
        super().__init__(
            f"No hay parámetros tributarios configurados para el año gravable {anio}. "
            f"Un Admin debe crearlos desde /configuracion/parametros-tributarios antes de "
            f"liquidar declaraciones de ese año."
        )


class TRMNoConfiguradaError(Exception):
    def __init__(self, fecha: date):
        self.fecha = fecha
        super().__init__(
            f"No hay una TRM cargada para {fecha} ni en ninguna fecha anterior. "
            f"Un Admin debe cargarla desde /configuracion/trm."
        )


class ParametrosVigentes:
    """
    Adaptador que expone los valores de un `ParametroTributario.valores`
    (diccionario con nombres en minúscula, validado por
    `ParametrosTributariosPayload`) con la MISMA interfaz de atributos en
    mayúscula que usa `app/rules_engine/parametros_2025.py`. Esto permite que
    las rutas de la API hagan `P = obtener_parametros_vigentes(db, anio)` y
    sigan escribiendo `P.UVT`, `P.TABLA_TARIFA_UVT`, etc. sin importar si el
    origen fue la base de datos o el módulo estático.
    """

    def __init__(self, datos: dict):
        self.ANIO_GRAVABLE = datos["anio_gravable"]
        self.UVT = datos["uvt"]
        self.TABLA_TARIFA_UVT = self._tabla_a_tuplas(datos["tabla_tarifa"])
        self.LIMITE_RENTA_EXENTA_DEDUCCIONES_PORCENTAJE = datos[
            "limite_renta_exenta_deducciones_porcentaje"
        ]
        self.TOPE_RENTA_EXENTA_DEDUCCIONES_UVT = datos["tope_renta_exenta_deducciones_uvt"]
        self.PORCENTAJE_RENTA_EXENTA_LABORAL = datos["porcentaje_renta_exenta_laboral"]
        self.TOPE_RENTA_EXENTA_LABORAL_UVT = datos["tope_renta_exenta_laboral_uvt"]
        self.TARIFA_RENTA_PRESUNTIVA = datos["tarifa_renta_presuntiva"]
        self.TOPE_VIVIENDA_HABITACION_UVT = datos["tope_vivienda_habitacion_uvt"]
        self.TOPE_ACTIVOS_SECTOR_AGROPECUARIO_UVT = datos["tope_activos_sector_agropecuario_uvt"]
        self.LIMITE_DESCUENTOS_TRIBUTARIOS_PORCENTAJE = datos[
            "limite_descuentos_tributarios_porcentaje"
        ]
        self.TOPE_PAGO_UNICA_CUOTA_UVT = datos["tope_pago_unica_cuota_uvt"]
        self.TARIFA_GANANCIA_OCASIONAL_GENERAL = datos["tarifa_ganancia_ocasional_general"]
        self.TARIFA_GANANCIA_OCASIONAL_LOTERIAS = datos["tarifa_ganancia_ocasional_loterias"]
        self.TOPE_EXENTO_VENTA_CASA_HABITACION_UVT = datos["tope_exento_venta_casa_habitacion_uvt"]
        self.PORCENTAJE_EXENTO_HERENCIA_GENERAL = datos["porcentaje_exento_herencia_general"]
        self.TOPE_EXENTO_HERENCIA_GENERAL_UVT = datos["tope_exento_herencia_general_uvt"]
        self.TOPE_EXENTO_HERENCIA_VIVIENDA_UVT = datos["tope_exento_herencia_vivienda_uvt"]
        self.TOPE_PARTICIPACION_ACCIONES_BOLSA_NO_GRAVADO = datos[
            "tope_participacion_acciones_bolsa_no_gravado"
        ]
        self.FACTORES_AJUSTE_ART73_POR_ANIO = {
            int(k): v for k, v in datos["factores_ajuste_art73_por_anio"].items()
        }
        self.TABLA_TARIFA_DIVIDENDOS_UVT = self._tabla_a_tuplas(datos["tabla_tarifa_dividendos"])
        self.TARIFA_DIVIDENDOS_NO_GRAVADOS_SOCIEDAD = datos["tarifa_dividendos_no_gravados_sociedad"]
        self.TOPE_DEDUCCION_INTERESES_VIVIENDA_UVT = datos["tope_deduccion_intereses_vivienda_uvt"]
        self.TOPE_DEDUCCION_SALUD_UVT_MENSUAL = datos["tope_deduccion_salud_uvt_mensual"]
        self.PORCENTAJE_DEDUCCION_DEPENDIENTES = datos["porcentaje_deduccion_dependientes"]
        self.TOPE_DEDUCCION_DEPENDIENTES_UVT_MENSUAL = datos["tope_deduccion_dependientes_uvt_mensual"]
        self.MAXIMO_DEPENDIENTES_RECONOCIDOS = datos["maximo_dependientes_reconocidos"]
        self.TABLA_EXENCION_CESANTIAS_UVT_MENSUAL = [
            (t["limite_inferior"], t["limite_superior"], t["porcentaje_exento"])
            for t in datos["tabla_exencion_cesantias_uvt_mensual"]
        ]
        self.TARIFA_DESCUENTO_DONACIONES = datos["tarifa_descuento_donaciones"]
        self.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL = datos[
            "sancion_extemporaneidad_porcentaje_mensual"
        ]
        self.SANCION_EXTEMPORANEIDAD_TOPE_PORCENTAJE_IMPUESTO = datos[
            "sancion_extemporaneidad_tope_porcentaje_impuesto"
        ]
        self.SANCION_EXTEMPORANEIDAD_PORCENTAJE_MENSUAL_SOBRE_INGRESOS = datos[
            "sancion_extemporaneidad_porcentaje_mensual_sobre_ingresos"
        ]
        self.SANCION_MINIMA_UVT = datos["sancion_minima_uvt"]
        self.SANCION_CORRECCION_ANTES_EMPLAZAMIENTO_PORCENTAJE = datos[
            "sancion_correccion_antes_emplazamiento_porcentaje"
        ]
        self.SANCION_CORRECCION_DESPUES_EMPLAZAMIENTO_PORCENTAJE = datos[
            "sancion_correccion_despues_emplazamiento_porcentaje"
        ]
        self.ANTICIPO_PORCENTAJE_PRIMERA_VEZ = datos["anticipo_porcentaje_primera_vez"]
        self.ANTICIPO_PORCENTAJE_SEGUNDA_VEZ = datos["anticipo_porcentaje_segunda_vez"]
        self.ANTICIPO_PORCENTAJE_TERCERA_VEZ_EN_ADELANTE = datos[
            "anticipo_porcentaje_tercera_vez_en_adelante"
        ]
        self.LIMITE_ANIOS_COMPENSACION_PERDIDAS = datos["limite_anios_compensacion_perdidas"]

    @staticmethod
    def _tabla_a_tuplas(tabla: list[dict]) -> list[tuple]:
        return [
            (t["limite_inferior"], t["limite_superior"], t["tarifa"], t["base_uvt"])
            for t in tabla
        ]


def obtener_parametros_vigentes(db: Session, anio: int) -> ParametrosVigentes:
    from app.models.configuracion import ParametroTributario

    registro = (
        db.query(ParametroTributario)
        .filter(ParametroTributario.anio == anio, ParametroTributario.activo.is_(True))
        .first()
    )
    if registro is not None:
        return ParametrosVigentes(registro.valores)

    if anio == _DEFAULTS.ANIO_GRAVABLE:
        # Respaldo de desarrollo: todavía no se ha sembrado la base de datos
        # para este año, se usan los valores estáticos del repositorio.
        return ParametrosVigentes(construir_payload_parametros_2025())

    raise ParametrosNoConfiguradosError(anio)


def activar_parametro_tributario(
    db: Session,
    *,
    anio: int,
    valores: dict,
    usuario_id,
    nota: str | None = None,
) -> ParametroTributario:
    """
    Crea un nuevo conjunto de parámetros para el año dado y lo marca como
    activo, desactivando cualquier otro que estuviera activo para ese mismo
    año. Cada cambio queda registrado en la auditoría porque afecta el
    cálculo de TODOS los declarantes de ese año.
    """
    from app.models.configuracion import ParametroTributario
    from app.services.auditoria_service import registrar_auditoria

    activo_anterior = (
        db.query(ParametroTributario)
        .filter(ParametroTributario.anio == anio, ParametroTributario.activo.is_(True))
        .first()
    )
    valores_anteriores = activo_anterior.valores if activo_anterior else None
    if activo_anterior is not None:
        activo_anterior.activo = False
        db.add(activo_anterior)

    nuevo = ParametroTributario(
        anio=anio, valores=valores, activo=True, creado_por_id=usuario_id, nota=nota
    )
    db.add(nuevo)
    db.flush()  # para obtener nuevo.id antes del commit

    registrar_auditoria(
        db,
        usuario_id=usuario_id,
        entidad="parametro_tributario",
        entidad_id=str(nuevo.id),
        accion="activar",
        valores_anteriores=valores_anteriores,
        valores_nuevos=valores,
    )

    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_trm_vigente(db: Session, fecha: date) -> float:
    """
    Devuelve la TRM aplicable a una fecha: la cargada exactamente para esa
    fecha, o si no existe, la más reciente cargada ANTES de esa fecha (los
    fines de semana y festivos no tienen TRM propia y se usa la del último
    día hábil, igual que en la práctica cambiaria real).
    """
    from app.models.configuracion import TRMDiaria

    registro = (
        db.query(TRMDiaria)
        .filter(TRMDiaria.fecha <= fecha)
        .order_by(TRMDiaria.fecha.desc())
        .first()
    )
    if registro is None:
        raise TRMNoConfiguradaError(fecha)
    return float(registro.valor)


def obtener_tasa_interes_mora_vigente(db: Session, fecha: date) -> float:
    from app.models.configuracion import TasaInteresMora

    registro = (
        db.query(TasaInteresMora)
        .filter(
            TasaInteresMora.vigente_desde <= fecha,
        )
        .order_by(TasaInteresMora.vigente_desde.desc())
        .first()
    )
    if registro is None:
        # Respaldo de desarrollo con la tasa referencial del módulo estático.
        return _DEFAULTS.TASA_INTERES_MORA_DIARIA_REFERENCIAL
    if registro.vigente_hasta is not None and registro.vigente_hasta < fecha:
        return _DEFAULTS.TASA_INTERES_MORA_DIARIA_REFERENCIAL
    return float(registro.tasa_diaria)
