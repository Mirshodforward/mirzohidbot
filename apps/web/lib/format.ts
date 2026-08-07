const TZ = "Asia/Tashkent";

/** 5000000 -> "5 000 000" (o'zbekcha o'qishga qulay ajratgich). */
export function money(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("uz-UZ").format(value).replace(/,/g, " ");
}

export function sum(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${money(value)} so'm`;
}

export function date(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: TZ,
  }).format(new Date(iso));
}

export function dateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: TZ,
  }).format(new Date(iso));
}

/** To'lov sanasigacha qolgan kunlar (Toshkent kunlari bo'yicha). */
export function daysUntil(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const target = new Date(iso);
  const now = new Date();
  const dayMs = 86_400_000;
  const t = Math.floor(target.getTime() / dayMs);
  const n = Math.floor(now.getTime() / dayMs);
  return t - n;
}
