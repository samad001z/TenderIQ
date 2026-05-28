import type { ReactNode } from "react";

import { AppShell } from "@/components/shell/app-shell";

/** Public design baseline — wrapped in the shell (no auth) so it renders standalone. */
export default function DesignTestLayout({ children }: { children: ReactNode }) {
  return <AppShell title="Design System" subtitle="Visual baseline">{children}</AppShell>;
}
