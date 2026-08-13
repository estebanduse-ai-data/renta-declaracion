import { useState, useCallback, useEffect, useMemo } from "react";
import ReactDOM from "react-dom/client";
import { login, listarDeclarantes, crearDeclarante, listarPeriodos } from "./api.js";
import DeclaracionRentaWizard from "./wizard/DeclaracionRentaWizard.jsx";
import PanelAdmin from "./admin/PanelAdmin.jsx";

/* ------------------------------------------------------------------ */
/* Tokens de diseño                                                    */
/* ------------------------------------------------------------------ */
const C = {
  bg:       "#F7F3EA",
  surface:  "#FFFFFF",
  border:   "#EAE4D4",
  border2:  "#F0ECE1",
  text:     "#1E1B15",
  text2:    "#3A342A",
  muted:    "#8A7F68",
  muted2:   "#C9C2AE",
  accent:   "#C96442",
  accentBg: "#FBF1EB",
  green:    "#4B7B5D",
  greenBg:  "#EAF3EC",
  greenBd:  "#C9E1CE",
  yellow:   "#B07D2A",
  yellowBg: "#FEF9EC",
  yellowBd: "#F0DFA0",
  red:      "#B3261E",
  redBg:    "#FBEAE8",
  redBd:    "#F0C7C2",
};

const FONT = { serif: "'Fraunces', serif", sans: "'Inter', sans-serif" };

const inputBase = {
  width: "100%", fontFamily: FONT.sans, fontSize: 14.5,
  padding: "10px 12px", borderRadius: 8, border: `1px solid ${C.border}`,
  background: C.surface, color: C.text2, outline: "none", boxSizing: "border-box",
};

const btnPrimario = {
  padding: "9px 18px", borderRadius: 8, border: "none",
  background: C.accent, color: "#FFF", fontSize: 13.5, fontWeight: 600,
  cursor: "pointer", fontFamily: FONT.sans, display: "flex", alignItems: "center", gap: 6,
};

const btnSecundario = {
  padding: "8px 14px", borderRadius: 8, border: `1px solid ${C.border}`,
  background: C.surface, color: C.text2, fontSize: 13, fontWeight: 600,
  cursor: "pointer", fontFamily: FONT.sans, display: "flex", alignItems: "center", gap: 6,
};

/* ------------------------------------------------------------------ */
/* Helpers compartidos                                                  */
/* ------------------------------------------------------------------ */
const ESTADOS = {
  borrador:    { label: "Borrador",    bg: C.yellowBg, bd: C.yellowBd, color: C.yellow   },
  en_revision: { label: "En revisión", bg: "#EEF2FB",  bd: "#C2D0EF",  color: "#2D4FA3"  },
  presentado:  { label: "Presentado",  bg: C.greenBg,  bd: C.greenBd,  color: C.green    },
  sin_periodo: { label: "Sin iniciar", bg: "#F4F2EE",  bd: C.border,   color: C.muted    },
};

function Chip({ estado }) {
  const e = ESTADOS[estado] || ESTADOS.sin_periodo;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      fontSize: 11.5, fontWeight: 700, fontFamily: FONT.sans,
      letterSpacing: "0.05em", textTransform: "uppercase",
      padding: "3px 9px", borderRadius: 999,
      background: e.bg, border: `1px solid ${e.bd}`, color: e.color,
    }}>
      {e.label}
    </span>
  );
}

