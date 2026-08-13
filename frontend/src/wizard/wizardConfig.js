/**
 * wizardConfig.js — fuente única de verdad para constantes del wizard.
 *
 * Por qué existe este archivo
 * ─────────────────────────────
 * Antes de DT-2, PASOS, ANIO_GRAVABLE y PARAMETROS_FALLBACK estaban
 * definidos en DeclaracionRentaWizard.jsx y no eran importables desde
 * los hooks. Eso obligaba a duplicar el valor de ANIO_GRAVABLE (2025)
 * en tres lugares diferentes.
 *
 * Ahora tanto DeclaracionRentaWizard.jsx como useWizardForm.js y
 * useWizardApi.js importan desde aquí.
 */

import {
  Calculator,
  FileCheck,
  Layers,
  Receipt,
  User,
  Wallet,
} from "lucide-react";

export const ANIO_GRAVABLE = 2025;

export const PASOS = [
  { id: "perfil",      numero: "0", titulo: "Perfil",              icon: Layers    },
  { id: "datos",       numero: "1", titulo: "Datos generales",     icon: User      },
  { id: "patrimonio",  numero: "2", titulo: "Patrimonio",          icon: Wallet    },
  { id: "ingresos",    numero: "3", titulo: "Rentas cedulares",    icon: Layers    },
  { id: "presuntiva",  numero: "6", titulo: "Renta presuntiva",    icon: Calculator },
  { id: "liquidacion", numero: "7", titulo: "Liquidación privada", icon: Receipt   },
  { id: "resumen",     numero: "8", titulo: "Resumen",             icon: FileCheck },
];

/**
 * Valores de fallback para los parámetros tributarios 2025.
 * Se usan solo si /configuracion/parametros-publicos/2025 falla
 * (BD no poblada o primera carga sin conexión).
 */
export const PARAMETROS_FALLBACK = {
  uvt: 49799,
  tabla_tarifa_uvt: [
    { desde: 0,     hasta: 1090,   tarifa: 0,    base: 0     },
    { desde: 1090,  hasta: 1700,   tarifa: 0.19, base: 0     },
    { desde: 1700,  hasta: 4100,   tarifa: 0.28, base: 116   },
    { desde: 4100,  hasta: 8670,   tarifa: 0.33, base: 788   },
    { desde: 8670,  hasta: 18970,  tarifa: 0.35, base: 2296  },
    { desde: 18970, hasta: 31000,  tarifa: 0.37, base: 6901  },
    { desde: 31000, hasta: 999999, tarifa: 0.39, base: 11352 },
  ],
  porcentaje_renta_exenta_laboral:              0.25,
  tope_renta_exenta_laboral_uvt:                790,
  limite_renta_exenta_deducciones_porcentaje:   0.40,
  tope_renta_exenta_deducciones_uvt:            1340,
};