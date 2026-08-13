/**
 * DeclaracionRentaWizard.jsx — componente raíz del asistente guiado.
 *
 * Responsabilidades (y solo estas):
 *   1. Controlar el paso activo y la navegación (irSiguiente, irAtras, irAPaso).
 *   2. Delegar estado del formulario a useWizardForm.
 *   3. Delegar llamadas a la API y persistencia a useWizardApi.
 *   4. Renderizar el layout: header, rail de pasos y panel de contenido.
 *   5. Renderizar el paso activo pasándole exactamente las props que necesita.
 *
 * Lo que NO hace este componente:
 *   • Calcular patrimonio líquido, totales de ingresos, renta exenta (→ useWizardForm)
 *   • Llamar a la API, manejar 409, recuperar IDs (→ useWizardApi)
 *   • Definir las constantes PASOS, ANIO_GRAVABLE (→ wizardConfig.js)
 *
 * Antes de DT-2: 1044 líneas con todo mezclado.
 * Después de DT-2: ~280 líneas de render puro + dos hooks especializados.
 */

import { useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  ChevronLeft,
  ChevronRight,
  Receipt,
} from "lucide-react";

import { PASOS } from "./wizardConfig.js";
import { useWizardApi } from "./useWizardApi.js";
import { useWizardForm } from "./useWizardForm.js";

// Pasos — componentes individuales (sin cambios de lógica, solo movidos de archivo)
import PasoPerfil     from "./pasos/PasoPerfil.jsx";
import PasoDatos      from "./pasos/PasoDatos.jsx";
import PasoPatrimonio from "./pasos/PasoPatrimonio.jsx";
import PasoIngresos   from "./pasos/PasoIngresos.jsx";
import PasoPresuntiva from "./pasos/PasoPresuntiva.jsx";
import PasoLiquidacion from "./pasos/PasoLiquidacion.jsx";
import PasoResumen    from "./pasos/PasoResumen.jsx";

// Utilidades de UI compartidas (movidas desde el wizard original)
import { formatCOP, Spinner } from "./ui/wizardUi.jsx";