function Metrica({ label, valor, color = C.text }) {
  return (
    <div style={{ background: C.bg, borderRadius: 10, padding: "14px 18px", flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: C.muted, fontFamily: FONT.sans, marginBottom: 6 }}>{label}</div>
      <div style={{ fontFamily: FONT.serif, fontSize: 26, fontWeight: 500, color }}>{valor}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PantallaLogin                                                       */
/* ------------------------------------------------------------------ */
function PantallaLogin({ onLogin }) {
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error,    setError]    = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email || !password) { setError("Ingresa tu correo y contraseña."); return; }
    setCargando(true); setError(null);
    try {
      const resp = await login(email, password);
      onLogin(resp);
    } catch (err) {
      setError(err.message || "Credenciales incorrectas.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: C.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
      `}</style>

      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 16, padding: "40px 36px", width: "100%", maxWidth: 400, boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: C.accent, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "#FFF", fontSize: 18, fontWeight: 700, fontFamily: FONT.serif }}>R</span>
          </div>
          <div>
            <div style={{ fontFamily: FONT.serif, fontSize: 17, fontWeight: 500, color: C.text }}>Renta Declaración</div>
            <div style={{ fontSize: 11.5, color: C.muted, fontFamily: FONT.sans, marginTop: 1 }}>Formulario 210 · DIAN 2025</div>
          </div>
        </div>

        <h1 style={{ fontFamily: FONT.serif, fontWeight: 500, fontSize: 22, margin: "0 0 6px 0", color: C.text }}>Iniciar sesión</h1>
        <p style={{ fontSize: 13.5, color: C.muted, margin: "0 0 24px 0", fontFamily: FONT.sans }}>Ingresa con tu cuenta de contador o auxiliar.</p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: C.text2, marginBottom: 6, fontFamily: FONT.sans }}>
              Correo electrónico
            </label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="correo@empresa.com" autoComplete="email" style={inputBase}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: C.text2, marginBottom: 6, fontFamily: FONT.sans }}>
              Contraseña
            </label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••" autoComplete="current-password" style={inputBase}
            />
          </div>

          {error && (
            <div style={{ background: C.redBg, border: `1px solid ${C.redBd}`, color: C.red, fontSize: 13, borderRadius: 8, padding: "9px 12px", marginBottom: 16, fontFamily: FONT.sans }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={cargando}
            style={{ ...btnPrimario, width: "100%", justifyContent: "center", fontSize: 14.5, padding: "11px 0", opacity: cargando ? 0.7 : 1 }}
          >
            {cargando ? "Ingresando…" : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PantallaCartera — panel del contador / auxiliar                     */
/* ------------------------------------------------------------------ */
function PantallaCartera({ sesion, onSeleccionar, onCerrarSesion }) {
  const [declarantes,   setDeclarantes]   = useState(null);
  const [periodosPorId, setPeriodosPorId] = useState({});
  const [cargando,      setCargando]      = useState(true);
  const [errorCarga,    setErrorCarga]    = useState(null);
  const [busqueda,      setBusqueda]      = useState("");
  const [filtroEstado,  setFiltroEstado]  = useState("todos");
  const [modalAbierto,  setModalAbierto]  = useState(false);

  const [form,     setForm]     = useState({ nit: "", dv: "", nombre: "", apellido: "", actividad: "" });
  const [creando,  setCreando]  = useState(false);
  const [errModal, setErrModal] = useState(null);

  /* ── Carga de datos ── */
  const cargarTodo = useCallback(async () => {
    setCargando(true); setErrorCarga(null);
    try {
      // Act. 1.3 — listarDeclarantes ahora devuelve { total, skip, limit, items }
      const resp = await listarDeclarantes(sesion.token, { limit: 500 });
      const lista = resp.items ?? resp; // compatibilidad si el backend aún no está actualizado
      setDeclarantes(lista);

      // Periodos 2025 en lotes de 10 en paralelo
      const chunks = [];
      for (let i = 0; i < lista.length; i += 10) chunks.push(lista.slice(i, i + 10));
      const mapa = {};
      for (const chunk of chunks) {
        await Promise.all(chunk.map(async (d) => {
          try {
            const periodos = await listarPeriodos(sesion.token, d.id);
            mapa[d.id] = periodos.find(p => p.anio === 2025) || null;
          } catch (_) { mapa[d.id] = null; }
        }));
      }
      setPeriodosPorId(mapa);
    } catch (err) {
      if (err.code === "UNAUTHORIZED") { onCerrarSesion(); return; }
      setErrorCarga(err.message);
    } finally {
      setCargando(false);
    }
  }, [sesion.token, onCerrarSesion]);

  useEffect(() => { cargarTodo(); }, [cargarTodo]);

  /* ── Métricas ── */
  const metricas = useMemo(() => {
    if (!declarantes) return null;
    return {
      total:      declarantes.length,
      sinInicio:  declarantes.filter(d => !periodosPorId[d.id]).length,
      borrador:   declarantes.filter(d => periodosPorId[d.id]?.estado === "borrador").length,
      enRevision: declarantes.filter(d => periodosPorId[d.id]?.estado === "en_revision").length,
      presentado: declarantes.filter(d => periodosPorId[d.id]?.estado === "presentado").length,
    };
  }, [declarantes, periodosPorId]);

  /* ── Filtrado + búsqueda ── */
  const lista = useMemo(() => {
    if (!declarantes) return [];
    return declarantes.filter(d => {
      const estado = periodosPorId[d.id]?.estado || "sin_periodo";
      if (filtroEstado !== "todos" && estado !== filtroEstado) return false;
      if (!busqueda.trim()) return true;
      const q = busqueda.toLowerCase();
      return (
        d.primer_apellido.toLowerCase().includes(q) ||
        d.primer_nombre.toLowerCase().includes(q)   ||
        d.nit.includes(q)
      );
    });
  }, [declarantes, periodosPorId, filtroEstado, busqueda]);

  /* ── Crear declarante ── */
  function resetForm() { setForm({ nit: "", dv: "", nombre: "", apellido: "", actividad: "" }); setErrModal(null); }

  async function handleCrear(e) {
    e.preventDefault();
    if (!form.nit || !form.apellido || !form.nombre || !form.actividad) {
      setErrModal("Completa todos los campos obligatorios."); return;
    }
    if (!/^\d{6,10}$/.test(form.nit)) {
      setErrModal("El NIT debe tener entre 6 y 10 dígitos, sin puntos ni guiones."); return;
    }
    setCreando(true); setErrModal(null);
    try {
      const nuevo = await crearDeclarante(sesion.token, {
        nit: form.nit, digito_verificacion: form.dv || "0",
        primer_nombre: form.nombre, primer_apellido: form.apellido,
        actividad_economica: form.actividad,
      });
      setModalAbierto(false); resetForm();
      onSeleccionar(nuevo);
    } catch (err) {
      if (err.code === "UNAUTHORIZED") { onCerrarSesion(); return; }
      setErrModal(err.message);
    } finally {
      setCreando(false);
    }
  }

  const ACTIVIDADES = [
    { value: "empleado",      label: "Asalariado / empleado" },
    { value: "independiente", label: "Servicios profesionales independientes" },
    { value: "rentista",      label: "Rentista de capital" },
    { value: "otro",          label: "Otra actividad" },
  ];

  const FILTROS = [
    { key: "todos",       label: "Todos" },
    { key: "sin_periodo", label: "Sin iniciar" },
    { key: "borrador",    label: "Borrador" },
    { key: "en_revision", label: "En revisión" },
    { key: "presentado",  label: "Presentados" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: C.bg }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        button:focus-visible { outline: 2px solid ${C.accent}; outline-offset: 2px; }
      `}</style>

      {/* Header */}
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, padding: "13px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: C.accent, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "#FFF", fontSize: 15, fontWeight: 700, fontFamily: FONT.serif }}>R</span>
          </div>
          <span style={{ fontFamily: FONT.serif, fontSize: 17, fontWeight: 500, color: C.text }}>Renta Declaración</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span style={{ fontSize: 13, color: C.muted, fontFamily: FONT.sans }}>
            {sesion.nombre} · <span style={{ textTransform: "capitalize" }}>{sesion.rol}</span>
          </span>
          <button onClick={onCerrarSesion} style={{ ...btnSecundario, fontSize: 13, padding: "7px 14px" }}>
            Cerrar sesión
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 1040, margin: "0 auto", padding: "32px 20px 60px" }}>

        {/* Título + botón nuevo */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
          <div>
            <h1 style={{ fontFamily: FONT.serif, fontWeight: 500, fontSize: 30, margin: "0 0 4px 0", color: C.text }}>Cartera de declarantes</h1>
            <p style={{ fontSize: 13.5, color: C.muted, margin: 0, fontFamily: FONT.sans }}>Año gravable 2025 · gestión de declaraciones de renta.</p>
          </div>
          <button onClick={() => { resetForm(); setModalAbierto(true); }} style={btnPrimario}>
            + Nuevo declarante
          </button>
        </div>

        {/* Métricas */}
        {metricas && (
          <div style={{ display: "flex", gap: 12, marginBottom: 28, flexWrap: "wrap" }}>
            <Metrica label="Total cartera"  valor={metricas.total}      color={C.text}     />
            <Metrica label="Sin iniciar"    valor={metricas.sinInicio}  color={C.muted}    />
            <Metrica label="En borrador"    valor={metricas.borrador}   color={C.yellow}   />
            <Metrica label="En revisión"    valor={metricas.enRevision} color="#2D4FA3"    />
            <Metrica label="Presentadas"    valor={metricas.presentado} color={C.green}    />
          </div>
        )}

        {/* Buscador + filtros */}
        <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <input
            value={busqueda} onChange={e => setBusqueda(e.target.value)}
            placeholder="🔍  Buscar por nombre o NIT…"
            style={{ ...inputBase, width: "auto", flex: "1 1 240px", fontSize: 13.5, padding: "8px 12px" }}
          />
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {FILTROS.map(f => (
              <button key={f.key} onClick={() => setFiltroEstado(f.key)} style={{
                padding: "7px 13px", borderRadius: 8, fontSize: 13, fontWeight: 600,
                fontFamily: FONT.sans, cursor: "pointer",
                border: `1px solid ${filtroEstado === f.key ? C.accent : C.border}`,
                background: filtroEstado === f.key ? C.accentBg : C.surface,
                color: filtroEstado === f.key ? C.accent : C.text2,
              }}>
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Estado de carga */}
        {cargando && (
          <div style={{ textAlign: "center", color: C.muted, padding: 56, fontFamily: FONT.sans, fontSize: 14 }}>
            Cargando cartera…
          </div>
        )}
        {errorCarga && (
          <div style={{ background: C.redBg, border: `1px solid ${C.redBd}`, color: C.red, fontSize: 13.5, borderRadius: 10, padding: "14px 18px", fontFamily: FONT.sans }}>
            {errorCarga} —{" "}
            <button onClick={cargarTodo} style={{ background: "none", border: "none", color: C.accent, cursor: "pointer", fontWeight: 600, fontSize: 13.5 }}>
              Reintentar
            </button>
          </div>
        )}

        {/* Lista vacía — sin declarantes */}
        {!cargando && !errorCarga && declarantes?.length === 0 && (
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "56px 32px", textAlign: "center" }}>
            <div style={{ fontFamily: FONT.serif, fontSize: 20, color: C.text2, marginBottom: 8 }}>
              Aún no hay declarantes registrados
            </div>
            <p style={{ fontSize: 13.5, color: C.muted, fontFamily: FONT.sans, marginBottom: 20 }}>
              Crea el primero para comenzar a liquidar declaraciones.
            </p>
            <button onClick={() => setModalAbierto(true)} style={{ ...btnPrimario, margin: "0 auto" }}>
              + Crear primer declarante
            </button>
          </div>
        )}

        {/* Sin resultados de búsqueda/filtro */}
        {!cargando && !errorCarga && declarantes?.length > 0 && lista.length === 0 && (
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "32px", textAlign: "center", color: C.muted, fontFamily: FONT.sans, fontSize: 14 }}>
            Ningún declarante coincide con los filtros aplicados.{" "}
            <button
              onClick={() => { setBusqueda(""); setFiltroEstado("todos"); }}
              style={{ background: "none", border: "none", color: C.accent, cursor: "pointer", fontWeight: 600, fontSize: 14 }}
            >
              Limpiar filtros
            </button>
          </div>
        )}

        {/* Tabla de cartera */}
        {!cargando && lista.length > 0 && (
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden" }}>
            {/* Cabecera */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1.2fr 1fr 1fr 44px", padding: "9px 20px", background: C.bg, borderBottom: `1px solid ${C.border}` }}>
              {["Declarante", "NIT", "Actividad", "Estado 2025", ""].map((h, i) => (
                <div key={i} style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: C.muted, fontFamily: FONT.sans }}>
                  {h}
                </div>
              ))}
            </div>

            {/* Filas */}
            {lista.map((d, i) => {
              const estado = periodosPorId[d.id]?.estado || "sin_periodo";
              return (
                <button
                  key={d.id} onClick={() => onSeleccionar(d)}
                  onMouseEnter={e => e.currentTarget.style.background = "#FBF9F4"}
                  onMouseLeave={e => e.currentTarget.style.background = "none"}
                  style={{
                    display: "grid", gridTemplateColumns: "2fr 1.2fr 1fr 1fr 44px",
                    width: "100%", textAlign: "left", background: "none", border: "none",
                    borderTop: i === 0 ? "none" : `1px solid ${C.border2}`,
                    padding: "14px 20px", cursor: "pointer", alignItems: "center",
                  }}
                >
                  <div style={{ fontFamily: FONT.sans, fontSize: 14.5, fontWeight: 600, color: C.text }}>
                    {d.primer_apellido}, {d.primer_nombre}
                  </div>
                  <div style={{ fontSize: 13.5, color: C.text2, fontFamily: FONT.sans }}>
                    {d.nit}<span style={{ color: C.muted2 }}>-{d.digito_verificacion}</span>
                  </div>
                  <div style={{ fontSize: 13, color: C.muted, fontFamily: FONT.sans, textTransform: "capitalize" }}>
                    {d.actividad_economica}
                  </div>
                  <div><Chip estado={estado} /></div>
                  <div style={{ color: C.muted2, fontSize: 18, textAlign: "right" }}>›</div>
                </button>
              );
            })}

            {/* Pie */}
            <div style={{ padding: "10px 20px", borderTop: `1px solid ${C.border}`, background: C.bg, fontSize: 12, color: C.muted, fontFamily: FONT.sans, display: "flex", justifyContent: "space-between" }}>
              <span>Mostrando {lista.length} de {declarantes?.length || 0} declarantes</span>
              <button onClick={cargarTodo} style={{ background: "none", border: "none", color: C.accent, cursor: "pointer", fontSize: 12, fontWeight: 600, fontFamily: FONT.sans }}>
                ↻ Actualizar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal — nuevo declarante */}
      {modalAbierto && (
        <div
          onClick={e => { if (e.target === e.currentTarget) { setModalAbierto(false); resetForm(); } }}
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}
        >
          <div style={{ background: C.surface, borderRadius: 14, padding: "32px 32px 28px", width: "100%", maxWidth: 480, boxShadow: "0 8px 40px rgba(0,0,0,0.18)" }}>
            <h2 style={{ fontFamily: FONT.serif, fontWeight: 500, fontSize: 20, margin: "0 0 6px 0", color: C.text }}>Nuevo declarante</h2>
            <p style={{ fontSize: 13, color: C.muted, margin: "0 0 22px 0", fontFamily: FONT.sans }}>Los datos deben coincidir con el RUT vigente en la DIAN.</p>

            <form onSubmit={handleCrear}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 80px", gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: C.text2, marginBottom: 5, fontFamily: FONT.sans }}>NIT <span style={{ color: C.accent }}>*</span></label>
                  <input value={form.nit} onChange={e => setForm(f => ({ ...f, nit: e.target.value }))} placeholder="79512345" style={inputBase} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: C.text2, marginBottom: 5, fontFamily: FONT.sans }}>DV</label>
                  <input value={form.dv} onChange={e => setForm(f => ({ ...f, dv: e.target.value }))} placeholder="4" maxLength={1} style={inputBase} />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: C.text2, marginBottom: 5, fontFamily: FONT.sans }}>Primer apellido <span style={{ color: C.accent }}>*</span></label>
                  <input value={form.apellido} onChange={e => setForm(f => ({ ...f, apellido: e.target.value }))} style={inputBase} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: C.text2, marginBottom: 5, fontFamily: FONT.sans }}>Primer nombre <span style={{ color: C.accent }}>*</span></label>
                  <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} style={inputBase} />
                </div>
              </div>

              <div style={{ marginBottom: 20 }}>
                <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: C.text2, marginBottom: 5, fontFamily: FONT.sans }}>Actividad económica <span style={{ color: C.accent }}>*</span></label>
                <select value={form.actividad} onChange={e => setForm(f => ({ ...f, actividad: e.target.value }))} style={{ ...inputBase, cursor: "pointer" }}>
                  <option value="">Seleccione…</option>
                  {ACTIVIDADES.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                </select>
              </div>

              {errModal && (
                <div style={{ background: C.redBg, border: `1px solid ${C.redBd}`, color: C.red, fontSize: 12.5, borderRadius: 8, padding: "8px 12px", marginBottom: 16, fontFamily: FONT.sans }}>
                  {errModal}
                </div>
              )}

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button type="button" onClick={() => { setModalAbierto(false); resetForm(); }} style={btnSecundario}>
                  Cancelar
                </button>
                <button type="submit" disabled={creando} style={{ ...btnPrimario, opacity: creando ? 0.7 : 1 }}>
                  {creando ? "Creando…" : "Crear y abrir declaración"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* App — router de estado                                              */
/* Enrutamiento por rol:                                               */
/*   admin      → PanelAdmin                                           */
/*   contador   → PantallaCartera → Wizard                            */
/*   auxiliar   → PantallaCartera → Wizard                            */
/* ------------------------------------------------------------------ */
function App() {
  const [sesion,           setSesion]           = useState(null);
  const [pantalla,         setPantalla]         = useState("login");
  const [declaranteActivo, setDeclaranteActivo] = useState(null);

  function handleLogin(respuesta) {
    const s = { token: respuesta.access_token, rol: respuesta.rol, nombre: respuesta.nombre };
    setSesion(s);
    setPantalla(respuesta.rol === "admin" ? "admin" : "cartera");
  }

  function handleCerrarSesion() {
    setSesion(null);
    setDeclaranteActivo(null);
    setPantalla("login");
  }

  function handleSeleccionarDeclarante(declarante) {
    setDeclaranteActivo(declarante);
    setPantalla("wizard");
  }

  function handleVolverAListado() {
    // Al volver del wizard siempre se va a cartera, independiente del rol.
    // El admin llega a la cartera desde el botón "Ir a cartera" del PanelAdmin,
    // y al terminar un wizard debe volver a la cartera (no al panel admin).
    // Act. 4.6 — parche rol admin-contador. Solución estructural en Act. 2F.2.
    setDeclaranteActivo(null);
    setPantalla("cartera");
  }

  function handleIrACartera() {
    // Act. 4.6 — permite al admin navegar a la cartera sin cambiar su rol.
    setPantalla("cartera");
  }

  if (pantalla === "login")   return <PantallaLogin onLogin={handleLogin} />;
  if (pantalla === "admin")   return <PanelAdmin sesion={sesion} onCerrarSesion={handleCerrarSesion} onIrACartera={handleIrACartera} />;
  if (pantalla === "cartera") return <PantallaCartera sesion={sesion} onSeleccionar={handleSeleccionarDeclarante} onCerrarSesion={handleCerrarSesion} />;
  if (pantalla === "wizard")  return <DeclaracionRentaWizard sesion={sesion} declarante={declaranteActivo} onVolver={handleVolverAListado} onSesionExpirada={handleCerrarSesion} />;
  return null;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);