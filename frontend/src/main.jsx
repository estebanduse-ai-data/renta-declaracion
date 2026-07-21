import { useState, useCallback } from "react";
import ReactDOM from "react-dom/client";
import { login, listarDeclarantes, crearDeclarante } from "./api.js";
import DeclaracionRentaWizard from "./wizard/DeclaracionRentaWizard.jsx";

/* ------------------------------------------------------------------ */
/* Estilos base compartidos                                            */
/* ------------------------------------------------------------------ */
const inputBase = {
  width: "100%",
  fontFamily: "'Inter', sans-serif",
  fontSize: 14.5,
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid #DAD3C0",
  background: "#FFFFFF",
  color: "#23201A",
  outline: "none",
  boxSizing: "border-box",
};

const btnPrimario = {
  width: "100%",
  padding: "11px 0",
  borderRadius: 8,
  border: "none",
  background: "#C96442",
  color: "#FFF",
  fontSize: 14.5,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "'Inter', sans-serif",
};

const btnSecundario = {
  padding: "9px 16px",
  borderRadius: 8,
  border: "1px solid #DAD3C0",
  background: "#FFF",
  color: "#3A342A",
  fontSize: 13.5,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "'Inter', sans-serif",
  display: "flex",
  alignItems: "center",
  gap: 6,
};

