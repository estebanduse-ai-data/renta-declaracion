/**
 * useWizardForm — estado del formulario, cálculos derivados y validaciones.
 *
 * Por qué existe este hook
 * ─────────────────────────
 * DeclaracionRentaWizard tenía 15+ useState mezclados con lógica de API
 * y el render de 400 líneas en el mismo componente. Eso hacía imposible:
 *   1. Probar los cálculos derivados (patrimonioLíquido, rentaExenta, etc.)
 *     sin montar el componente completo.
 *   2. Trabajar en los pasos del formulario en paralelo sin tocar el
 *     componente raíz.
 *   3. Entender de un vistazo dónde vive cada estado.
 *
 * Lo que contiene este hook
 * ──────────────────────────
 * • Estado de los 4 formularios: perfil, datos, patrimonio, ingresos.
 * • Estado de validación: errores y tocado (qué pasos ya se visitaron).
 * • Todos los useMemo de cálculo derivado (totales, renta exenta, etc.).
 * • La función validarPaso() — lógica de validación por paso.
 *
 * Lo que NO contiene
 * ───────────────────
 * • Llamadas a la API (eso va en useWizardApi).
 * • IDs de BD: declaranteId, periodoId (también en useWizardApi).
 * • Estado de navegación: pasoActivo (en el componente raíz).
 *
 * Dependencia de parámetros tributarios
 * ───────────────────────────────────────
 * Los cálculos de renta exenta y límite del 40% necesitan la UVT y los
 * topes. Se reciben como prop `parametros` desde el componente raíz
 * (que los carga vía useWizardApi). Esto evita que el hook de formulario
 * tenga que conocer la API.
 */

import { useMemo, useState } from "react";
import { PASOS } from "./wizardConfig.js";

// ── Estado inicial ─────────────────────────────────────────────────────────────

function estadoInicialDatos(declarante) {
  return {
    nit:               declarante?.nit                   ?? "",
    dv:                declarante?.digito_verificacion   ?? "",
    primerApellido:    declarante?.primer_apellido       ?? "",
    primerNombre:      declarante?.primer_nombre         ?? "",
    actividadEconomica: declarante?.actividad_economica ?? "",
    aniosDeclarando:   "",
    impuestoNetoAnterior: "",
    dependientes:      "0",
  };
}

function estadoInicialPatrimonio() {
  return {
    // año anterior
    activosBrutoAnterior: "", pasivoAnterior: "",
    // activos 2025 desglosados
    efectivoBancos: "", inversiones: "", cuentasCobrar: "",
    inventarios: "", propiedades: "", vehiculos: "", otrosActivos: "",
    // pasivos 2025 desglosados
    deudasBancarias: "", deudasPersonas: "", otrosPasivos: "",
    // totales manuales (sobreescriben la suma si se editan)
    activosBruto: "", pasivos: "",
  };
}

function estadoInicialIngresos() {
  return {
    // cédulas
    salarios: "", retencionSalarios: "",
    honorarios: "", retencionHonorarios: "",
    capital: "", retencionCapital: "",
    pensiones: "", retencionPensiones: "",
    ganancias: "", retencionGanancias: "",
    // deducciones — pensión y AFC
    fondoPension: "", afc: "",
    // deducciones — salud
    medicinaPrepagada: "", segurosComplementarios: "",
    // otras deducciones
    interesesVivienda: "", icetex: "", dependientes: "", donaciones: "",
  };
}

// ── Hook principal ─────────────────────────────────────────────────────────────

/**
 * @param {object} declarante  Declarante pre-cargado (modo edición) o null
 * @param {object} parametros  Parámetros tributarios vigentes (UVT, topes, etc.)
 */
