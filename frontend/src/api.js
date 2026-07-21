/* ------------------------------------------------------------------ */
/* api.js — capa de comunicación con el backend FastAPI                */
/* Todos los fetch de la app pasan por aquí.                           */
/* ------------------------------------------------------------------ */

const BASE_URL = "http://localhost:8000";

/**
 * Wrapper central de fetch.
 * - Agrega Authorization: Bearer <token> si se provee.
 * - Lanza un Error con el `detail` del backend en caso de respuesta no-ok.
 * - En 401 lanza un error especial para que App.jsx redirija al login.
 */
async function apiFetch(path, options = {}, token = null) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    const err = new Error("Sesión expirada. Por favor inicia sesión de nuevo.");
    err.code = "UNAUTHORIZED";
    throw err;
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) { /* respuesta sin JSON */ }
    throw new Error(detail);
  }

  // 204 No Content no tiene body
  if (res.status === 204) return null;
  return res.json();
}

/* ------------------------------------------------------------------ */
/* Auth                                                                */
/* ------------------------------------------------------------------ */

export async function login(email, password) {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  // Devuelve: { access_token, token_type, rol, nombre }
}

/* ------------------------------------------------------------------ */
/* Declarantes                                                         */
/* ------------------------------------------------------------------ */

export async function listarDeclarantes(token) {
  return apiFetch("/declarantes", {}, token);
  // Devuelve: [{ id, nit, digito_verificacion, primer_nombre, primer_apellido, actividad_economica }]
}

export async function crearDeclarante(token, datos) {
  return apiFetch("/declarantes", {
    method: "POST",
    body: JSON.stringify(datos),
  }, token);
  // Body: { nit, digito_verificacion, primer_nombre, primer_apellido, actividad_economica }
  // Devuelve: RespuestaDeclarante (incluye id UUID)
  // Lanza Error con detail si el NIT ya existe (409)
}

export async function obtenerDeclarante(token, declaranteId) {
  return apiFetch(`/declarantes/${declaranteId}`, {}, token);
}

/* ------------------------------------------------------------------ */
/* Periodos gravables                                                  */
/* ------------------------------------------------------------------ */

export async function crearPeriodo(token, declaranteId, datos) {
  return apiFetch(`/declarantes/${declaranteId}/periodos`, {
    method: "POST",
    body: JSON.stringify(datos),
  }, token);
  // Body: { anio, patrimonio_bruto, pasivos }
  // Lanza Error con detail si el periodo ya existe para ese año (409)
}

export async function listarPeriodos(token, declaranteId) {
  return apiFetch(`/declarantes/${declaranteId}/periodos`, {}, token);
}

export async function actualizarPeriodo(token, declaranteId, periodoId, datos) {
  return apiFetch(`/declarantes/${declaranteId}/periodos/${periodoId}`, {
    method: "PATCH",
    body: JSON.stringify(datos),
  }, token);
}

/* ------------------------------------------------------------------ */
/* Liquidación                                                         */
/* ------------------------------------------------------------------ */

export async function calcularLiquidacion(token, payload) {
  return apiFetch("/liquidacion/calcular", {
    method: "POST",
    body: JSON.stringify(payload),
  }, token);
  // Body: {
  //   anio_gravable, total_ingresos_brutos_pesos, deducciones_imputables_pesos,
  //   ingreso_salarios_pesos, total_retenciones_pesos, patrimonio_liquido_anterior_pesos
  // }
  // Devuelve: {
  //   renta_liquida_gravable_pesos, impuesto_uvt, impuesto_a_cargo_pesos,
  //   total_retenciones_pesos, saldo_pesos, es_saldo_a_pagar, anio_gravable, uvt_utilizada
  // }
}
