import { useState, useMemo, useRef, useEffect } from "react";
import {
  Info,
  ChevronRight,
  ChevronLeft,
  Check,
  AlertCircle,
  User,
  Wallet,
  Layers,
  Calculator,
  Receipt,
  FileCheck,
  HelpCircle,
  X,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* Parámetros tributarios — año gravable 2025 (editables en un solo lugar) */
/* ------------------------------------------------------------------ */
const UVT_2025 = 49799; // valor referencial UVT 2025, ajustar cada año

// Tabla progresiva Art. 241 E.T. — rangos en UVT sobre renta líquida gravable
const TABLA_TARIFA = [
  { desde: 0, hasta: 1090, tarifa: 0, base: 0 },
  { desde: 1090, hasta: 1700, tarifa: 0.19, base: 0 },
  { desde: 1700, hasta: 4100, tarifa: 0.28, base: 116 },
  { desde: 4100, hasta: 8670, tarifa: 0.33, base: 788 },
  { desde: 8670, hasta: 18970, tarifa: 0.35, base: 2296 },
  { desde: 18970, hasta: 31000, tarifa: 0.37, base: 6901 },
  { desde: 31000, hasta: Infinity, tarifa: 0.39, base: 11352 },
];

const LIMITE_RENTA_EXENTA_DEDUCCIONES = 0.4; // 40% cédula general, art. 336 E.T.
const TOPE_RENTA_EXENTA_DEDUCCIONES_UVT = 1340;

function formatCOP(valor) {
  if (valor === null || valor === undefined || isNaN(valor)) return "$ 0";
  const signo = valor < 0 ? "-" : "";
  return `${signo}$ ${Math.abs(Math.round(valor)).toLocaleString("es-CO")}`;
}

function aUVT(pesos) {
  return pesos / UVT_2025;
}
function aPesos(uvt) {
  return uvt * UVT_2025;
}

function calcularImpuestoUVT(baseUVT) {
  if (baseUVT <= 0) return 0;
  const tramo = TABLA_TARIFA.find((t) => baseUVT > t.desde && baseUVT <= t.hasta) ||
    TABLA_TARIFA[TABLA_TARIFA.length - 1];
  return tramo.base + (baseUVT - tramo.desde) * tramo.tarifa;
}

/* ------------------------------------------------------------------ */
/* Definición de pasos                                                 */
/* ------------------------------------------------------------------ */
const PASOS = [
  { id: "perfil", numero: "0", titulo: "Perfil", icon: Layers },
  { id: "datos", numero: "1", titulo: "Datos generales", icon: User },
  { id: "patrimonio", numero: "2", titulo: "Patrimonio", icon: Wallet },
  { id: "ingresos", numero: "3", titulo: "Rentas cedulares", icon: Layers },
  { id: "presuntiva", numero: "6", titulo: "Renta presuntiva", icon: Calculator },
  { id: "liquidacion", numero: "7", titulo: "Liquidación privada", icon: Receipt },
  { id: "resumen", numero: "8", titulo: "Resumen", icon: FileCheck },
];

/* ------------------------------------------------------------------ */
/* Componentes de ayuda: tooltip / info                                */
/* ------------------------------------------------------------------ */
function AyudaInfo({ children }) {
  const [abierto, setAbierto] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    function fuera(e) {
      if (ref.current && !ref.current.contains(e.target)) setAbierto(false);
    }
    document.addEventListener("mousedown", fuera);
    return () => document.removeEventListener("mousedown", fuera);
  }, []);
  return (
    <span style={{ position: "relative", display: "inline-flex" }} ref={ref}>
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        aria-label="Ver ayuda"
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: 18,
          height: 18,
          borderRadius: 999,
          border: "1px solid #C9BFA8",
          background: abierto ? "#C96442" : "transparent",
          color: abierto ? "#FFFFFF" : "#8A7F68",
          cursor: "pointer",
          flexShrink: 0,
        }}
      >
        <Info size={11} strokeWidth={2.5} />
      </button>
      {abierto && (
        <div
          style={{
            position: "absolute",
            zIndex: 30,
            top: 24,
            left: 0,
            width: 260,
            background: "#2A241C",
            color: "#F2EEE3",
            fontSize: 12.5,
            lineHeight: 1.5,
            padding: "10px 12px",
            borderRadius: 8,
            boxShadow: "0 8px 24px rgba(0,0,0,0.25)",
            fontFamily: "'Inter', sans-serif",
          }}
        >
          {children}
        </div>
      )}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Campo de formulario reutilizable                                    */
