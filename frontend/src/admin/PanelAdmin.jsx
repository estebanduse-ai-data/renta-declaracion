import { useState, useEffect, useCallback, useMemo } from "react";
import { obtenerChecklist, toggleDocumento } from "../api.js"; // Act. 1.1

/* ------------------------------------------------------------------ */
/* Tokens de diseño (mismos que main.jsx)                              */
/* ------------------------------------------------------------------ */
const C = {
  bg: "#F7F3EA", surface: "#FFFFFF", border: "#EAE4D4", border2: "#F0ECE1",
  text: "#1E1B15", text2: "#3A342A", muted: "#8A7F68", muted2: "#C9C2AE",
  accent: "#C96442", accentBg: "#FBF1EB", accentBd: "#F0C7C2",
  green: "#4B7B5D", greenBg: "#EAF3EC", greenBd: "#C9E1CE",
  yellow: "#B07D2A", yellowBg: "#FEF9EC", yellowBd: "#F0DFA0",
  red: "#B3261E", redBg: "#FBEAE8", redBd: "#F0C7C2",
  blue: "#2D4FA3", blueBg: "#EEF2FB", blueBd: "#C2D0EF",
};
const FONT = { serif: "'Fraunces', serif", sans: "'Inter', sans-serif" };
const BASE_URL = "http://localhost:8000";

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */
const ESTADOS = {
  borrador:    { label: "Borrador",    bg: C.yellowBg, bd: C.yellowBd, color: C.yellow },
  en_revision: { label: "En revisión", bg: C.blueBg,   bd: C.blueBd,   color: C.blue   },
  presentado:  { label: "Presentado",  bg: C.greenBg,  bd: C.greenBd,  color: C.green  },
  sin_periodo: { label: "Sin iniciar", bg: "#F4F2EE",  bd: C.border,   color: C.muted  },
};

function Chip({ estado }) {
  const e = ESTADOS[estado] || ESTADOS.sin_periodo;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", fontSize: 11, fontWeight: 700,
      fontFamily: FONT.sans, letterSpacing: "0.05em", textTransform: "uppercase",
      padding: "3px 9px", borderRadius: 999, background: e.bg, border: `1px solid ${e.bd}`, color: e.color }}>
      {e.label}
    </span>
  );
}

function Card({ children, style }) {
  return <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, ...style }}>{children}</div>;
}

function MetricaCard({ label, valor, color = C.text, sub }) {
  return (
    <div style={{ background: C.bg, borderRadius: 10, padding: "14px 18px", flex: 1, minWidth: 110 }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: C.muted, fontFamily: FONT.sans, marginBottom: 6 }}>{label}</div>
      <div style={{ fontFamily: FONT.serif, fontSize: 28, fontWeight: 500, color }}>{valor}</div>
      {sub && <div style={{ fontSize: 11, color: C.muted, fontFamily: FONT.sans, marginTop: 3 }}>{sub}</div>}
    </div>
  );
}

function Alerta({ tipo = "info", children }) {
  const t = {
    info:    { bg: C.blueBg,   bd: C.blueBd,   color: C.blue   },
    warn:    { bg: C.yellowBg, bd: C.yellowBd,  color: C.yellow },
    error:   { bg: C.redBg,    bd: C.redBd,     color: C.red    },
    success: { bg: C.greenBg,  bd: C.greenBd,   color: C.green  },
  }[tipo];
  return (
    <div style={{ background: t.bg, border: `1px solid ${t.bd}`, color: t.color,
      fontSize: 13, borderRadius: 8, padding: "10px 14px", fontFamily: FONT.sans }}>
      {children}
    </div>
  );
}

/* ─── Fecha de vencimiento DIAN ──────────────────────────────────────
   Vencimientos 2025 (último dígito NIT, fechas orientativas — el admin
   debe actualizarlas cada año desde la resolución DIAN correspondiente) */
