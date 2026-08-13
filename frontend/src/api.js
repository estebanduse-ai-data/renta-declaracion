/* ------------------------------------------------------------------ */
/* api.js — capa de comunicación con el backend FastAPI                */
/* Todos los fetch de la app pasan por aquí.                           */
/*                                                                     */
/* Cambios v0.4:                                                       */
/*   + importarDeclarantes()  — POST /admin/importar-declarantes       */
/*   + descargarPlantilla()   — GET  /admin/plantilla-declarantes      */
/*   + calcularLiquidacion()  — agrega periodo_id opcional al payload  */
/* Cambios v0.5 (Act. 1.1):                                            */
/*   + obtenerChecklist()     — GET  /declarantes/:d/periodos/:p/checklist      */
/*   + toggleDocumento()      — PATCH /declarantes/:d/periodos/:p/checklist/:t  */
/* ------------------------------------------------------------------ */

const BASE_URL = "http://localhost:8000";

/**
 * Wrapper central de fetch.
 * - Agrega Authorization: Bearer <token> si se provee.
 * - Lanza un Error con el `detail` del backend en caso de respuesta no-ok.
 * - En 401 lanza un error con code="UNAUTHORIZED" para redirigir al login.
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

export async function listarDeclarantes(token, { skip = 0, limit = 200, busqueda = "" } = {}) {
  const params = new URLSearchParams({ skip, limit });
  if (busqueda) params.set("busqueda", busqueda);
  // Devuelve: { total, skip, limit, items: [RespuestaDeclarante] }
  // Act. 1.3 — endpoint paginado; items contiene la página solicitada.
  return apiFetch(`/declarantes?${params}`, {}, token);
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
  // Body parcial: { estado?, patrimonio_bruto?, pasivos? }
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
  //   ingreso_salarios_pesos, total_retenciones_pesos,
  //   patrimonio_liquido_anterior_pesos,
  //   periodo_id?   ← NUEVO v0.4: si se provee, persiste el resultado en BD
  // }
  // Devuelve: {
  //   renta_liquida_gravable_pesos, impuesto_uvt, impuesto_a_cargo_pesos,
  //   total_retenciones_pesos, saldo_pesos, es_saldo_a_pagar,
  //   anio_gravable, uvt_utilizada,
  //   persistido    ← NUEVO v0.4: true si el resultado quedó guardado en periodo_gravable
  // }
}

/* ------------------------------------------------------------------ */
/* Admin — carga masiva (solo rol Admin)                               */
/* ------------------------------------------------------------------ */

/**
 * Importa declarantes desde un archivo Excel (.xlsx).
 * Nota: usa fetch directamente (no apiFetch) porque el body es FormData,
 * no JSON — no se puede setear Content-Type manualmente con FormData.
 *
 * @param {string} token   JWT del usuario Admin
 * @param {File}   archivo Objeto File del input[type=file]
 * @returns {Promise<RespuestaImportacion>}
 *   { total_filas, importados, omitidos, errores, detalle: [FilaResultado] }
 */
export async function importarDeclarantes(token, archivo) {
  const fd = new FormData();
  fd.append("archivo", archivo);

  const res = await fetch(`${BASE_URL}/admin/importar-declarantes`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    // NO poner Content-Type aquí: el browser lo setea automáticamente con el boundary
    body: fd,
  });

  if (res.status === 401) {
    const err = new Error("Sesión expirada. Por favor inicia sesión de nuevo.");
    err.code = "UNAUTHORIZED";
    throw err;
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try { const body = await res.json(); detail = body.detail || detail; } catch (_) {}
    throw new Error(detail);
  }

  return res.json();
}

/**
 * Descarga la plantilla Excel estándar para carga masiva de declarantes.
 * Abre el diálogo de descarga del navegador directamente.
 *
 * @param {string} token JWT del usuario Admin
 */
export async function descargarPlantilla(token) {
  const res = await fetch(`${BASE_URL}/admin/plantilla-declarantes`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) throw new Error(`Error ${res.status} al descargar la plantilla`);

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "plantilla_declarantes.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}
/* ------------------------------------------------------------------ */
/* Configuración pública (Act. 1.4 — accesible por todos los roles)   */
/* ------------------------------------------------------------------ */

/**
 * Devuelve los parámetros tributarios del año para display en el wizard:
 * UVT, tabla de tarifa y topes de deducciones.
 *
 * @param {string} token  JWT del usuario
 * @param {number} anio   Año gravable (ej: 2025)
 * @returns {Promise<ParametrosPublicos>}
 *   { anio, uvt, tabla_tarifa_uvt, porcentaje_renta_exenta_laboral,
 *     tope_renta_exenta_laboral_uvt, limite_renta_exenta_deducciones_porcentaje,
 *     tope_renta_exenta_deducciones_uvt }
 */
export async function obtenerParametrosPublicos(token, anio) {
  return apiFetch(`/configuracion/parametros-publicos/${anio}`, {}, token);
}

/**
 * Obtiene el checklist completo de documentos para un periodo gravable.
 * El backend inicializa los tipos faltantes como recibido=false
 * antes de responder, por lo que siempre devuelve los 8 tipos.
 *
 * @param {string} token        JWT del usuario
 * @param {string} declaranteId UUID del declarante
 * @param {string} periodoId    UUID del periodo gravable
 * @returns {Promise<RespuestaChecklist>}
 *   { periodo_id, items: [{ id, tipo_documento, recibido, marcado_por_id,
 *     actualizado_en }], total, recibidos, porcentaje }
 */
export async function obtenerChecklist(token, declaranteId, periodoId) {
  return apiFetch(
    `/declarantes/${declaranteId}/periodos/${periodoId}/checklist`,
    {},
    token,
  );
}

/**
 * Invierte el estado `recibido` de un tipo de documento.
 * Registra en BD el usuario que realizó el cambio.
 *
 * @param {string} token          JWT del usuario
 * @param {string} declaranteId   UUID del declarante
 * @param {string} periodoId      UUID del periodo gravable
 * @param {string} tipoDocumento  Valor del enum TipoDocumento (ej: "rut")
 * @returns {Promise<ItemChecklist>}
 *   { id, tipo_documento, recibido, marcado_por_id, actualizado_en }
 */
export async function toggleDocumento(token, declaranteId, periodoId, tipoDocumento) {
  return apiFetch(
    `/declarantes/${declaranteId}/periodos/${periodoId}/checklist/${tipoDocumento}`,
    { method: "PATCH" },
    token,
  );
}