/* ------------------------------------------------------------------ */
function Campo({ label, ayuda, error, children, required, casilla }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <label
          style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: 13,
            fontWeight: 600,
            color: "#3A342A",
            letterSpacing: "0.01em",
          }}
        >
          {label} {required && <span style={{ color: "#C96442" }}>*</span>}
        </label>
        {casilla && (
          <span
            style={{
              fontSize: 10.5,
              fontFamily: "'Inter', sans-serif",
              color: "#8A7F68",
              border: "1px solid #E4DFD1",
              borderRadius: 5,
              padding: "1px 6px",
            }}
          >
            Casilla {casilla}
          </span>
        )}
        {ayuda && <AyudaInfo>{ayuda}</AyudaInfo>}
      </div>
      {children}
      {error && (
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 5,
            marginTop: 6,
            color: "#B3261E",
            fontFamily: "'Inter', sans-serif",
            fontSize: 12.5,
          }}
        >
          <AlertCircle size={13} style={{ marginTop: 1, flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

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

function inputStyle(hasError, focused) {
  return {
    ...inputBase,
    borderColor: hasError ? "#B3261E" : focused ? "#C96442" : "#DAD3C0",
    boxShadow: focused
      ? `0 0 0 3px ${hasError ? "rgba(179,38,30,0.12)" : "rgba(201,100,66,0.14)"}`
      : "none",
  };
}

function TextInput({ value, onChange, hasError, placeholder, prefix, ...props }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ position: "relative" }}>
      {prefix && (
        <span
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            transform: "translateY(-50%)",
            fontSize: 14.5,
            color: "#8A7F68",
            fontFamily: "'Inter', sans-serif",
          }}
        >
          {prefix}
        </span>
      )}
      <input
        value={value}
        onChange={onChange}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={placeholder}
        style={{
          ...inputStyle(hasError, focused),
          paddingLeft: prefix ? 26 : 12,
        }}
        {...props}
      />
    </div>
  );
}

