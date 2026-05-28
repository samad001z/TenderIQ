export type Role = "bidder" | "officer";

/** Where a signed-in, onboarded user should land. */
export function homePathForRole(role: Role | string | null | undefined): string {
  return role === "officer" ? "/officer/dashboard" : "/bidder/tenders";
}
