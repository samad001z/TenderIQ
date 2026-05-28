/** ₹ with Indian digit grouping (12,34,567). */
export function formatINR(n: number | null | undefined): string {
  if (n == null) return "—";
  return `₹ ${new Intl.NumberFormat("en-IN").format(n)}`;
}

/** Whole days until an ISO timestamp (negative if past). */
export function daysUntil(iso: string | null | undefined): number | null {
  if (!iso) return null;
  return Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000);
}
