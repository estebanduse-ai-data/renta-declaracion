/**
 * useWizardApi — IDs persistidos en BD, llamadas a la API y orquestación.
 *
 * Por qué existe este hook
 * ─────────────────────────
 * En el wizard original, 8 useState de estado de API (guardando, errorApi,
 * resultadoLiquidacion, cargandoLiquidacion, errorLiquidacion,
 * liquidacionPersistida, guardandoFinal, errorFinal) más las funciones
 * persistirSiCorresponde() y llamarLiquidacion() estaban mezclados con
 * el estado de formulario y el render. Eso causaba:
 *
 *   1. `irSiguiente()` tenía que conocer tanto la validación como la
 *     persistencia — dos responsabilidades en una sola función.
 *   2. Testear la lógica de "si ya existe el periodo, actualizar en vez
 *     de crear" requería renderizar el componente completo.
 *   3. El FIX 1 (recuperar declarante por NIT en un 409) usaba fetch
 *     directo con la URL hardcodeada en medio de la función irSiguiente.
 *     Ese fetch ahora usa listarDeclarantes() de api.js correctamente.
 *
 * Correcciones aplicadas vs. el código original
 * ───────────────────────────────────────────────
 * FIX 1 (recuperación de declarante existente):
 *   Antes:  fetch('http://localhost:8000/declarantes', ...).then(r => r.json()).find(...)
 *           — hacía un fetch directo, sin paginación, con URL hardcodeada.
 *   Ahora:  listarDeclarantes(token, { busqueda: nit }) de api.js.
 *           Más robusto, no depende de cargar toda la lista.
 *
 * FIX 2 (periodo existente al abrir el wizard):
 *   Sin cambios de lógica — el useEffect de recuperación está aquí,
 *   separado del formulario. Más fácil de leer.
 *
 * FIX 3 (liquidación + persistencia):
 *   Sin cambios de lógica — llamarLiquidacion() recibe decId y perId
 *   para el caso en que se acaban de crear en el mismo paso.
 *
 * Lo que NO contiene este hook
 * ─────────────────────────────
 * • Estado del formulario (eso va en useWizardForm).
 * • Validaciones de campos (ídem).
 * • Cálculos derivados de patrimonio e ingresos (ídem).
 * • Render de ningún tipo.
 */

import { useCallback, useEffect, useState } from "react";
import {
  actualizarPeriodo,
  calcularLiquidacion,
  crearDeclarante,
  crearPeriodo,
  listarDeclarantes,
  listarPeriodos,
  obtenerParametrosPublicos,
} from "../api.js";
import { ANIO_GRAVABLE, PARAMETROS_FALLBACK } from "./wizardConfig.js";

/**
 * @param {object}   declarante        Declarante pre-cargado o null
 * @param {object}   sesion            { token }
 * @param {function} onSesionExpirada  Callback al recibir 401
 * @param {object}   totales           Valores derivados de useWizardForm necesarios
 *                                     para la llamada a liquidación
 */