export function useWizardForm(declarante, parametros) {

  // Formularios
  const [perfil,     setPerfil]     = useState({ salarios: true, honorarios: false, capital: false, pensiones: false, ganancias: false });
  const [datos,      setDatos]      = useState(() => estadoInicialDatos(declarante));
  const [patrimonio, setPatrimonio] = useState(estadoInicialPatrimonio);
  const [ingresos,   setIngresos]   = useState(estadoInicialIngresos);

  // Validación
  const [errores, setErrores] = useState({});
  const [tocado,  setTocado]  = useState({});

  // ── Cálculos derivados — Patrimonio ───────────────────────────────────────

  const totalActivos2025 = useMemo(() =>
    ["efectivoBancos", "inversiones", "cuentasCobrar",
     "inventarios", "propiedades", "vehiculos", "otrosActivos"]
      .reduce((s, k) => s + (parseFloat(patrimonio[k]) || 0), 0),
  [patrimonio]);

  const totalPasivos2025 = useMemo(() =>
    ["deudasBancarias", "deudasPersonas", "otrosPasivos"]
      .reduce((s, k) => s + (parseFloat(patrimonio[k]) || 0), 0),
  [patrimonio]);

  const patrimonioLiquidoAnterior = useMemo(() =>
    (parseFloat(patrimonio.activosBrutoAnterior) || 0)
    - (parseFloat(patrimonio.pasivoAnterior)     || 0),
  [patrimonio]);

  // Si el usuario editó el total manual lo usamos; si no, la suma del desglose
  const patrimonioBrutoEfectivo = parseFloat(patrimonio.activosBruto) || totalActivos2025;
  const pasivosEfectivos        = parseFloat(patrimonio.pasivos)       || totalPasivos2025;
  const patrimonioLiquido       = patrimonioBrutoEfectivo - pasivosEfectivos;

  // ── Cálculos derivados — Ingresos ─────────────────────────────────────────

  const totalIngresosBrutos = useMemo(() =>
    [
      perfil.salarios   && ingresos.salarios,
      perfil.honorarios && ingresos.honorarios,
      perfil.capital    && ingresos.capital,
      perfil.pensiones  && ingresos.pensiones,
      perfil.ganancias  && ingresos.ganancias,
    ].reduce((acc, v) => acc + (parseFloat(v) || 0), 0),
  [ingresos, perfil]);

  const totalRetenciones = useMemo(() =>
    [
      perfil.salarios   && ingresos.retencionSalarios,
      perfil.honorarios && ingresos.retencionHonorarios,
      perfil.capital    && ingresos.retencionCapital,
      perfil.pensiones  && ingresos.retencionPensiones,
      perfil.ganancias  && ingresos.retencionGanancias,
    ].reduce((acc, v) => acc + (parseFloat(v) || 0), 0),
  [ingresos, perfil]);

  const totalDeducciones = useMemo(() =>
    ["fondoPension", "afc", "medicinaPrepagada", "segurosComplementarios",
     "interesesVivienda", "icetex", "dependientes", "donaciones"]
      .reduce((acc, k) => acc + (parseFloat(ingresos[k]) || 0), 0),
  [ingresos]);

  // ── Cálculos derivados — Motor local (preview; el definitivo lo hace el backend) ──

  const rentaExentaLaboral = useMemo(() => {
    const uvt  = parametros.uvt;
    const tope = parametros.tope_renta_exenta_laboral_uvt;
    const pct  = parametros.porcentaje_renta_exenta_laboral;
    return Math.min((parseFloat(ingresos.salarios) || 0) * pct, tope * uvt);
  }, [ingresos.salarios, parametros]);

  const limiteExenciones40 = useMemo(() => {
    const uvt  = parametros.uvt;
    const tope = parametros.tope_renta_exenta_deducciones_uvt;
    const pct  = parametros.limite_renta_exenta_deducciones_porcentaje;
    return Math.min(totalIngresosBrutos * pct, tope * uvt);
  }, [totalIngresosBrutos, parametros]);

  const exencionesAplicadas  = Math.min(totalDeducciones + rentaExentaLaboral, limiteExenciones40);
  const rentaLiquidaCedular  = Math.max(totalIngresosBrutos - exencionesAplicadas, 0);
  const rentaPresuntivaPesos = 0; // Tarifa 0% — Ley 2277 de 2022

  // ── Validación por paso ────────────────────────────────────────────────────

  function validarPaso(idx) {
    const err = {};
    const id  = PASOS[idx].id;

    if (id === "datos") {
      if (!datos.nit || !/^\d{6,10}$/.test(datos.nit))
        err.nit = "El NIT debe tener entre 6 y 10 dígitos, sin puntos ni guiones.";
      if (!datos.primerApellido)
        err.primerApellido = "Este campo es obligatorio.";
      if (!datos.primerNombre)
        err.primerNombre = "Este campo es obligatorio.";
      if (!datos.actividadEconomica)
        err.actividadEconomica = "Seleccione el código de actividad económica del RUT.";
      if (datos.aniosDeclarando && parseInt(datos.aniosDeclarando) < 0)
        err.aniosDeclarando = "El número de años no puede ser negativo.";
    }

    if (id === "patrimonio") {
      const bruto = parseFloat(patrimonio.activosBruto) || totalActivos2025;
      const pas   = parseFloat(patrimonio.pasivos)       || totalPasivos2025;
      if (!bruto && bruto !== 0)
        err.activosBruto = "Indique el valor total de su patrimonio bruto, aunque sea cero.";
      if (pas > bruto)
        err.pasivos = "Los pasivos no pueden superar el total de activos brutos.";
    }

    if (id === "ingresos") {
      const alguno =
        (perfil.salarios   && ingresos.salarios)   ||
        (perfil.honorarios && ingresos.honorarios) ||
        (perfil.capital    && ingresos.capital)    ||
        (perfil.pensiones  && ingresos.pensiones)  ||
        (perfil.ganancias  && ingresos.ganancias);
      if (!alguno)
        err.general = "Diligencie al menos un valor de ingreso para las cédulas seleccionadas.";
      if (perfil.salarios && parseFloat(ingresos.retencionSalarios || 0) > parseFloat(ingresos.salarios || 0))
        err.retencionSalarios = "La retención no puede ser mayor al ingreso bruto de esta cédula.";
    }

    return err;
  }

  // ── API pública del hook ───────────────────────────────────────────────────

  return {
    // Formularios
    perfil,     setPerfil,
    datos,      setDatos,
    patrimonio, setPatrimonio,
    ingresos,   setIngresos,

    // Validación
    errores, setErrores,
    tocado,  setTocado,

    // Cálculos derivados — Patrimonio
    totalActivos2025,
    totalPasivos2025,
    patrimonioLiquidoAnterior,
    patrimonioBrutoEfectivo,
    pasivosEfectivos,
    patrimonioLiquido,

    // Cálculos derivados — Ingresos
    totalIngresosBrutos,
    totalRetenciones,
    totalDeducciones,
    rentaExentaLaboral,
    rentaLiquidaCedular,
    rentaPresuntivaPesos,

    // Validación
    validarPaso,
  };
}