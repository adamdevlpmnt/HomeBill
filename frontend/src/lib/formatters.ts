// Utilitaires de formatage de devises, nombres et dates avec Intl

export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined) return "0,00 DA";
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return "0,00 DA";

  const formatted = new Intl.NumberFormat("fr-DZ", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);

  return `${formatted} DA`;
}

export function formatNumber(
  val: number | string | null | undefined,
  decimals: number = 2
): string {
  if (val === null || val === undefined) return "0";
  const num = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(num)) return "0";

  return new Intl.NumberFormat("fr-DZ", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

export function formatConsumption(
  val: number | string | null | undefined,
  unit: string = "kWh",
  decimals: number = 1
): string {
  return `${formatNumber(val, decimals)} ${unit}`;
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;

  return new Intl.DateTimeFormat("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(d);
}

export function formatShortDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;

  return new Intl.DateTimeFormat("fr-FR", {
    day: "numeric",
    month: "short",
  }).format(d);
}

export function formatPercent(val: number | string | null | undefined): string {
  if (val === null || val === undefined) return "0,0 %";
  const num = typeof val === "string" ? parseFloat(val) : val;
  const prefix = num > 0 ? "+" : "";
  return `${prefix}${formatNumber(num, 1)} %`;
}