export function useWizardApi(declarante, sesion, onSesionExpirada, totales) {
  const {
    datos,
    totalIngresosBrutos,
    totalDeducciones,
    ingresoSalarios,
    totalRetenciones,
    patrimonioLiquidoAnterior,
    patrimonioBrutoEfectivo,
    pasivosEfectivos,
  } = totales;

  // ── IDs persistidos ────────────────────────────────────────────────────────
  const [declaranteId, setDeclaranteId] = useState(declarante?.id ?? null);
  const [periodoId,    setPeriodoId]    = useState(null);

  // ── Parámetros tributarios ─────────────────────────────────────────────────
  const [parametros, setParametros] = useState(PARAMETROS_FALLBACK);
  useEffect(() => {
    obtenerParametrosPublicos(sesion.token, ANIO_GRAVABLE)
      .then(p => setParametros(p))
      .catch(() => {
        console.warn(`[wizard] No se pudieron cargar parámetros ${ANIO_GRAVABLE} — usando fallback.`);
      });
  }, [sesion.token]);

  // ── Recuperar periodo existente al abrir el wizard (FIX 2) ────────────────
  useEffect(() => {
    if (!declarante?.id || periodoId) return;
    (async () => {
      try {
        const periodos = await listarPeriodos(sesion.token, declarante.id);
        const p2025 = periodos.find(p => p.anio === ANIO_GRAVABLE);
        if (p2025) setPeriodoId(p2025.id);
      } catch (_) { /* no bloquea la apertura del wizard */ }
    })();
  }, [declarante?.id, sesion.token, periodoId]);

  // ── Estado de UI de API ────────────────────────────────────────────────────
  const [guardando,              setGuardando]              = useState(false);
  const [errorApi,               setErrorApi]               = useState(null);
  const [resultadoLiquidacion,   setResultadoLiquidacion]   = useState(null);
  const [cargandoLiquidacion,    setCargandoLiquidacion]    = useState(false);
  const [errorLiquidacion,       setErrorLiquidacion]       = useState(null);
  const [liquidacionPersistida,  setLiquidacionPersistida]  = useState(false);
  const [guardandoFinal,         setGuardandoFinal]         = useState(false);
  const [errorFinal,             setErrorFinal]             = useState(null);

  // ── Llamada a liquidación + persistencia (FIX 3) ──────────────────────────
  const llamarLiquidacion = useCallback(async (decId, perId) => {
    setCargandoLiquidacion(true);
    setErrorLiquidacion(null);
    setLiquidacionPersistida(false);
    try {
      const resultado = await calcularLiquidacion(sesion.token, {
        anio_gravable:                    ANIO_GRAVABLE,
        total_ingresos_brutos_pesos:      totalIngresosBrutos,
        deducciones_imputables_pesos:     totalDeducciones,
        ingreso_salarios_pesos:           parseFloat(ingresoSalarios) || 0,
        total_retenciones_pesos:          totalRetenciones,
        patrimonio_liquido_anterior_pesos: patrimonioLiquidoAnterior,
        periodo_id:                       perId ?? periodoId ?? null,
      });
      setResultadoLiquidacion(resultado);
      if (resultado.persistido) setLiquidacionPersistida(true);
    } catch (err) {
      if (err.code === "UNAUTHORIZED") { onSesionExpirada(); return; }
      setErrorLiquidacion(err.message);
    } finally {
      setCargandoLiquidacion(false);
    }
  }, [
    sesion.token,
    totalIngresosBrutos, totalDeducciones, ingresoSalarios,
    totalRetenciones, patrimonioLiquidoAnterior, periodoId,
    onSesionExpirada,
  ]);

  // ── Persistencia al avanzar entre pasos ───────────────────────────────────

  /**
   * Persiste en BD lo que corresponde al paso actual.
   *
   * Devuelve { ok: boolean, decId?, perId? } para que irSiguiente()
   * sepa si puede avanzar y con qué IDs llamar a la liquidación.
   *
   * @param {string} pasoId   ID del paso actual (ej: "datos", "patrimonio")
   */
  async function persistirSiCorresponde(pasoId) {

    // ── PASO DATOS: crear declarante si no existe ──────────────────────────
    if (pasoId === "datos" && !declaranteId) {
      setGuardando(true);
      setErrorApi(null);
      try {
        const nuevo = await crearDeclarante(sesion.token, {
          nit:                datos.nit,
          digito_verificacion: datos.dv || "0",
          primer_nombre:      datos.primerNombre,
          primer_apellido:    datos.primerApellido,
          actividad_economica: datos.actividadEconomica,
        });
        setDeclaranteId(nuevo.id);
        return { ok: true, decId: nuevo.id };

      } catch (err) {
        if (err.code === "UNAUTHORIZED") { onSesionExpirada(); return { ok: false }; }

        // FIX 1 — El declarante ya existe: recuperar por NIT con busqueda param
        // Antes usaba fetch directo sin paginación. Ahora usa listarDeclarantes()
        // con filtro de búsqueda para no cargar toda la lista.
        if (err.message.includes("409") || err.message.toLowerCase().includes("ya existe")) {
          try {
            const respuesta = await listarDeclarantes(sesion.token, { busqueda: datos.nit });
            const encontrado = respuesta.items?.find(d => d.nit === datos.nit);
            if (encontrado) {
              setDeclaranteId(encontrado.id);
              return { ok: true, decId: encontrado.id };
            }
          } catch (_) { /* si falla el fallback, caemos al error genérico */ }
          setErrorApi("El declarante ya existe pero no se pudo recuperar su ID. Selecciónalo desde el listado.");
          return { ok: false };
        }

        setErrorApi(`No se pudo guardar el declarante: ${err.message}`);
        return { ok: false };

      } finally {
        setGuardando(false);
      }
    }

    // ── PASO PATRIMONIO: crear o actualizar periodo ────────────────────────
    if (pasoId === "patrimonio") {
      const idAUsar = declaranteId;
      if (!idAUsar) return { ok: true }; // sin declarante aún, no hay nada que persistir

      setGuardando(true);
      setErrorApi(null);

      // Si ya tenemos periodoId (recuperado al abrir el wizard), actualizar
      if (periodoId) {
        try {
          await actualizarPeriodo(sesion.token, idAUsar, periodoId, {
            patrimonio_bruto: patrimonioBrutoEfectivo,
            pasivos:          pasivosEfectivos,
          });
          return { ok: true, perId: periodoId };
        } catch (err) {
          if (err.code === "UNAUTHORIZED") { onSesionExpirada(); return { ok: false }; }
          setErrorApi(`No se pudo actualizar el patrimonio: ${err.message}`);
          return { ok: false };
        } finally {
          setGuardando(false);
        }
      }

      // Si no existe periodo, crear uno nuevo
      try {
        const periodo = await crearPeriodo(sesion.token, idAUsar, {
          anio:             ANIO_GRAVABLE,
          patrimonio_bruto: patrimonioBrutoEfectivo,
          pasivos:          pasivosEfectivos,
        });
        setPeriodoId(periodo.id);
        return { ok: true, perId: periodo.id };

      } catch (err) {
        if (err.code === "UNAUTHORIZED") { onSesionExpirada(); return { ok: false }; }

        // Si el periodo ya existe (ej. el usuario volvió atrás y avanzó de nuevo)
        if (err.message.toLowerCase().includes("ya tiene un periodo")) {
          try {
            const periodos = await listarPeriodos(sesion.token, idAUsar);
            const p2025 = periodos.find(p => p.anio === ANIO_GRAVABLE);
            if (p2025) {
              setPeriodoId(p2025.id);
              return { ok: true, perId: p2025.id };
            }
          } catch (_) { /* si falla el fallback, caemos al error genérico */ }
        }

        setErrorApi(`No se pudo guardar el patrimonio: ${err.message}`);
        return { ok: false };

      } finally {
        setGuardando(false);
      }
    }

    // Todos los demás pasos no necesitan persistencia antes de avanzar
    return { ok: true };
  }

  // ── Marcar en revisión (último paso) ──────────────────────────────────────

  async function marcarEnRevision() {
    if (!periodoId || !declaranteId) return;
    setGuardandoFinal(true);
    setErrorFinal(null);
    try {
      await actualizarPeriodo(sesion.token, declaranteId, periodoId, { estado: "en_revision" });
      return { ok: true }; // el componente raíz llama onVolver()
    } catch (err) {
      if (err.code === "UNAUTHORIZED") { onSesionExpirada(); return { ok: false }; }
      setErrorFinal(err.message);
      return { ok: false };
    } finally {
      setGuardandoFinal(false);
    }
  }

  // ── API pública del hook ───────────────────────────────────────────────────

  return {
    // IDs
    declaranteId,
    periodoId,

    // Parámetros tributarios (cargados desde la API)
    parametros,

    // Estado de guardado
    guardando,
    errorApi,      setErrorApi,

    // Liquidación
    resultadoLiquidacion,
    cargandoLiquidacion,
    errorLiquidacion,
    liquidacionPersistida,

    // Marcar en revisión
    guardandoFinal,
    errorFinal,

    // Acciones
    persistirSiCorresponde,
    llamarLiquidacion,
    marcarEnRevision,
  };
}