/* ------------------------------------------------------------------ */
/* PantallaLogin                                                       */
/* ------------------------------------------------------------------ */
function PantallaLogin({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email || !password) { setError("Ingresa tu correo y contraseña."); return; }
    setCargando(true);
    setError(null);
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
    <div style={{
      minHeight: "100vh", background: "#F7F3EA", display: "flex",
      alignItems: "center", justifyContent: "center",
    }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap'); * { box-sizing: border-box; }`}</style>
      <div style={{
        background: "#FFF", border: "1px solid #EAE4D4", borderRadius: 16,
        padding: "40px 36px", width: "100%", maxWidth: 400,
        boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10, background: "#C96442",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ color: "#FFF", fontSize: 18, fontWeight: 700, fontFamily: "'Fraunces', serif" }}>R</span>
          </div>
          <div>
            <div style={{ fontFamily: "'Fraunces', serif", fontSize: 17, fontWeight: 500, color: "#1E1B15" }}>
              Renta Declaración
            </div>
            <div style={{ fontSize: 11.5, color: "#8A7F68", fontFamily: "'Inter', sans-serif", marginTop: 1 }}>
              Formulario 210 · DIAN 2025
            </div>
          </div>
        </div>

        <h1 style={{ fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 22, margin: "0 0 6px 0", color: "#1E1B15" }}>
          Iniciar sesión
        </h1>
        <p style={{ fontSize: 13.5, color: "#8A7F68", margin: "0 0 24px 0", fontFamily: "'Inter', sans-serif" }}>
          Ingresa con tu cuenta de contador o auxiliar.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#3A342A", marginBottom: 6, fontFamily: "'Inter', sans-serif" }}>
              Correo electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="correo@empresa.com"
              autoComplete="email"
              style={inputBase}
            />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#3A342A", marginBottom: 6, fontFamily: "'Inter', sans-serif" }}>
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              style={inputBase}
            />
          </div>

          {error && (
            <div style={{
              background: "#FBEAE8", border: "1px solid #F0C7C2", color: "#8C231C",
              fontSize: 13, borderRadius: 8, padding: "9px 12px", marginBottom: 16,
              fontFamily: "'Inter', sans-serif",
            }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={cargando} style={{ ...btnPrimario, opacity: cargando ? 0.7 : 1 }}>
            {cargando ? "Ingresando…" : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PantallaDeclarantes — listado + crear nuevo                         */
/* ------------------------------------------------------------------ */
function PantallaDeclarantes({ sesion, onSeleccionar, onCerrarSesion }) {
  const [declarantes, setDeclarantes] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(null);

  // Modal nuevo declarante
  const [modalAbierto, setModalAbierto] = useState(false);
  const [nuevoNit, setNuevoNit] = useState("");
  const [nuevoDv, setNuevoDv] = useState("");
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevoApellido, setNuevoApellido] = useState("");
  const [nuevaActividad, setNuevaActividad] = useState("");
  const [creando, setCreando] = useState(false);
  const [errorModal, setErrorModal] = useState(null);

  const cargarDeclarantes = useCallback(async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      const lista = await listarDeclarantes(sesion.token);
      setDeclarantes(lista);
    } catch (err) {
      if (err.code === "UNAUTHORIZED") { onCerrarSesion(); return; }
      setErrorCarga(err.message);
    } finally {
      setCargando(false);
    }
  }, [sesion.token, onCerrarSesion]);

  // Cargar al montar
  useState(() => { cargarDeclarantes(); }, []);
  // Workaround: useEffect no está importado aquí, usamos el patrón lazy init
  // En producción usar useEffect; por simplicidad llamamos en el primer render
  if (declarantes === null && !cargando && !errorCarga) cargarDeclarantes();

  async function handleCrear(e) {
    e.preventDefault();
    if (!nuevoNit || !nuevoApellido || !nuevoNombre || !nuevaActividad) {
      setErrorModal("Completa todos los campos obligatorios."); return;
    }
    if (!/^\d{6,10}$/.test(nuevoNit)) {
      setErrorModal("El NIT debe tener entre 6 y 10 dígitos, sin puntos ni guiones."); return;
    }
    setCreando(true);
    setErrorModal(null);
    try {
      const nuevo = await crearDeclarante(sesion.token, {
        nit: nuevoNit,
        digito_verificacion: nuevoDv || "0",
        primer_nombre: nuevoNombre,
        primer_apellido: nuevoApellido,
        actividad_economica: nuevaActividad,
      });
      setModalAbierto(false);
      resetModal();
      // Abrir el wizard con el declarante recién creado (sin periodo aún)
      onSeleccionar(nuevo);
    } catch (err) {
      if (err.code === "UNAUTHORIZED") { onCerrarSesion(); return; }
      setErrorModal(err.message);
    } finally {
      setCreando(false);
    }
  }

  function resetModal() {
    setNuevoNit(""); setNuevoDv(""); setNuevoNombre("");
    setNuevoApellido(""); setNuevaActividad(""); setErrorModal(null);
  }

  const ACTIVIDADES = [
    { value: "empleado", label: "Asalariado / empleado" },
    { value: "independiente", label: "Servicios profesionales independientes" },
    { value: "rentista", label: "Rentista de capital" },
    { value: "otro", label: "Otra actividad" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#F7F3EA" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap'); * { box-sizing: border-box; }`}</style>

      {/* Header */}
      <div style={{
        background: "#FFF", borderBottom: "1px solid #EAE4D4",
        padding: "14px 32px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8, background: "#C96442",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ color: "#FFF", fontSize: 15, fontWeight: 700, fontFamily: "'Fraunces', serif" }}>R</span>
          </div>
          <span style={{ fontFamily: "'Fraunces', serif", fontSize: 17, fontWeight: 500, color: "#1E1B15" }}>
            Renta Declaración
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 13, color: "#6B6355", fontFamily: "'Inter', sans-serif" }}>
            {sesion.nombre} · <span style={{ textTransform: "capitalize" }}>{sesion.rol}</span>
          </span>
          <button onClick={onCerrarSesion} style={{ ...btnSecundario, fontSize: 13, padding: "7px 14px" }}>
            Cerrar sesión
          </button>
        </div>
      </div>

      {/* Contenido */}
      <div style={{ maxWidth: 860, margin: "0 auto", padding: "36px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 28 }}>
          <div>
            <h1 style={{ fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 28, margin: "0 0 4px 0", color: "#1E1B15" }}>
              Declarantes
            </h1>
            <p style={{ fontSize: 13.5, color: "#8A7F68", margin: 0, fontFamily: "'Inter', sans-serif" }}>
              Selecciona un declarante para abrir su asistente de declaración de renta 2025.
            </p>
          </div>
          <button
            onClick={() => { resetModal(); setModalAbierto(true); }}
            style={{ ...btnPrimario, width: "auto", padding: "9px 18px" }}
          >
            + Nuevo declarante
          </button>
        </div>

        {/* Estado de carga / error */}
        {cargando && (
          <div style={{ textAlign: "center", color: "#8A7F68", padding: 48, fontFamily: "'Inter', sans-serif", fontSize: 14 }}>
            Cargando declarantes…
          </div>
        )}
        {errorCarga && (
          <div style={{
            background: "#FBEAE8", border: "1px solid #F0C7C2", color: "#8C231C",
            fontSize: 13.5, borderRadius: 10, padding: "14px 18px", fontFamily: "'Inter', sans-serif",
          }}>
            {errorCarga} —{" "}
            <button onClick={cargarDeclarantes} style={{ background: "none", border: "none", color: "#C96442", cursor: "pointer", fontWeight: 600, fontSize: 13.5 }}>
              Reintentar
            </button>
          </div>
        )}

        {/* Lista */}
        {declarantes && declarantes.length === 0 && (
          <div style={{
            background: "#FFF", border: "1px solid #EAE4D4", borderRadius: 12,
            padding: "48px 32px", textAlign: "center",
          }}>
            <div style={{ fontFamily: "'Fraunces', serif", fontSize: 18, color: "#3A342A", marginBottom: 8 }}>
              Aún no hay declarantes registrados
            </div>
            <p style={{ fontSize: 13.5, color: "#8A7F68", fontFamily: "'Inter', sans-serif", marginBottom: 20 }}>
              Crea el primero para comenzar a liquidar declaraciones de renta.
            </p>
            <button onClick={() => setModalAbierto(true)} style={{ ...btnPrimario, width: "auto", padding: "10px 24px" }}>
              + Crear primer declarante
            </button>
          </div>
        )}

        {declarantes && declarantes.length > 0 && (
          <div style={{ background: "#FFF", border: "1px solid #EAE4D4", borderRadius: 12, overflow: "hidden" }}>
            {declarantes.map((d, i) => (
              <button
                key={d.id}
                onClick={() => onSeleccionar(d)}
                style={{
                  width: "100%", textAlign: "left", background: "none", border: "none",
                  borderTop: i === 0 ? "none" : "1px solid #F0ECE1",
                  padding: "16px 20px", cursor: "pointer", display: "flex",
                  alignItems: "center", justifyContent: "space-between",
                  transition: "background 0.12s",
                }}
                onMouseEnter={e => e.currentTarget.style.background = "#FBF9F4"}
                onMouseLeave={e => e.currentTarget.style.background = "none"}
              >
                <div>
                  <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 15, fontWeight: 600, color: "#1E1B15" }}>
                    {d.primer_apellido}, {d.primer_nombre}
                  </div>
                  <div style={{ fontSize: 12.5, color: "#8A7F68", marginTop: 3, fontFamily: "'Inter', sans-serif" }}>
                    NIT {d.nit}-{d.digito_verificacion} · Actividad {d.actividad_economica}
                  </div>
                </div>
                <span style={{ fontSize: 18, color: "#C9C2AE" }}>›</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Modal nuevo declarante */}
      {modalAbierto && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
        }}
          onClick={e => { if (e.target === e.currentTarget) { setModalAbierto(false); resetModal(); } }}
        >
          <div style={{
            background: "#FFF", borderRadius: 14, padding: "32px 32px 28px",
            width: "100%", maxWidth: 480, boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
          }}>
            <h2 style={{ fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 20, margin: "0 0 6px 0", color: "#1E1B15" }}>
              Nuevo declarante
            </h2>
            <p style={{ fontSize: 13, color: "#8A7F68", margin: "0 0 22px 0", fontFamily: "'Inter', sans-serif" }}>
              Los datos deben coincidir con el RUT vigente en la DIAN.
            </p>

            <form onSubmit={handleCrear}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 80px", gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: "#3A342A", marginBottom: 5, fontFamily: "'Inter', sans-serif" }}>
                    NIT <span style={{ color: "#C96442" }}>*</span>
                  </label>
                  <input value={nuevoNit} onChange={e => setNuevoNit(e.target.value)} placeholder="79512345" style={inputBase} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: "#3A342A", marginBottom: 5, fontFamily: "'Inter', sans-serif" }}>
                    DV
                  </label>
                  <input value={nuevoDv} onChange={e => setNuevoDv(e.target.value)} placeholder="4" maxLength={1} style={inputBase} />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: "#3A342A", marginBottom: 5, fontFamily: "'Inter', sans-serif" }}>
                    Primer apellido <span style={{ color: "#C96442" }}>*</span>
                  </label>
                  <input value={nuevoApellido} onChange={e => setNuevoApellido(e.target.value)} style={inputBase} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: "#3A342A", marginBottom: 5, fontFamily: "'Inter', sans-serif" }}>
                    Primer nombre <span style={{ color: "#C96442" }}>*</span>
                  </label>
                  <input value={nuevoNombre} onChange={e => setNuevoNombre(e.target.value)} style={inputBase} />
                </div>
              </div>

              <div style={{ marginBottom: 20 }}>
                <label style={{ display: "block", fontSize: 12.5, fontWeight: 600, color: "#3A342A", marginBottom: 5, fontFamily: "'Inter', sans-serif" }}>
                  Actividad económica <span style={{ color: "#C96442" }}>*</span>
                </label>
                <select value={nuevaActividad} onChange={e => setNuevaActividad(e.target.value)} style={{ ...inputBase, cursor: "pointer" }}>
                  <option value="">Seleccione…</option>
                  {ACTIVIDADES.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                </select>
              </div>

              {errorModal && (
                <div style={{
                  background: "#FBEAE8", border: "1px solid #F0C7C2", color: "#8C231C",
                  fontSize: 12.5, borderRadius: 8, padding: "8px 12px", marginBottom: 16,
                  fontFamily: "'Inter', sans-serif",
                }}>
                  {errorModal}
                </div>
              )}

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button type="button" onClick={() => { setModalAbierto(false); resetModal(); }} style={btnSecundario}>
                  Cancelar
                </button>
                <button type="submit" disabled={creando} style={{ ...btnPrimario, width: "auto", padding: "9px 22px", opacity: creando ? 0.7 : 1 }}>
                  {creando ? "Creando…" : "Crear y abrir wizard"}
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
/* ------------------------------------------------------------------ */
function App() {
  // sesion: null | { token, rol, nombre }
  const [sesion, setSesion] = useState(null);
  // pantalla: "login" | "declarantes" | "wizard"
  const [pantalla, setPantalla] = useState("login");
  // declarante seleccionado para abrir el wizard
  const [declaranteActivo, setDeclaranteActivo] = useState(null);

  function handleLogin(respuesta) {
    setSesion({ token: respuesta.access_token, rol: respuesta.rol, nombre: respuesta.nombre });
    setPantalla("declarantes");
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
    setDeclaranteActivo(null);
    setPantalla("declarantes");
  }

  // Redirigir a login si el token expiró (capturado en api.js)
  function handleSesionExpirada() {
    handleCerrarSesion();
  }

  if (pantalla === "login") {
    return <PantallaLogin onLogin={handleLogin} />;
  }

  if (pantalla === "declarantes") {
    return (
      <PantallaDeclarantes
        sesion={sesion}
        onSeleccionar={handleSeleccionarDeclarante}
        onCerrarSesion={handleCerrarSesion}
      />
    );
  }

  if (pantalla === "wizard") {
    return (
      <DeclaracionRentaWizard
        sesion={sesion}
        declarante={declaranteActivo}
        onVolver={handleVolverAListado}
        onSesionExpirada={handleSesionExpirada}
      />
    );
  }

  return null;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