const VENCIMIENTOS_2025 = {
  "1": "2026-08-12", "2": "2026-08-13", "3": "2026-08-14",
  "4": "2026-08-17", "5": "2026-08-18", "6": "2026-08-19",
  "7": "2026-08-20", "8": "2026-08-21", "9": "2026-08-22", "0": "2026-08-25",
};

function vencimientoDeclarante(nit) {
  const ultimo = String(nit).slice(-1);
  return VENCIMIENTOS_2025[ultimo] || null;
}

function diasRestantes(fechaStr) {
  if (!fechaStr) return null;
  const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
  const v = new Date(fechaStr + "T00:00:00");
  return Math.ceil((v - hoy) / 86400000);
}

function ChipVencimiento({ nit }) {
  const fecha = vencimientoDeclarante(nit);
  const dias = diasRestantes(fecha);
  if (dias === null) return null;
  const vencido = dias < 0;
  const urgente = dias >= 0 && dias <= 7;
  const bg   = vencido ? C.redBg   : urgente ? C.yellowBg : C.greenBg;
  const bd   = vencido ? C.redBd   : urgente ? C.yellowBd : C.greenBd;
  const color = vencido ? C.red    : urgente ? C.yellow   : C.green;
  const label = vencido ? `Venció hace ${Math.abs(dias)}d` : dias === 0 ? "Vence hoy" : `${dias}d restantes`;
  return (
    <span style={{ fontSize: 10.5, fontWeight: 700, fontFamily: FONT.sans, padding: "2px 7px",
      borderRadius: 999, background: bg, border: `1px solid ${bd}`, color, whiteSpace: "nowrap" }}>
      {label}
    </span>
  );
}

/* ── Checklist de documentos base ─────────────────────────────────── */
const DOCS_BASE = [
  { key: "rut",           label: "RUT vigente" },
  { key: "cedula",        label: "Cédula de ciudadanía" },
  { key: "cert_ingresos", label: "Certificado de ingresos y retenciones" },
  { key: "extractos",     label: "Extractos bancarios / estado de cuenta" },
  { key: "cert_pension",  label: "Certificado aportes voluntarios / AFC" },
  { key: "cert_salud",    label: "Certificado medicina prepagada" },
  { key: "escrituras",    label: "Escrituras / avalúo predial (si aplica)" },
  { key: "certificado_retencion", label: "Otros certificados de retención" },
];

