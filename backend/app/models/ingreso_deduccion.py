"""
Modelos de detalle de ingresos cedulares y deducciones por periodo gravable.

Por qué existen estas tablas
─────────────────────────────
Antes de Act. 1.2, el wizard enviaba totales ya consolidados al endpoint
/liquidacion/calcular. Eso impedía:
  - Recalcular una liquidación sin volver a capturar todos los datos.
  - Guardar historial de cambios por rubro.
  - Construir el mapper del Formulario 210 (Act. 3.1) que necesita los
    valores desagregados por casilla, no solo los totales.

Diseño deliberado
─────────────────
• Un registro por rubro, no una columna por rubro. Así agregar un concepto
  nuevo (por ejemplo, un nuevo tipo de ingreso exento que introduzca una
  reforma) es un dato nuevo, no un ALTER TABLE.
• `tope_aplicado` en Deduccion registra si el motor de reglas recortó el
  valor informado al tope normativo. Esto es trazabilidad obligatoria para
  la revisión del contador y para la auditoría de la DIAN.
• Ambas tablas se limpian y reescriben en cada recálculo del wizard
  (DELETE WHERE periodo_id = X, luego INSERT). No hay versionado aquí;
  el historial de cambios vive en auditoria_cambio.

Referencias
───────────
  Act. 1.2  — creación de este módulo
  Act. 3.1  — mapper resultado → casillas Formulario 210 (consume estas tablas)
  Act. 3.3  — service layer (LiquidacionService usará estas tablas)
  docs/ARQUITECTURA.md §6 — deuda técnica resuelta por esta actividad
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ── Enums de tipo ──────────────────────────────────────────────────────────────

class TipoIngresoCedular(str, enum.Enum):
    """
    Cédulas del E.T. que aplican a personas naturales residentes.
    Cada valor corresponde a una sección del Formulario 210.
    """
    # Cédula general (art. 330 E.T.)
    SALARIOS_Y_HONORARIOS        = "salarios_y_honorarios"
    HONORARIOS_SIN_EMPLEADOS     = "honorarios_sin_empleados"
    SERVICIOS                    = "servicios"
    COMISIONES                   = "comisiones"
    RENDIMIENTOS_FINANCIEROS     = "rendimientos_financieros"
    ARRENDAMIENTOS               = "arrendamientos"
    REGALIAS                     = "regalias"
    EXPLOTACION_IMAGEN           = "explotacion_imagen"
    COMPENSACIONES               = "compensaciones"
    # Cédula de pensiones (art. 337 E.T.)
    PENSIONES_NACIONALES         = "pensiones_nacionales"
    PENSIONES_EXTRANJERAS        = "pensiones_extranjeras"
    # Cédula de dividendos (art. 342 E.T.)
    DIVIDENDOS_GRAVADOS          = "dividendos_gravados"
    DIVIDENDOS_NO_GRAVADOS       = "dividendos_no_gravados"
    # Ingresos no constitutivos de renta
    INGRESO_NO_CONSTITUTIVO      = "ingreso_no_constitutivo"
    # Rentas exentas por tipo
    RENTA_EXENTA_LABORAL         = "renta_exenta_laboral"
    RENTA_EXENTA_CESANTIAS       = "renta_exenta_cesantias"
    RENTA_EXENTA_OTRO            = "renta_exenta_otro"


class TipoDeduccion(str, enum.Enum):
    """
    Deducciones imputables a la cédula general (art. 331-336 E.T.).
    El wizard captura cada una por separado; el motor de reglas aplica
    los topes y los registra en `tope_aplicado`.
    """
    INTERESES_VIVIENDA           = "intereses_vivienda"   # art. 119 E.T.
    INTERESES_ICETEX             = "intereses_icetex"     # art. 119 E.T. (comparte tope con vivienda)
    MEDICINA_PREPAGADA           = "medicina_prepagada"   # art. 387 E.T.
    DEPENDIENTES                 = "dependientes"         # art. 387 E.T.
    AFC                          = "afc"                  # art. 126-4 E.T.
    PENSION_VOLUNTARIA           = "pension_voluntaria"   # art. 126-1 E.T.
    DONACIONES                   = "donaciones"           # art. 257 E.T.
    GRAVAMEN_MOVIMIENTOS_FINANC  = "gravamen_movimientos_financieros"  # art. 115 E.T.
    OTRA                         = "otra"


# ── Modelos ────────────────────────────────────────────────────────────────────

class IngresoCedular(Base):
    """
    Un registro por concepto de ingreso dentro de un periodo gravable.

    Relación: PeriodoGravable 1 → N IngresoCedular
    """
    __tablename__ = "ingreso_cedular"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    periodo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periodo_gravable.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    tipo: Mapped[TipoIngresoCedular] = mapped_column(
        Enum(
            TipoIngresoCedular,
            values_callable=lambda e: [m.value for m in e],
            create_type=False,  # el tipo lo crea la migración 0003
        ),
        nullable=False,
    )

    # Valor informado por el contribuyente en pesos colombianos.
    monto_pesos: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    # Descripción libre opcional (ej: "Empleador: Empresa XYZ S.A.S.")
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relación inversa — navegación opcional
    periodo: Mapped["PeriodoGravable"] = relationship(back_populates="ingresos_cedulares")  # type: ignore[name-defined]


class Deduccion(Base):
    """
    Un registro por concepto de deducción dentro de un periodo gravable.

    Relación: PeriodoGravable 1 → N Deduccion

    El campo `tope_aplicado` indica si el valor informado fue recortado al
    tope normativo por el motor de reglas. El valor efectivamente deducido
    en el cálculo es `monto_efectivo_pesos`; el valor original informado
    por el contribuyente se conserva en `monto_informado_pesos` para
    transparencia y revisión del contador.
    """
    __tablename__ = "deduccion"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    periodo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periodo_gravable.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    tipo: Mapped[TipoDeduccion] = mapped_column(
        Enum(
            TipoDeduccion,
            values_callable=lambda e: [m.value for m in e],
            create_type=False,  # el tipo lo crea la migración 0003
        ),
        nullable=False,
    )

    # Valor original informado por el contribuyente.
    monto_informado_pesos: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    # Valor efectivamente aplicado tras los topes normativos.
    # Igual a monto_informado_pesos si no se aplicó ningún tope.
    monto_efectivo_pesos: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    # True si el motor de reglas recortó monto_informado al tope normativo.
    tope_aplicado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Tope normativo que se aplicó, expresado en pesos (para trazabilidad).
    tope_valor_pesos: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relación inversa
    periodo: Mapped["PeriodoGravable"] = relationship(back_populates="deducciones")  # type: ignore[name-defined]