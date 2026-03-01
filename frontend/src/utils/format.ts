/**
 * Formatação de valores para o mercado angolano
 */

/**
 * Formata valores monetários em Kwanzas (AOA)
 */
export function formatKz(value: number): string {
  return new Intl.NumberFormat("pt-AO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value) + " Kz";
}

/**
 * Formata valores monetários com código de moeda
 */
export function formatCurrency(value: number, currency: string = "AOA"): string {
  return new Intl.NumberFormat("pt-AO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value) + " Kz";
}

/**
 * Formata peso em quilogramas
 */
export function formatWeight(value: number): string {
  return `${new Intl.NumberFormat("pt-AO").format(value)} kg`;
}

/**
 * Formata datas para o formato angolano
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat("pt-AO", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(d);
}

/**
 * Formata data e hora completa
 */
export function formatDateTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat("pt-AO", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}