/* ------------------------------------------------------------------ */
/* PanelAdmin — componente principal                                   */
/* ------------------------------------------------------------------ */
export default function PanelAdmin({ sesion, onCerrarSesion, onIrACartera }) {
  const [tab, setTab] = useState("dashboard");

  /* ── Estado global ── */
  const [declarantes,   setDeclarantes]   = useState([]);
  const [periodosPorId, setPeriodosPorId] = useState({});
  const [docsPorId,     setDocsPorId]     = useState({});   // { [decId]: { [docKey]: bool } }
  const [cargando,      setCargando]      = useState(true);
  const [errorCarga,    setErrorCarga]    = useState(null);

  /* ── Estado importación ── */
  const [archivoXlsx,    setArchivoXlsx]    = useState(null);
  const [importando,     setImportando]      = useState(false);
  const [resultadoImport, setResultadoImport] = useState(null);
  const [errorImport,    setErrorImport]     = useState(null);

  /* ── Cargar datos ── */
  const cargarTodo = useCallback(async () => {
    setCargando(true); setErrorCarga(null);
    try {
      // Act. 1.3 — /declarantes ahora devuelve { total, skip, limit, items }
      const [decResp] = await Promise.all([
        fetch(`${BASE_URL}/declarantes?limit=500`, { headers: { Authorization: `Bearer ${sesion.token}` } }).then(r => r.json()),
      ]);
      const listaDeclarantes = decResp.items ?? decResp; // compatibilidad
      setDeclarantes(listaDeclarantes);

      // Cargar periodos en lotes de 10
      const mapa = {};
      const chunks = [];
      for (let i = 0; i < decResp.length; i += 10) chunks.push(decResp.slice(i, i + 10));
      for (const chunk of chunks) {
        await Promise.all(chunk.map(async (d) => {
          try {
            const periodos = await fetch(`${BASE_URL}/declarantes/${d.id}/periodos`,
              { headers: { Authorization: `Bearer ${sesion.token}` } }).then(r => r.json());
            mapa[d.id] = periodos.find(p => p.anio === 2025) || null;
          } catch (_) { mapa[d.id] = null; }
        }));
      }
      setPeriodosPorId(mapa);

      // Act. 1.1 — cargar checklist desde BD para cada declarante que
      // ya tiene un periodo 2025. Se reemplaza el localStorage.
      const checklistMapa = {};
      await Promise.all(
        Object.entries(mapa)
          .filter(([, periodo]) => periodo !== null)
          .map(async ([decId, periodo]) => {
            try {
              const resp = await obtenerChecklist(sesion.token, decId, periodo.id);
              // Convertir lista de items a mapa { tipo_documento: recibido }
              checklistMapa[decId] = Object.fromEntries(
                resp.items.map(item => [item.tipo_documento, item.recibido])
              );
            } catch (_) {
              checklistMapa[decId] = {};
            }
          })
      );
      setDocsPorId(checklistMapa);
    } catch (err) {
      setErrorCarga(err.message);
    } finally {
      setCargando(false);
    }
  }, [sesion.token]);

  useEffect(() => { cargarTodo(); }, [cargarTodo]);

  /* ── Toggle doc checklist — Act. 1.1: persiste en BD, no en localStorage ── */
  async function toggleDoc(decId, docKey) {
    const periodo = periodosPorId[decId];
    if (!periodo) return; // no hay periodo aún, no se puede guardar
    try {
      const item = await toggleDocumento(sesion.token, decId, periodo.id, docKey);
      setDocsPorId(prev => ({
        ...prev,
        [decId]: { ...(prev[decId] || {}), [docKey]: item.recibido },
      }));
    } catch (err) {
      // Fallo silencioso: el checkbox no cambia de estado si la API falla
      console.error("Error al actualizar checklist:", err.message);
    }
  }

  /* ── Métricas ── */
  const metricas = useMemo(() => {
    const total      = declarantes.length;
    const sinInicio  = declarantes.filter(d => !periodosPorId[d.id]).length;
    const borrador   = declarantes.filter(d => periodosPorId[d.id]?.estado === "borrador").length;
    const enRevision = declarantes.filter(d => periodosPorId[d.id]?.estado === "en_revision").length;
    const presentado = declarantes.filter(d => periodosPorId[d.id]?.estado === "presentado").length;

    // Alertas de vencimiento
    const vencidos  = declarantes.filter(d => {
      const dias = diasRestantes(vencimientoDeclarante(d.nit));
      return dias !== null && dias < 0 && periodosPorId[d.id]?.estado !== "presentado";
    }).length;
    const urgentes  = declarantes.filter(d => {
      const dias = diasRestantes(vencimientoDeclarante(d.nit));
      return dias !== null && dias >= 0 && dias <= 7 && periodosPorId[d.id]?.estado !== "presentado";
    }).length;

    // Docs completos
    const docsCompletos = declarantes.filter(d => {
      const docs = docsPorId[d.id] || {};
      return DOCS_BASE.every(doc => docs[doc.key]);
    }).length;

    const avance = total > 0 ? Math.round((presentado / total) * 100) : 0;
    return { total, sinInicio, borrador, enRevision, presentado, vencidos, urgentes, docsCompletos, avance };
  }, [declarantes, periodosPorId, docsPorId]);

  /* ── Importar Excel ── */
  async function handleImportar() {
    if (!archivoXlsx) return;
    setImportando(true); setResultadoImport(null); setErrorImport(null);
    const fd = new FormData();
    fd.append("archivo", archivoXlsx);
    try {
      const resp = await fetch(`${BASE_URL}/admin/importar-declarantes`, {
        method: "POST",
        headers: { Authorization: `Bearer ${sesion.token}` },
        body: fd,
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || `Error ${resp.status}`);
      }
      const data = await resp.json();
      setResultadoImport(data);
      if (data.importados > 0) cargarTodo();
    } catch (err) {
      setErrorImport(err.message);
    } finally {
      setImportando(false);
    }
  }

  async function descargarPlantilla() {
    const resp = await fetch(`${BASE_URL}/admin/plantilla-declarantes`, {
      headers: { Authorization: `Bearer ${sesion.token}` },
    });
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "plantilla_declarantes.xlsx"; a.click();
    URL.revokeObjectURL(url);
  }

  /* ── Alertas para el dashboard ── */
  const alertas = useMemo(() => {
    const lista = [];
    if (metricas.vencidos > 0)
      lista.push({ tipo: "error", msg: `${metricas.vencidos} declarante(s) con fecha de vencimiento DIAN ya superada y sin presentar.` });
    if (metricas.urgentes > 0)
      lista.push({ tipo: "warn", msg: `${metricas.urgentes} declarante(s) vencen en los próximos 7 días y no están presentados.` });
    if (metricas.sinInicio > 0)
      lista.push({ tipo: "info", msg: `${metricas.sinInicio} declarante(s) sin ningún periodo gravable iniciado.` });
    if (metricas.docsCompletos < metricas.total && metricas.total > 0)
      lista.push({ tipo: "warn", msg: `${metricas.total - metricas.docsCompletos} declarante(s) con checklist de documentos incompleto.` });
    if (metricas.avance === 100 && metricas.total > 0)
      lista.push({ tipo: "success", msg: "¡Toda la cartera está presentada! 🎉" });
    return lista;
  }, [metricas]);

  /* ── Barra de progreso ── */
  function BarraProgreso({ pct }) {
    return (
      <div style={{ height: 8, borderRadius: 99, background: C.border, overflow: "hidden", margin: "8px 0" }}>
        <div style={{ height: "100%", width: `${pct}%`, background: pct === 100 ? C.green : C.accent, borderRadius: 99, transition: "width 0.5s" }} />
      </div>
    );
  }

  /* ── Tabs ── */
  const tabs = [
    { key: "dashboard",  label: "Dashboard"        },
    { key: "cartera",    label: "Cartera"           },
    { key: "documentos", label: "Documentos"        },
    { key: "importar",   label: "Importar Excel"    },
  ];

  /* ─────────────────────────────────────────────────────────────────── */
  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: FONT.sans }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap'); * { box-sizing: border-box; } button:focus-visible { outline: 2px solid ${C.accent}; outline-offset: 2px; }`}</style>

      {/* Header */}
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, padding: "13px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: C.accent, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "#FFF", fontSize: 15, fontWeight: 700, fontFamily: FONT.serif }}>R</span>
          </div>
          <span style={{ fontFamily: FONT.serif, fontSize: 17, fontWeight: 500, color: C.text }}>Renta Declaración</span>
          <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 6, background: C.accentBg, color: C.accent, letterSpacing: "0.06em" }}>ADMIN</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span style={{ fontSize: 13, color: "#6B6355" }}>{sesion.nombre}</span>
          {/* Act. 4.6 — parche admin-contador: acceso a cartera sin cambiar el modelo
              de roles. La solución estructural (roles múltiples) va en Act. 2F.2. */}
          {onIrACartera && (
            <button onClick={onIrACartera} style={{ padding: "7px 14px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surface, color: C.text2, fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
              Ir a cartera
            </button>
          )}
          <button onClick={onCerrarSesion} style={{ padding: "7px 14px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surface, color: C.text2, fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
            Cerrar sesión
          </button>
        </div>
      </div>

      {/* Nav tabs */}
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, padding: "0 32px", display: "flex", gap: 0 }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding: "12px 18px", border: "none", background: "none", cursor: "pointer",
            fontSize: 13.5, fontWeight: tab === t.key ? 700 : 500, fontFamily: FONT.sans,
            color: tab === t.key ? C.accent : C.muted,
            borderBottom: `2px solid ${tab === t.key ? C.accent : "transparent"}`,
          }}>{t.label}</button>
        ))}
        <button onClick={cargarTodo} style={{ marginLeft: "auto", padding: "10px 14px", border: "none", background: "none", cursor: "pointer", fontSize: 12, color: C.muted, fontFamily: FONT.sans }}>
          ↻ Actualizar
        </button>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "28px 20px 60px" }}>
        {cargando && <div style={{ textAlign: "center", color: C.muted, padding: 56, fontSize: 14 }}>Cargando datos…</div>}
        {errorCarga && <Alerta tipo="error">{errorCarga} — <button onClick={cargarTodo} style={{ background: "none", border: "none", color: C.accent, cursor: "pointer", fontWeight: 600 }}>Reintentar</button></Alerta>}

        {/* ══ TAB: DASHBOARD ══════════════════════════════════════════ */}
        {!cargando && tab === "dashboard" && (
          <div>
            <h1 style={{ fontFamily: FONT.serif, fontWeight: 500, fontSize: 28, margin: "0 0 6px 0", color: C.text }}>Dashboard · Año gravable 2025</h1>
            <p style={{ fontSize: 13.5, color: C.muted, margin: "0 0 24px 0" }}>Visión general de la cartera y alertas prioritarias.</p>

            {/* Alertas */}
            {alertas.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
                {alertas.map((a, i) => <Alerta key={i} tipo={a.tipo}>{a.msg}</Alerta>)}
              </div>
            )}

            {/* Métricas */}
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
              <MetricaCard label="Total cartera"    valor={metricas.total}       color={C.text} />
              <MetricaCard label="Sin iniciar"      valor={metricas.sinInicio}   color={C.muted} />
              <MetricaCard label="En borrador"      valor={metricas.borrador}    color={C.yellow} />
              <MetricaCard label="En revisión"      valor={metricas.enRevision}  color={C.blue} />
              <MetricaCard label="Presentados"      valor={metricas.presentado}  color={C.green} />
            </div>

            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 28 }}>
              <MetricaCard label="Vencidos sin presentar" valor={metricas.vencidos}     color={metricas.vencidos > 0 ? C.red : C.muted} />
              <MetricaCard label="Urgentes (≤7 días)"     valor={metricas.urgentes}     color={metricas.urgentes > 0 ? C.yellow : C.muted} />
              <MetricaCard label="Docs completos"          valor={metricas.docsCompletos} color={C.green} sub={`de ${metricas.total}`} />
            </div>

            {/* Barra de avance */}
            <Card style={{ padding: "20px 24px", marginBottom: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: C.text2 }}>Avance de la cartera 2025</span>
                <span style={{ fontFamily: FONT.serif, fontSize: 18, color: metricas.avance === 100 ? C.green : C.accent }}>{metricas.avance}%</span>
              </div>
              <div style={{ height: 10, borderRadius: 99, background: C.border, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${metricas.avance}%`, background: metricas.avance === 100 ? C.green : C.accent, borderRadius: 99, transition: "width 0.6s" }} />
              </div>
              <div style={{ display: "flex", gap: 20, marginTop: 12, fontSize: 12, color: C.muted }}>
                <span>🟡 {metricas.borrador} borrador</span>
                <span>🔵 {metricas.enRevision} revisión</span>
                <span>🟢 {metricas.presentado} presentado</span>
                <span>⚪ {metricas.sinInicio} sin iniciar</span>
              </div>
            </Card>

            {/* Próximos vencimientos */}
            <Card style={{ overflow: "hidden" }}>
              <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, fontWeight: 700, fontSize: 13, color: C.text2 }}>
                Próximos vencimientos DIAN — declarantes no presentados
              </div>
              {declarantes
                .filter(d => periodosPorId[d.id]?.estado !== "presentado")
                .map(d => ({ d, dias: diasRestantes(vencimientoDeclarante(d.nit)), fecha: vencimientoDeclarante(d.nit) }))
                .filter(x => x.dias !== null)
                .sort((a, b) => a.dias - b.dias)
                .slice(0, 10)
                .map(({ d, fecha }, i) => (
                  <div key={d.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 20px", borderTop: i === 0 ? "none" : `1px solid ${C.border2}`, background: i % 2 === 0 ? C.surface : "#FDFCF8" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{d.primer_apellido}, {d.primer_nombre}</div>
                      <div style={{ fontSize: 12, color: C.muted }}>NIT {d.nit}-{d.digito_verificacion}</div>
                    </div>
                    <div style={{ fontSize: 12, color: C.muted }}>{fecha}</div>
                    <Chip estado={periodosPorId[d.id]?.estado || "sin_periodo"} />
                    <ChipVencimiento nit={d.nit} />
                  </div>
                ))}
              {declarantes.filter(d => periodosPorId[d.id]?.estado !== "presentado").length === 0 && (
                <div style={{ padding: 28, textAlign: "center", color: C.muted, fontSize: 14 }}>Toda la cartera está presentada ✅</div>
              )}
            </Card>
          </div>
        )}

        {/* ══ TAB: CARTERA ════════════════════════════════════════════ */}
        {!cargando && tab === "cartera" && (
          <div>
            <h1 style={{ fontFamily: FONT.serif, fontWeight: 500, fontSize: 28, margin: "0 0 20px 0", color: C.text }}>Cartera de declarantes</h1>
            <Card style={{ overflow: "hidden" }}>
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1.2fr 1fr 1fr 1fr 1fr", padding: "9px 20px", background: C.bg, borderBottom: `1px solid ${C.border}` }}>
                {["Declarante", "NIT", "Actividad", "Estado", "Vencimiento", "Docs"].map((h, i) => (
                  <div key={i} style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: C.muted }}>{h}</div>
                ))}
              </div>
              {declarantes.map((d, i) => {
                const estado = periodosPorId[d.id]?.estado || "sin_periodo";
                const docs = docsPorId[d.id] || {};
                const docsOk = DOCS_BASE.filter(doc => docs[doc.key]).length;
                return (
                  <div key={d.id} style={{ display: "grid", gridTemplateColumns: "2fr 1.2fr 1fr 1fr 1fr 1fr", padding: "12px 20px", borderTop: i === 0 ? "none" : `1px solid ${C.border2}`, alignItems: "center", background: i % 2 === 0 ? C.surface : "#FDFCF8" }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{d.primer_apellido}, {d.primer_nombre}</div>
                    </div>
                    <div style={{ fontSize: 13, color: C.text2 }}>{d.nit}<span style={{ color: C.muted2 }}>-{d.digito_verificacion}</span></div>
                    <div style={{ fontSize: 12.5, color: C.muted, textTransform: "capitalize" }}>{d.actividad_economica}</div>
                    <div><Chip estado={estado} /></div>
                    <div><ChipVencimiento nit={d.nit} /></div>
                    <div style={{ fontSize: 12, color: docsOk === DOCS_BASE.length ? C.green : C.muted }}>
                      {docsOk}/{DOCS_BASE.length} docs
                    </div>
                  </div>
                );
              })}
              <div style={{ padding: "10px 20px", borderTop: `1px solid ${C.border}`, background: C.bg, fontSize: 12, color: C.muted, display: "flex", justifyContent: "space-between" }}>
                <span>{declarantes.length} declarantes en total</span>
                <button onClick={cargarTodo} style={{ background: "none", border: "none", color: C.accent, cursor: "pointer", fontSize: 12, fontWeight: 600 }}>↻ Actualizar</button>
              </div>
            </Card>
          </div>
        )}

        {/* ══ TAB: DOCUMENTOS ═════════════════════════════════════════ */}
        {!cargando && tab === "documentos" && (
          <div>
            <h1 style={{ fontFamily: FONT.serif, fontWeight: 500, fontSize: 28, margin: "0 0 6px 0", color: C.text }}>Checklist de documentos base</h1>
            <p style={{ fontSize: 13.5, color: C.muted, margin: "0 0 20px 0" }}>
              Marca los documentos recibidos por declarante. El estado se guarda en la base de datos.
            </p>
            <div style={{ height: 12 }} />
            {declarantes.map((d, di) => {
              const docs = docsPorId[d.id] || {};
              const total = DOCS_BASE.length;
              const ok = DOCS_BASE.filter(doc => docs[doc.key]).length;
              const pct = Math.round((ok / total) * 100);
              return (
                <Card key={d.id} style={{ marginBottom: 12, overflow: "hidden" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "14px 20px", borderBottom: `1px solid ${C.border}`, background: "#FDFCF8" }}>
                    <div style={{ flex: 1 }}>
                      <span style={{ fontSize: 14.5, fontWeight: 700, color: C.text }}>{d.primer_apellido}, {d.primer_nombre}</span>
                      <span style={{ marginLeft: 10, fontSize: 12, color: C.muted }}>NIT {d.nit}-{d.digito_verificacion}</span>
                    </div>
                    <div style={{ width: 120, height: 6, borderRadius: 99, background: C.border, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: pct === 100 ? C.green : C.accent, borderRadius: 99 }} />
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: pct === 100 ? C.green : C.muted, minWidth: 52, textAlign: "right" }}>{ok}/{total}</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
                    {DOCS_BASE.map((doc, i) => (
                      <button key={doc.key} onClick={() => toggleDoc(d.id, doc.key)}
                        style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 16px", background: "none", border: "none", borderTop: i < 2 ? "none" : `1px solid ${C.border2}`, borderLeft: i % 2 === 1 ? `1px solid ${C.border2}` : "none", cursor: "pointer", textAlign: "left" }}>
                        <div style={{ width: 18, height: 18, borderRadius: 5, border: `1.5px solid ${docs[doc.key] ? C.green : C.muted2}`, background: docs[doc.key] ? C.green : "#FFF", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                          {docs[doc.key] && <span style={{ color: "#FFF", fontSize: 11, fontWeight: 900 }}>✓</span>}
                        </div>
                        <span style={{ fontSize: 13, color: docs[doc.key] ? C.text : C.muted, fontWeight: docs[doc.key] ? 600 : 400 }}>{doc.label}</span>
                      </button>
                    ))}
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        {/* ══ TAB: IMPORTAR EXCEL ══════════════════════════════════════ */}
        {tab === "importar" && (
          <div>
            <h1 style={{ fontFamily: FONT.serif, fontWeight: 500, fontSize: 28, margin: "0 0 6px 0", color: C.text }}>Importar declarantes desde Excel</h1>
            <p style={{ fontSize: 13.5, color: C.muted, margin: "0 0 24px 0" }}>Carga masiva de declarantes con su patrimonio inicial. Los NIT ya existentes se omiten.</p>

            {/* Paso 1: descargar plantilla */}
            <Card style={{ padding: "22px 24px", marginBottom: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.text2, marginBottom: 8 }}>Paso 1 — Descarga la plantilla estándar</div>
              <p style={{ fontSize: 13, color: C.muted, margin: "0 0 14px 0" }}>
                El archivo incluye los encabezados exactos que el sistema espera y una fila de ejemplo.
                Completa una fila por declarante y guarda el archivo.
              </p>
              <div style={{ background: C.bg, borderRadius: 8, padding: "10px 14px", marginBottom: 14, fontSize: 12.5, color: C.text2 }}>
                <strong>Columnas obligatorias:</strong> nit · digito_verificacion · primer_apellido · primer_nombre · actividad_economica<br />
                <strong>Columnas opcionales:</strong> patrimonio_bruto_2025 · pasivos_2025 · patrimonio_bruto_2024 · pasivos_2024<br />
                <strong>Valores válidos para actividad_economica:</strong> empleado · independiente · rentista · otro
              </div>
              <button onClick={descargarPlantilla}
                style={{ padding: "9px 18px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surface, color: C.text2, fontSize: 13.5, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
                ⬇ Descargar plantilla_declarantes.xlsx
              </button>
            </Card>

            {/* Paso 2: subir archivo */}
            <Card style={{ padding: "22px 24px", marginBottom: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.text2, marginBottom: 8 }}>Paso 2 — Adjunta el archivo completado</div>
              <input type="file" accept=".xlsx,.xls" onChange={e => { setArchivoXlsx(e.target.files[0]); setResultadoImport(null); setErrorImport(null); }}
                style={{ display: "block", marginBottom: 14, fontSize: 13.5, fontFamily: FONT.sans, color: C.text2 }} />
              {archivoXlsx && <div style={{ fontSize: 12.5, color: C.muted, marginBottom: 14 }}>Archivo seleccionado: <strong>{archivoXlsx.name}</strong> ({(archivoXlsx.size / 1024).toFixed(1)} KB)</div>}
              <button onClick={handleImportar} disabled={!archivoXlsx || importando}
                style={{ padding: "9px 20px", borderRadius: 8, border: "none", background: !archivoXlsx || importando ? C.muted2 : C.accent, color: "#FFF", fontSize: 13.5, fontWeight: 600, cursor: !archivoXlsx || importando ? "default" : "pointer" }}>
                {importando ? "Importando…" : "Importar declarantes"}
              </button>
            </Card>

            {/* Resultado */}
            {errorImport && <Alerta tipo="error">{errorImport}</Alerta>}
            {resultadoImport && (
              <Card style={{ overflow: "hidden" }}>
                <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", gap: 24 }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: C.text2 }}>Resultado de la importación</span>
                  <span style={{ fontSize: 13, color: C.green }}>✅ {resultadoImport.importados} importados</span>
                  <span style={{ fontSize: 13, color: C.muted }}>⏭ {resultadoImport.omitidos} omitidos</span>
                  <span style={{ fontSize: 13, color: resultadoImport.errores > 0 ? C.red : C.muted }}>❌ {resultadoImport.errores} errores</span>
                </div>
                <div style={{ maxHeight: 380, overflowY: "auto" }}>
                  {resultadoImport.detalle.filter(d => !d.ok).map((d, i) => (
                    <div key={i} style={{ display: "flex", gap: 12, padding: "9px 20px", borderTop: `1px solid ${C.border2}`, alignItems: "center", background: C.redBg }}>
                      <span style={{ fontSize: 11.5, color: C.muted, minWidth: 50 }}>Fila {d.fila}</span>
                      <span style={{ fontSize: 13, color: C.text2, minWidth: 100 }}>{d.nit}</span>
                      <span style={{ fontSize: 13, color: C.text2, flex: 1 }}>{d.nombre}</span>
                      <span style={{ fontSize: 12.5, color: C.red }}>{d.mensaje}</span>
                    </div>
                  ))}
                  {resultadoImport.errores === 0 && resultadoImport.omitidos === 0 && (
                    <div style={{ padding: 24, textAlign: "center", color: C.green, fontSize: 14 }}>✅ Todos los registros se importaron correctamente.</div>
                  )}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}