export default function DeclaracionRentaWizard({ sesion, declarante, onVolver, onSesionExpirada }) {

  // ── Navegación ─────────────────────────────────────────────────────────────
  const [pasoActivo, setPasoActivo] = useState(0);

  // ── Formulario y cálculos derivados ───────────────────────────────────────
  const form = useWizardForm(declarante, null /* parametros se pasan abajo */);
  const {
    perfil, setPerfil,
    datos, setDatos,
    patrimonio, setPatrimonio,
    ingresos, setIngresos,
    errores, setErrores,
    tocado, setTocado,
    // cálculos derivados
    totalActivos2025, totalPasivos2025,
    patrimonioLiquidoAnterior,
    patrimonioBrutoEfectivo, pasivosEfectivos, patrimonioLiquido,
    totalIngresosBrutos, totalRetenciones, totalDeducciones,
    rentaLiquidaCedular, rentaPresuntivaPesos,
    // validación
    validarPaso,
  } = form;

  // ── API y persistencia ────────────────────────────────────────────────────
  const api = useWizardApi(declarante, sesion, onSesionExpirada, {
    datos,
    totalIngresosBrutos,
    totalDeducciones,
    ingresoSalarios:          ingresos.salarios,
    totalRetenciones,
    patrimonioLiquidoAnterior,
    patrimonioBrutoEfectivo,
    pasivosEfectivos,
  });
  const {
    declaranteId, periodoId,
    parametros,
    guardando, errorApi,
    resultadoLiquidacion, cargandoLiquidacion, errorLiquidacion, liquidacionPersistida,
    guardandoFinal, errorFinal,
    persistirSiCorresponde, llamarLiquidacion, marcarEnRevision,
  } = api;

  // Reasignar form con parametros ya disponibles
  // (necesario porque useWizardForm necesita parametros para los cálculos de renta exenta)
  const formConParametros = useWizardForm(declarante, parametros);

  // ── Navegación entre pasos ────────────────────────────────────────────────

  async function irSiguiente() {
    const err = validarPaso(pasoActivo);
    setErrores(err);
    setTocado(t => ({ ...t, [pasoActivo]: true }));
    if (Object.keys(err).length > 0) return;

    const pasoId    = PASOS[pasoActivo].id;
    const resultado = await persistirSiCorresponde(pasoId);
    if (!resultado.ok) return;

    const siguienteIdx = Math.min(pasoActivo + 1, PASOS.length - 1);

    // Si el siguiente paso es liquidación, lanzar el cálculo inmediatamente
    if (PASOS[siguienteIdx].id === "liquidacion") {
      setPasoActivo(siguienteIdx);
      setErrores({});
      await llamarLiquidacion(resultado.decId, resultado.perId);
      return;
    }

    setPasoActivo(siguienteIdx);
    setErrores({});
  }

  function irAtras() {
    setErrores({});
    setPasoActivo(p => Math.max(p - 1, 0));
  }

  function irAPaso(idx) {
    if (idx <= pasoActivo || tocado[pasoActivo]) {
      setErrores({});
      setPasoActivo(idx);
    }
  }

  async function handleMarcarEnRevision() {
    const resultado = await marcarEnRevision();
    if (resultado?.ok) onVolver();
  }

  const idPaso     = PASOS[pasoActivo].id;
  const esUltimoPaso = pasoActivo === PASOS.length - 1;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", background: "#F7F3EA", minHeight: "100vh", color: "#23201A" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>

      {/* Header */}
      <div style={{ background: "#FFF", borderBottom: "1px solid #EAE4D4", padding: "12px 32px", display: "flex", alignItems: "center", gap: 12 }}>
        <button onClick={onVolver}
          style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, color: "#8A7F68", fontSize: 13, fontFamily: "'Inter', sans-serif", padding: 0 }}>
          <ArrowLeft size={14} /> Declarantes
        </button>
        <span style={{ color: "#C9C2AE", fontSize: 13 }}>›</span>
        <span style={{ fontSize: 13, color: "#3A342A", fontWeight: 600, fontFamily: "'Inter', sans-serif" }}>
          {datos.primerApellido ? `${datos.primerApellido}, ${datos.primerNombre}` : "Nuevo declarante"}
        </span>
        {periodoId && (
          <span style={{ marginLeft: "auto", fontSize: 11.5, color: "#4B7B5D", fontFamily: "'Inter', sans-serif", display: "flex", alignItems: "center", gap: 4 }}>
            <Check size={11} /> Periodo {ANIO_GRAVABLE} guardado
          </span>
        )}
      </div>

      <div style={{ maxWidth: 980, margin: "0 auto", padding: "28px 20px 60px" }}>

        {/* Título */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: "#C96442", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Receipt size={16} color="#FFF" />
            </div>
            <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 12.5, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "#8A7F68" }}>
              Formulario 210 · Año gravable {ANIO_GRAVABLE}
            </span>
          </div>
          <h1 style={{ fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 32, margin: 0, color: "#1E1B15" }}>
            Declaración de renta — asistente guiado
          </h1>
        </div>

        {/* Banner de error de API */}
        {errorApi && (
          <div style={{ background: "#FBEAE8", border: "1px solid #F0C7C2", color: "#8C231C", fontSize: 13, borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontFamily: "'Inter', sans-serif", display: "flex", gap: 8 }}>
            <AlertCircle size={15} style={{ marginTop: 1, flexShrink: 0 }} /> {errorApi}
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 28 }}>

          {/* Rail de pasos */}
          <div>
            {PASOS.map((p, idx) => {
              const activo = idx === pasoActivo;
              const hecho  = idx < pasoActivo;
              return (
                <button key={p.id} onClick={() => irAPaso(idx)}
                  style={{
                    display: "flex", alignItems: "center", gap: 10,
                    width: "100%", textAlign: "left",
                    background: activo ? "#FFFFFF" : "transparent",
                    border: "none",
                    cursor: idx <= pasoActivo || tocado[pasoActivo] ? "pointer" : "default",
                    padding: "10px 8px", borderRadius: 8, marginBottom: 2,
                    opacity: idx > pasoActivo && !tocado[pasoActivo] ? 0.45 : 1,
                    boxShadow: activo ? "0 1px 3px rgba(0,0,0,0.06)" : "none",
                  }}>
                  <div style={{
                    width: 24, height: 24, borderRadius: 999,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0, fontSize: 11.5, fontWeight: 700,
                    fontFamily: "'Inter', sans-serif",
                    background: hecho ? "#4B7B5D" : activo ? "#C96442" : "#EAE4D4",
                    color: hecho || activo ? "#FFF" : "#8A7F68",
                  }}>
                    {hecho ? <Check size={13} /> : p.numero}
                  </div>
                  <span style={{ fontSize: 13.5, fontWeight: activo ? 600 : 500, color: activo ? "#1E1B15" : "#5B5344" }}>
                    {p.titulo}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Panel de contenido */}
          <div style={{ background: "#FFFFFF", border: "1px solid #EAE4D4", borderRadius: 14, padding: "28px 32px", boxShadow: "0 1px 2px rgba(0,0,0,0.03)", minHeight: 480 }}>

            {idPaso === "perfil" && (
              <PasoPerfil perfil={perfil} setPerfil={setPerfil} />
            )}
            {idPaso === "datos" && (
              <PasoDatos
                datos={datos} setDatos={setDatos}
                errores={errores}
                modoEdicion={!!declarante?.id}
              />
            )}
            {idPaso === "patrimonio" && (
              <PasoPatrimonio
                patrimonio={patrimonio} setPatrimonio={setPatrimonio}
                errores={errores}
                patrimonioLiquido={patrimonioLiquido}
                patrimonioLiquidoAnterior={patrimonioLiquidoAnterior}
              />
            )}
            {idPaso === "ingresos" && (
              <PasoIngresos
                perfil={perfil}
                ingresos={ingresos} setIngresos={setIngresos}
                errores={errores}
                totalIngresosBrutos={totalIngresosBrutos}
                totalRetenciones={totalRetenciones}
                totalDeducciones={totalDeducciones}
              />
            )}
            {idPaso === "presuntiva" && (
              <PasoPresuntiva
                patrimonioLiquidoAnterior={patrimonioLiquidoAnterior}
                rentaPresuntivaPesos={rentaPresuntivaPesos}
                rentaLiquidaCedular={rentaLiquidaCedular}
              />
            )}
            {idPaso === "liquidacion" && (
              <PasoLiquidacion
                resultadoApi={resultadoLiquidacion}
                cargandoApi={cargandoLiquidacion}
                errorApi={errorLiquidacion}
                uvt={resultadoLiquidacion?.uvt_utilizada}
                persistida={liquidacionPersistida}
                parametros={parametros}
              />
            )}
            {idPaso === "resumen" && (
              <PasoResumen
                datos={datos}
                patrimonioLiquido={patrimonioLiquido}
                totalIngresosBrutos={totalIngresosBrutos}
                totalDeducciones={totalDeducciones}
                resultadoApi={resultadoLiquidacion}
                periodoId={periodoId}
                guardandoFinal={guardandoFinal}
                errorFinal={errorFinal}
              />
            )}

            {/* Error general de validación (paso ingresos) */}
            {errores.general && (
              <div style={{ display: "flex", gap: 8, alignItems: "flex-start", background: "#FBEAE8", border: "1px solid #F0C7C2", color: "#8C231C", fontSize: 13, borderRadius: 8, padding: "10px 12px", marginTop: 8 }}>
                <AlertCircle size={15} style={{ marginTop: 1, flexShrink: 0 }} /> {errores.general}
              </div>
            )}

            {/* Navegación */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 32, paddingTop: 20, borderTop: "1px solid #EFEAE0" }}>
              <button onClick={irAtras} disabled={pasoActivo === 0}
                style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 16px", borderRadius: 8, border: "1px solid #DAD3C0", background: "#FFF", color: pasoActivo === 0 ? "#C9C2AE" : "#3A342A", fontSize: 13.5, fontWeight: 600, cursor: pasoActivo === 0 ? "default" : "pointer" }}>
                <ChevronLeft size={15} /> Anterior
              </button>

              {guardando && <Spinner />}

              {!esUltimoPaso ? (
                <button onClick={irSiguiente} disabled={guardando}
                  style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 18px", borderRadius: 8, border: "none", background: guardando ? "#D9A890" : "#C96442", color: "#FFF", fontSize: 13.5, fontWeight: 600, cursor: guardando ? "default" : "pointer" }}>
                  Continuar <ChevronRight size={15} />
                </button>
              ) : (
                <button onClick={handleMarcarEnRevision} disabled={guardandoFinal || !periodoId}
                  style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 18px", borderRadius: 8, border: "none", background: guardandoFinal || !periodoId ? "#7FA98D" : "#4B7B5D", color: "#FFF", fontSize: 13.5, fontWeight: 600, cursor: guardandoFinal || !periodoId ? "default" : "pointer" }}>
                  <Check size={15} /> {guardandoFinal ? "Guardando…" : "Marcar en revisión"}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}