function Select({ value, onChange, options, hasError }) {
  const [focused, setFocused] = useState(false);
  return (
    <select
      value={value}
      onChange={onChange}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{ ...inputStyle(hasError, focused), cursor: "pointer" }}
    >
      <option value="">Seleccione…</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

/* ------------------------------------------------------------------ */
/* Tarjeta de resumen numérico                                         */
/* ------------------------------------------------------------------ */
function Metrica({ label, valor, tono = "neutral", grande }) {
  const colores = {
    neutral: "#23201A",
    positivo: "#4B7B5D",
    negativo: "#B3261E",
    acento: "#C96442",
  };
  return (
    <div>
      <div
        style={{
          fontFamily: "'Inter', sans-serif",
          fontSize: 11.5,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          color: "#8A7F68",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "'Fraunces', serif",
          fontSize: grande ? 30 : 20,
          fontWeight: 500,
          color: colores[tono],
        }}
      >
        {formatCOP(valor)}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* App principal                                                       */
/* ------------------------------------------------------------------ */
export default function DeclaracionRentaWizard() {
  const [pasoActivo, setPasoActivo] = useState(0);
  const [errores, setErrores] = useState({});
  const [tocado, setTocado] = useState({});

  const [perfil, setPerfil] = useState({
    salarios: true,
    honorarios: false,
    capital: false,
    pensiones: false,
    ganancias: false,
  });

  const [datos, setDatos] = useState({
    nit: "",
    dv: "",
    primerApellido: "",
    primerNombre: "",
    actividadEconomica: "",
    aniosDeclarando: "",
    impuestoNetoAnterior: "",
    dependientes: "0",
  });

  const [patrimonio, setPatrimonio] = useState({
    activosBrutoAnterior: "",
    pasivoAnterior: "",
    activosBruto: "",
    pasivos: "",
  });

  const [ingresos, setIngresos] = useState({
    salarios: "",
    retencionSalarios: "",
    honorarios: "",
    retencionHonorarios: "",
    capital: "",
    retencionCapital: "",
    pensiones: "",
    retencionPensiones: "",
    ganancias: "",
    retencionGanancias: "",
    aportesVoluntarios: "",
    saludPrepagada: "",
  });

  const pasosVisibles = useMemo(() => {
    return PASOS.filter((p) => {
      if (p.id === "ingresos") return true;
      return true;
    });
  }, [perfil]);

  /* -------------------- Cálculos derivados -------------------- */

  const patrimonioLiquidoAnterior = useMemo(() => {
    const a = parseFloat(patrimonio.activosBrutoAnterior) || 0;
    const p = parseFloat(patrimonio.pasivoAnterior) || 0;
    return a - p;
  }, [patrimonio]);

  const patrimonioLiquido = useMemo(() => {
    const a = parseFloat(patrimonio.activosBruto) || 0;
    const p = parseFloat(patrimonio.pasivos) || 0;
    return a - p;
  }, [patrimonio]);

  const totalIngresosBrutos = useMemo(() => {
    const campos = [
      perfil.salarios && ingresos.salarios,
      perfil.honorarios && ingresos.honorarios,
      perfil.capital && ingresos.capital,
      perfil.pensiones && ingresos.pensiones,
      perfil.ganancias && ingresos.ganancias,
    ];
    return campos.reduce((acc, v) => acc + (parseFloat(v) || 0), 0);
  }, [ingresos, perfil]);

  const totalRetenciones = useMemo(() => {
    const campos = [
      perfil.salarios && ingresos.retencionSalarios,
      perfil.honorarios && ingresos.retencionHonorarios,
      perfil.capital && ingresos.retencionCapital,
      perfil.pensiones && ingresos.retencionPensiones,
      perfil.ganancias && ingresos.retencionGanancias,
    ];
    return campos.reduce((acc, v) => acc + (parseFloat(v) || 0), 0);
  }, [ingresos, perfil]);

  const deduccionesImputables = useMemo(() => {
    const aportes = parseFloat(ingresos.aportesVoluntarios) || 0;
    const salud = parseFloat(ingresos.saludPrepagada) || 0;
    return aportes + salud;
  }, [ingresos]);

  const rentaExentaLaboral = useMemo(() => {
    // 25% de renta exenta sobre salarios, limitada a 790 UVT/año (simplificado)
    const base = (parseFloat(ingresos.salarios) || 0) * 0.25;
    const tope = aPesos(790);
    return Math.min(base, tope);
  }, [ingresos]);

  const baseGravableAntesLimite = useMemo(() => {
    const bruto = totalIngresosBrutos;
    const menosDeducciones = bruto - deduccionesImputables - rentaExentaLaboral;
    return Math.max(menosDeducciones, 0);
  }, [totalIngresosBrutos, deduccionesImputables, rentaExentaLaboral]);

  const limiteExenciones40 = useMemo(() => {
    const topeUVT = aPesos(TOPE_RENTA_EXENTA_DEDUCCIONES_UVT);
    const tope40 = totalIngresosBrutos * LIMITE_RENTA_EXENTA_DEDUCCIONES;
    return Math.min(topeUVT, tope40);
  }, [totalIngresosBrutos]);

  const exencionesAplicadas = Math.min(
    deduccionesImputables + rentaExentaLaboral,
    limiteExenciones40
  );

  const rentaLiquidaCedular = Math.max(totalIngresosBrutos - exencionesAplicadas, 0);

  const rentaPresuntivaPesos = useMemo(() => {
    // Tarifa 0% año gravable 2025 (Ley 2277 de 2022) — se conserva la estructura
    const porcentaje = 0;
    return Math.max(patrimonioLiquidoAnterior, 0) * porcentaje;
  }, [patrimonioLiquidoAnterior]);

  const rentaLiquidaGravable = Math.max(rentaLiquidaCedular, rentaPresuntivaPesos);

  const impuestoUVT = calcularImpuestoUVT(aUVT(rentaLiquidaGravable));
  const impuestoACargo = aPesos(impuestoUVT);

  const saldoFinal = impuestoACargo - totalRetenciones;

  /* -------------------- Validaciones -------------------- */

  function validarPaso(idx) {
    const err = {};
    if (PASOS[idx].id === "datos") {
      if (!datos.nit || !/^\d{6,10}$/.test(datos.nit))
        err.nit = "El NIT debe tener entre 6 y 10 dígitos, sin puntos ni guiones.";
      if (!datos.primerApellido) err.primerApellido = "Este campo es obligatorio.";
      if (!datos.primerNombre) err.primerNombre = "Este campo es obligatorio.";
      if (!datos.actividadEconomica)
        err.actividadEconomica = "Seleccione el código de actividad económica del RUT.";
      if (datos.aniosDeclarando && parseInt(datos.aniosDeclarando) < 0)
        err.aniosDeclarando = "El número de años no puede ser negativo.";
    }
    if (PASOS[idx].id === "patrimonio") {
      if (patrimonio.activosBruto === "")
        err.activosBruto = "Indique el valor total de su patrimonio bruto, aunque sea cero.";
      if (
        patrimonio.pasivos !== "" &&
        parseFloat(patrimonio.pasivos) > parseFloat(patrimonio.activosBruto || 0)
      )
        err.pasivos = "Los pasivos no pueden superar el total de activos brutos declarados.";
    }
    if (PASOS[idx].id === "ingresos") {
      const algunoDiligenciado =
        (perfil.salarios && ingresos.salarios) ||
        (perfil.honorarios && ingresos.honorarios) ||
        (perfil.capital && ingresos.capital) ||
        (perfil.pensiones && ingresos.pensiones) ||
        (perfil.ganancias && ingresos.ganancias);
      if (!algunoDiligenciado)
        err.general = "Diligencie al menos un valor de ingreso para las cédulas seleccionadas en su perfil.";
      if (
        perfil.salarios &&
        parseFloat(ingresos.retencionSalarios || 0) > parseFloat(ingresos.salarios || 0)
      )
        err.retencionSalarios = "La retención no puede ser mayor al ingreso bruto de esta cédula.";
    }
    return err;
  }

  function irSiguiente() {
    const err = validarPaso(pasoActivo);
    setErrores(err);
    setTocado((t) => ({ ...t, [pasoActivo]: true }));
    if (Object.keys(err).length === 0) {
      setPasoActivo((p) => Math.min(p + 1, PASOS.length - 1));
      setErrores({});
    }
  }

  function irAtras() {
    setErrores({});
    setPasoActivo((p) => Math.max(p - 1, 0));
  }

  function irAPaso(idx) {
    if (idx <= pasoActivo || tocado[pasoActivo]) {
      setErrores({});
      setPasoActivo(idx);
    }
  }

  const idPaso = PASOS[pasoActivo].id;

  /* ------------------------------------------------------------------ */
  return (
    <div
      style={{
        fontFamily: "'Inter', sans-serif",
        background: "#F7F3EA",
        minHeight: "100%",
        color: "#23201A",
        padding: "0",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        input:focus, select:focus { }
        ::selection { background: #EBD3C4; }
      `}</style>

      <div style={{ maxWidth: 980, margin: "0 auto", padding: "28px 20px 60px" }}>
        {/* Encabezado */}
        <div style={{ marginBottom: 28 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 6,
            }}
          >
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 8,
                background: "#C96442",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Receipt size={16} color="#FFF" />
            </div>
            <span
              style={{
                fontFamily: "'Inter', sans-serif",
                fontSize: 12.5,
                fontWeight: 600,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "#8A7F68",
              }}
            >
              Formulario 210 · Año gravable 2025
            </span>
          </div>
          <h1
            style={{
              fontFamily: "'Fraunces', serif",
              fontWeight: 500,
              fontSize: 32,
              margin: 0,
              color: "#1E1B15",
            }}
          >
            Declaración de renta — asistente guiado
          </h1>
          <p
            style={{
              fontSize: 14,
              color: "#6B6355",
              marginTop: 6,
              maxWidth: 600,
              lineHeight: 1.5,
            }}
          >
            Prototipo navegable del wizard para el contador. Los cálculos usan la tabla
            progresiva del artículo 241 del E.T. y la UVT {formatCOP(UVT_2025)} como
            referencia — ambos parámetros se administran centralmente.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 28 }}>
          {/* Rail de pasos */}
          <div>
            {PASOS.map((p, idx) => {
              const activo = idx === pasoActivo;
              const hecho = idx < pasoActivo;
              const Icono = p.icon;
              return (
                <button
                  key={p.id}
                  onClick={() => irAPaso(idx)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    width: "100%",
                    textAlign: "left",
                    background: "none",
                    border: "none",
                    cursor: idx <= pasoActivo || tocado[pasoActivo] ? "pointer" : "default",
                    padding: "10px 8px",
                    borderRadius: 8,
                    marginBottom: 2,
                    opacity: idx > pasoActivo && !tocado[pasoActivo] ? 0.45 : 1,
                    background: activo ? "#FFFFFF" : "transparent",
                    boxShadow: activo ? "0 1px 3px rgba(0,0,0,0.06)" : "none",
                  }}
                >
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: 999,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      fontSize: 11.5,
                      fontWeight: 700,
                      fontFamily: "'Inter', sans-serif",
                      background: hecho ? "#4B7B5D" : activo ? "#C96442" : "#EAE4D4",
                      color: hecho || activo ? "#FFF" : "#8A7F68",
                    }}
                  >
                    {hecho ? <Check size={13} /> : p.numero}
                  </div>
                  <span
                    style={{
                      fontSize: 13.5,
                      fontWeight: activo ? 600 : 500,
                      color: activo ? "#1E1B15" : "#5B5344",
                    }}
                  >
                    {p.titulo}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Panel de contenido */}
          <div
            style={{
              background: "#FFFFFF",
              border: "1px solid #EAE4D4",
              borderRadius: 14,
              padding: "28px 32px",
              boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
              minHeight: 480,
            }}
          >
            {idPaso === "perfil" && (
              <PasoPerfil perfil={perfil} setPerfil={setPerfil} />
            )}
            {idPaso === "datos" && (
              <PasoDatos datos={datos} setDatos={setDatos} errores={errores} />
            )}
            {idPaso === "patrimonio" && (
              <PasoPatrimonio
                patrimonio={patrimonio}
                setPatrimonio={setPatrimonio}
                errores={errores}
                patrimonioLiquido={patrimonioLiquido}
                patrimonioLiquidoAnterior={patrimonioLiquidoAnterior}
              />
            )}
            {idPaso === "ingresos" && (
              <PasoIngresos
                perfil={perfil}
                ingresos={ingresos}
                setIngresos={setIngresos}
                errores={errores}
                totalIngresosBrutos={totalIngresosBrutos}
                totalRetenciones={totalRetenciones}
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
                rentaLiquidaGravable={rentaLiquidaGravable}
                impuestoUVT={impuestoUVT}
                impuestoACargo={impuestoACargo}
                totalRetenciones={totalRetenciones}
                saldoFinal={saldoFinal}
              />
            )}
            {idPaso === "resumen" && (
              <PasoResumen
                datos={datos}
                patrimonioLiquido={patrimonioLiquido}
                totalIngresosBrutos={totalIngresosBrutos}
                rentaLiquidaGravable={rentaLiquidaGravable}
                impuestoACargo={impuestoACargo}
                totalRetenciones={totalRetenciones}
                saldoFinal={saldoFinal}
              />
            )}

            {errores.general && (
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  alignItems: "flex-start",
                  background: "#FBEAE8",
                  border: "1px solid #F0C7C2",
                  color: "#8C231C",
                  fontSize: 13,
                  borderRadius: 8,
                  padding: "10px 12px",
                  marginTop: 8,
                }}
              >
                <AlertCircle size={15} style={{ marginTop: 1, flexShrink: 0 }} />
                {errores.general}
              </div>
            )}

            {/* Navegación */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 32,
                paddingTop: 20,
                borderTop: "1px solid #EFEAE0",
              }}
            >
              <button
                onClick={irAtras}
                disabled={pasoActivo === 0}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "9px 16px",
                  borderRadius: 8,
                  border: "1px solid #DAD3C0",
                  background: "#FFF",
                  color: pasoActivo === 0 ? "#C9C2AE" : "#3A342A",
                  fontSize: 13.5,
                  fontWeight: 600,
                  cursor: pasoActivo === 0 ? "default" : "pointer",
                }}
              >
                <ChevronLeft size={15} /> Anterior
              </button>
              {pasoActivo < PASOS.length - 1 ? (
                <button
                  onClick={irSiguiente}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "9px 18px",
                    borderRadius: 8,
                    border: "none",
                    background: "#C96442",
                    color: "#FFF",
                    fontSize: 13.5,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Continuar <ChevronRight size={15} />
                </button>
              ) : (
                <button
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "9px 18px",
                    borderRadius: 8,
                    border: "none",
                    background: "#4B7B5D",
                    color: "#FFF",
                    fontSize: 13.5,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  <Check size={15} /> Marcar como lista
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PASO 0 — Perfil                                                     */
/* ------------------------------------------------------------------ */
function PasoPerfil({ perfil, setPerfil }) {
  const opciones = [
    { key: "salarios", titulo: "Salarios y pagos laborales", desc: "Relación laboral, legal o reglamentaria." },
    { key: "honorarios", titulo: "Honorarios y servicios", desc: "Independiente, sin relación laboral." },
    { key: "capital", titulo: "Rentas de capital", desc: "Intereses, arrendamientos, regalías." },
    { key: "pensiones", titulo: "Pensiones", desc: "Pensión de jubilación, invalidez o vejez." },
    { key: "ganancias", titulo: "Ganancias ocasionales", desc: "Loterías, herencias, venta de activos fijos." },
  ];
  return (
    <div>
      <TituloPaso
        titulo="¿Qué tipo de ingresos tuvo el declarante en 2025?"
        subtitulo="Seleccione todas las que apliquen — el asistente solo mostrará después los pasos relevantes para este perfil."
      />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {opciones.map((o) => {
          const activo = perfil[o.key];
          return (
            <button
              key={o.key}
              onClick={() => setPerfil((p) => ({ ...p, [o.key]: !p[o.key] }))}
              style={{
                textAlign: "left",
                padding: "14px 16px",
                borderRadius: 10,
                border: `1.5px solid ${activo ? "#C96442" : "#E4DFD1"}`,
                background: activo ? "#FBF1EB" : "#FFF",
                cursor: "pointer",
                display: "flex",
                gap: 10,
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 5,
                  border: `1.5px solid ${activo ? "#C96442" : "#C9C2AE"}`,
                  background: activo ? "#C96442" : "#FFF",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginTop: 2,
                  flexShrink: 0,
                }}
              >
                {activo && <Check size={12} color="#FFF" />}
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#23201A" }}>{o.titulo}</div>
                <div style={{ fontSize: 12.5, color: "#8A7F68", marginTop: 2 }}>{o.desc}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PASO 1 — Datos generales                                            */
/* ------------------------------------------------------------------ */
function PasoDatos({ datos, setDatos, errores }) {
  const set = (campo) => (e) => setDatos((d) => ({ ...d, [campo]: e.target.value }));
  return (
    <div>
      <TituloPaso
        titulo="1. Datos del declarante"
        subtitulo="Tome esta información directamente del RUT vigente en la DIAN."
      />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <Campo
          label="NIT"
          required
          casilla="5"
          ayuda="Número de Identificación Tributaria según el RUT, sin puntos ni guiones."
          error={errores.nit}
        >
          <TextInput
            value={datos.nit}
            onChange={set("nit")}
            hasError={!!errores.nit}
            placeholder="Ej: 79512345"
          />
        </Campo>
        <Campo label="Dígito de verificación (DV)" ayuda="Último dígito que asigna la DIAN al NIT.">
          <TextInput value={datos.dv} onChange={set("dv")} placeholder="Ej: 4" />
        </Campo>
        <Campo label="Primer apellido" required error={errores.primerApellido}>
          <TextInput
            value={datos.primerApellido}
            onChange={set("primerApellido")}
            hasError={!!errores.primerApellido}
          />
        </Campo>
        <Campo label="Primer nombre" required error={errores.primerNombre}>
          <TextInput
            value={datos.primerNombre}
            onChange={set("primerNombre")}
            hasError={!!errores.primerNombre}
          />
        </Campo>
        <Campo
          label="Actividad económica"
          required
          error={errores.actividadEconomica}
          ayuda="Código CIIU registrado en el RUT. Determina algunas deducciones y el cálculo del anticipo."
        >
          <Select
            value={datos.actividadEconomica}
            onChange={set("actividadEconomica")}
            hasError={!!errores.actividadEconomica}
            options={[
              { value: "empleado", label: "Asalariado / empleado" },
              { value: "independiente", label: "Servicios profesionales independientes" },
              { value: "rentista", label: "Rentista de capital" },
              { value: "otro", label: "Otra actividad" },
            ]}
          />
        </Campo>
        <Campo
          label="Años que ha declarado (incluido 2025)"
          ayuda="Se usa para calcular el anticipo de renta del año siguiente."
          error={errores.aniosDeclarando}
        >
          <TextInput
            type="number"
            value={datos.aniosDeclarando}
            onChange={set("aniosDeclarando")}
            hasError={!!errores.aniosDeclarando}
          />
        </Campo>
        <Campo
          label="Impuesto neto de renta 2024"
          casilla="126 (declaración anterior)"
          ayuda="Valor de la casilla 126 del Formulario 210 del año gravable 2024."
        >
          <TextInput
            type="number"
            prefix="$"
            value={datos.impuestoNetoAnterior}
            onChange={set("impuestoNetoAnterior")}
          />
        </Campo>
        <Campo
          label="Dependientes económicos"
          ayuda="Número de personas a cargo que dan derecho a la deducción del art. 387 E.T."
        >
          <TextInput type="number" value={datos.dependientes} onChange={set("dependientes")} />
        </Campo>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PASO 2 — Patrimonio                                                  */
/* ------------------------------------------------------------------ */
function PasoPatrimonio({
  patrimonio,
  setPatrimonio,
  errores,
  patrimonioLiquido,
  patrimonioLiquidoAnterior,
}) {
  const set = (campo) => (e) => setPatrimonio((p) => ({ ...p, [campo]: e.target.value }));
  return (
    <div>
      <TituloPaso
        titulo="2. Patrimonio"
        subtitulo="Bienes, derechos y obligaciones apreciables en dinero poseídos a 31 de diciembre de 2025."
      />

      <SubBloque titulo="Año anterior (2024) — referencia para renta presuntiva y comparación patrimonial">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <Campo label="Patrimonio bruto 2024" ayuda="Casilla informada en la declaración del año anterior.">
            <TextInput
              type="number"
              prefix="$"
              value={patrimonio.activosBrutoAnterior}
              onChange={set("activosBrutoAnterior")}
            />
          </Campo>
          <Campo label="Pasivos 2024">
            <TextInput
              type="number"
              prefix="$"
              value={patrimonio.pasivoAnterior}
              onChange={set("pasivoAnterior")}
            />
          </Campo>
        </div>
        <MiniResultado
          label="Patrimonio líquido 2024"
          valor={patrimonioLiquidoAnterior}
          nota="Base para el cálculo de la renta presuntiva del año 2025."
        />
      </SubBloque>

      <SubBloque titulo="Año gravable 2025">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <Campo
            label="Patrimonio bruto"
            required
            casilla="72"
            error={errores.activosBruto}
            ayuda="Suma de efectivo, inversiones, inventarios, activos fijos y bienes en moneda extranjera."
          >
            <TextInput
              type="number"
              prefix="$"
              value={patrimonio.activosBruto}
              onChange={set("activosBruto")}
              hasError={!!errores.activosBruto}
            />
          </Campo>
          <Campo label="Pasivos / deudas" casilla="73" error={errores.pasivos}>
            <TextInput
              type="number"
              prefix="$"
              value={patrimonio.pasivos}
              onChange={set("pasivos")}
              hasError={!!errores.pasivos}
            />
          </Campo>
        </div>
        <MiniResultado
          label="Patrimonio líquido 2025"
          valor={patrimonioLiquido}
          tono={patrimonioLiquido < 0 ? "negativo" : "positivo"}
          nota="Patrimonio bruto menos pasivos. Casilla 74 del Formulario 210."
        />
      </SubBloque>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PASO 3 — Ingresos / rentas cedulares                                 */
/* ------------------------------------------------------------------ */
function PasoIngresos({ perfil, ingresos, setIngresos, errores, totalIngresosBrutos, totalRetenciones }) {
  const set = (campo) => (e) => setIngresos((d) => ({ ...d, [campo]: e.target.value }));

  const bloques = [
    {
      activo: perfil.salarios,
      titulo: "Rentas de trabajo — salarios",
      campoIngreso: "salarios",
      campoReten: "retencionSalarios",
      ayuda: "Total de pagos laborales gravados recibidos durante 2025, antes de deducciones.",
      errorReten: errores.retencionSalarios,
    },
    {
      activo: perfil.honorarios,
      titulo: "Honorarios y servicios",
      campoIngreso: "honorarios",
      campoReten: "retencionHonorarios",
      ayuda: "Ingresos por servicios profesionales prestados sin relación laboral.",
    },
    {
      activo: perfil.capital,
      titulo: "Rentas de capital",
      campoIngreso: "capital",
      campoReten: "retencionCapital",
      ayuda: "Intereses, arrendamientos y rendimientos financieros.",
    },
    {
      activo: perfil.pensiones,
      titulo: "Pensiones",
      campoIngreso: "pensiones",
      campoReten: "retencionPensiones",
      ayuda: "Ingreso por mesadas pensionales; las primeras 1.000 UVT mensuales están exentas.",
    },
    {
      activo: perfil.ganancias,
      titulo: "Ganancias ocasionales",
      campoIngreso: "ganancias",
      campoReten: "retencionGanancias",
      ayuda: "Loterías, rifas, herencias, ventas de activos fijos poseídos por más de 2 años.",
    },
  ].filter((b) => b.activo);

  return (
    <div>
      <TituloPaso
        titulo="3. Rentas cedulares"
        subtitulo="Solo se muestran las cédulas seleccionadas en el paso de perfil."
      />
      {bloques.map((b) => (
        <SubBloque key={b.campoIngreso} titulo={b.titulo}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <Campo label="Ingreso bruto del año" ayuda={b.ayuda}>
              <TextInput
                type="number"
                prefix="$"
                value={ingresos[b.campoIngreso]}
                onChange={set(b.campoIngreso)}
              />
            </Campo>
            <Campo
              label="Retención en la fuente practicada"
              error={b.errorReten}
              ayuda="Suma de los certificados de retención recibidos para este concepto."
            >
              <TextInput
                type="number"
                prefix="$"
                value={ingresos[b.campoReten]}
                onChange={set(b.campoReten)}
                hasError={!!b.errorReten}
              />
            </Campo>
          </div>
        </SubBloque>
      ))}

      <SubBloque titulo="Deducciones imputables a la cédula general">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <Campo
            label="Aportes voluntarios a fondos de pensión / AFC"
            ayuda="Deducibles hasta el 30% del ingreso, sin exceder 3.800 UVT."
          >
            <TextInput
              type="number"
              prefix="$"
              value={ingresos.aportesVoluntarios}
              onChange={set("aportesVoluntarios")}
            />
          </Campo>
          <Campo label="Medicina prepagada / seguros de salud" ayuda="Deducible hasta 16 UVT mensuales.">
            <TextInput
              type="number"
              prefix="$"
              value={ingresos.saludPrepagada}
              onChange={set("saludPrepagada")}
            />
          </Campo>
        </div>
      </SubBloque>

      <div style={{ display: "flex", gap: 24, marginTop: 4 }}>
        <Metrica label="Total ingresos brutos" valor={totalIngresosBrutos} />
        <Metrica label="Total retenciones" valor={totalRetenciones} tono="acento" />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PASO 4 — Renta presuntiva                                            */
/* ------------------------------------------------------------------ */
function PasoPresuntiva({ patrimonioLiquidoAnterior, rentaPresuntivaPesos, rentaLiquidaCedular }) {
  return (
    <div>
      <TituloPaso
        titulo="6. Renta presuntiva"
        subtitulo="Se presume que la renta líquida no es inferior a un porcentaje del patrimonio líquido del año anterior."
      />
      <div
        style={{
          background: "#F7F3EA",
          border: "1px solid #EAE4D4",
          borderRadius: 10,
          padding: 18,
          marginBottom: 20,
          fontSize: 13.5,
          color: "#5B5344",
          lineHeight: 1.6,
        }}
      >
        Para el año gravable 2025, la tarifa de renta presuntiva quedó en <strong>0%</strong>{" "}
        (Ley 2277 de 2022), por lo cual este cálculo no genera renta líquida adicional. Se
        conserva la estructura del formulario porque puede volver a activarse en años futuros.
      </div>
      <div style={{ display: "flex", gap: 32 }}>
        <Metrica label="Patrimonio líquido 2024 (base)" valor={patrimonioLiquidoAnterior} />
        <Metrica label="Renta presuntiva calculada" valor={rentaPresuntivaPesos} tono="neutral" />
        <Metrica
          label="Renta líquida cedular (para comparar)"
          valor={rentaLiquidaCedular}
          tono="acento"
        />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PASO 5 — Liquidación privada                                         */
/* ------------------------------------------------------------------ */
function PasoLiquidacion({
  rentaLiquidaGravable,
  impuestoUVT,
  impuestoACargo,
  totalRetenciones,
  saldoFinal,
}) {
  return (
    <div>
      <TituloPaso
        titulo="7. Liquidación privada"
        subtitulo="Aplicación de la tabla progresiva del artículo 241 del Estatuto Tributario."
      />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        <Metrica label="Renta líquida gravable" valor={rentaLiquidaGravable} />
        <Metrica label="Equivalente en UVT" valor={aUVT(rentaLiquidaGravable) * UVT_2025} tono="neutral" />
      </div>

      <div
        style={{
          border: "1px solid #EAE4D4",
          borderRadius: 10,
          overflow: "hidden",
          marginBottom: 24,
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
          <thead>
            <tr style={{ background: "#F7F3EA", textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>Rango (UVT)</th>
              <th style={{ padding: "8px 12px" }}>Tarifa marginal</th>
            </tr>
          </thead>
          <tbody>
            {TABLA_TARIFA.map((t, i) => {
              const activo =
                aUVT(rentaLiquidaGravable) > t.desde && aUVT(rentaLiquidaGravable) <= t.hasta;
              return (
                <tr
                  key={i}
                  style={{
                    background: activo ? "#FBF1EB" : "transparent",
                    borderTop: "1px solid #EFEAE0",
                    fontWeight: activo ? 700 : 400,
                  }}
                >
                  <td style={{ padding: "7px 12px" }}>
                    {t.desde.toLocaleString("es-CO")} —{" "}
                    {t.hasta === Infinity ? "en adelante" : t.hasta.toLocaleString("es-CO")}
                  </td>
                  <td style={{ padding: "7px 12px" }}>{(t.tarifa * 100).toFixed(0)}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
        <Metrica label="Impuesto a cargo" valor={impuestoACargo} tono="acento" />
        <Metrica label="Menos: retenciones" valor={-totalRetenciones} />
        <Metrica
          label={saldoFinal >= 0 ? "Saldo a pagar" : "Saldo a favor"}
          valor={Math.abs(saldoFinal)}
          tono={saldoFinal >= 0 ? "negativo" : "positivo"}
          grande
        />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PASO 6 — Resumen                                                     */
/* ------------------------------------------------------------------ */
function PasoResumen({
  datos,
  patrimonioLiquido,
  totalIngresosBrutos,
  rentaLiquidaGravable,
  impuestoACargo,
  totalRetenciones,
  saldoFinal,
}) {
  const filas = [
    { label: "Declarante", valor: `${datos.primerNombre || "—"} ${datos.primerApellido || ""}` },
    { label: "NIT", valor: datos.nit || "—" },
    { label: "Patrimonio líquido 2025", valor: formatCOP(patrimonioLiquido) },
    { label: "Total ingresos brutos", valor: formatCOP(totalIngresosBrutos) },
    { label: "Renta líquida gravable", valor: formatCOP(rentaLiquidaGravable) },
    { label: "Impuesto a cargo", valor: formatCOP(impuestoACargo) },
    { label: "Retenciones practicadas", valor: formatCOP(totalRetenciones) },
  ];
  return (
    <div>
      <TituloPaso
        titulo="Resumen para el contador"
        subtitulo="Vista de control antes de trasladar la información al Formulario 210 en los Servicios Informáticos Electrónicos de la DIAN."
      />
      <div
        style={{
          border: "1px solid #EAE4D4",
          borderRadius: 10,
          overflow: "hidden",
          marginBottom: 24,
        }}
      >
        {filas.map((f, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "11px 16px",
              fontSize: 13.5,
              background: i % 2 === 0 ? "#FBF9F4" : "#FFF",
              borderTop: i === 0 ? "none" : "1px solid #F0ECE1",
            }}
          >
            <span style={{ color: "#6B6355" }}>{f.label}</span>
            <span style={{ fontWeight: 600 }}>{f.valor}</span>
          </div>
        ))}
      </div>

      <div
        style={{
          background: saldoFinal >= 0 ? "#FBEAE8" : "#EAF3EC",
          border: `1px solid ${saldoFinal >= 0 ? "#F0C7C2" : "#C9E1CE"}`,
          borderRadius: 10,
          padding: "18px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <div style={{ fontSize: 12.5, color: "#6B6355", marginBottom: 2 }}>
            {saldoFinal >= 0 ? "Casilla 134 — Saldo a pagar" : "Casilla 137 — Saldo a favor"}
          </div>
          <div
            style={{
              fontFamily: "'Fraunces', serif",
              fontSize: 26,
              fontWeight: 500,
              color: saldoFinal >= 0 ? "#B3261E" : "#4B7B5D",
            }}
          >
            {formatCOP(Math.abs(saldoFinal))}
          </div>
        </div>
        <FileCheck size={28} color={saldoFinal >= 0 ? "#B3261E" : "#4B7B5D"} />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Elementos compartidos                                                */
/* ------------------------------------------------------------------ */
function TituloPaso({ titulo, subtitulo }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h2
        style={{
          fontFamily: "'Fraunces', serif",
          fontWeight: 500,
          fontSize: 21,
          margin: "0 0 6px 0",
          color: "#1E1B15",
        }}
      >
        {titulo}
      </h2>
      {subtitulo && (
        <p style={{ fontSize: 13.5, color: "#8A7F68", margin: 0, lineHeight: 1.5 }}>{subtitulo}</p>
      )}
    </div>
  );
}

function SubBloque({ titulo, children }) {
  return (
    <div style={{ marginBottom: 26 }}>
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          color: "#C96442",
          marginBottom: 12,
          paddingBottom: 8,
          borderBottom: "1px solid #F0ECE1",
        }}
      >
        {titulo}
      </div>
      {children}
    </div>
  );
}

function MiniResultado({ label, valor, nota, tono = "neutral" }) {
  const colores = { neutral: "#23201A", positivo: "#4B7B5D", negativo: "#B3261E" };
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: "#F7F3EA",
        borderRadius: 8,
        padding: "10px 14px",
        marginTop: 4,
      }}
    >
      <div>
        <div style={{ fontSize: 12.5, fontWeight: 600, color: "#3A342A" }}>{label}</div>
        {nota && <div style={{ fontSize: 11.5, color: "#8A7F68", marginTop: 1 }}>{nota}</div>}
      </div>
      <div style={{ fontFamily: "'Fraunces', serif", fontSize: 18, color: colores[tono] }}>
        {formatCOP(valor)}
      </div>
    </div>
  );
}
