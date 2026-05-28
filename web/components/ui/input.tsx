import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * High-contrast input. White-cream surface + dark navy text + a clear border, so the
 * field is unambiguously visible on every background TenderIQ uses — the obsidian
 * auth pane, the carbon bidder portal, AND the light government-portal workspace.
 *
 * (Earlier the input rendered as a barely-lighter dark grey on a dark pane, which
 * read to users as "white text boxes where I can't see what I'm typing".)
 */
const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-md border border-gov-border-strong bg-white px-3 py-1.5 font-sans text-[14px] text-gov-ink shadow-sm transition-colors",
        "placeholder:text-gov-ink-faint",
        "focus-visible:outline-none focus-visible:border-gov-navy focus-visible:ring-2 focus-visible:ring-gov-navy/20",
        "disabled:cursor-not-allowed disabled:bg-gov-bg disabled:opacity-60",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
