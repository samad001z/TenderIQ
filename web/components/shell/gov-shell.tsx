import type { ReactNode } from "react";

import { GovFooter } from "./gov-footer";
import { GovHeader } from "./gov-header";
import { GovLogoutButton } from "./gov-logout-button";
import { GovNav } from "./gov-nav";

/** The institutional officer-area shell.
 *  Header (tricolor + emblem + portal title) → primary nav → main content → footer.
 *  Replaces the obsidian AppShell for /officer routes. */
export function GovShell({
  fullName,
  ministry,
  children,
}: {
  fullName: string;
  ministry?: string | null;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gov-bg text-gov-ink">
      <GovHeader fullName={fullName} ministry={ministry} />
      <GovNav />
      <main id="main" className="mx-auto max-w-content px-6 py-6">
        {children}
      </main>
      <div className="mx-auto flex max-w-content items-center justify-end gap-3 px-6 pb-6">
        <GovLogoutButton />
      </div>
      <GovFooter />
    </div>
  );
}
