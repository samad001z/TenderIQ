"use client";

import { Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchPageHighlightBlob, getAccessToken } from "@/lib/api";
import { cn } from "@/lib/utils";

export type HighlightTarget = {
  bidId: string;
  sourceDoc: string;
  page: number;
  quote: string;
};

/** Centered modal showing the bid page rendered as PNG with a saffron-gold rectangle
 *  over the quote's bounding box. Server-rendered via /api/bids/{id}/page-highlight. */
export function PageHighlightModal({
  target, onClose,
}: {
  target: HighlightTarget | null;
  onClose: () => void;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [matched, setMatched] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!target) return;
    let revoke: string | null = null;
    let cancelled = false;
    setUrl(null); setError(null); setLoading(true);

    (async () => {
      try {
        const tok = await getAccessToken();
        if (!tok) throw new Error("Session expired — please sign in again.");
        const { url, matched } = await fetchPageHighlightBlob(
          target.bidId, target.sourceDoc, target.page, target.quote, tok,
        );
        if (cancelled) { URL.revokeObjectURL(url); return; }
        revoke = url;
        setUrl(url);
        setMatched(matched);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load page.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      if (revoke) URL.revokeObjectURL(revoke);
    };
  }, [target]);

  useEffect(() => {
    if (!target) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [target, onClose]);

  if (!target) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-gov-ink/70 p-6 backdrop-blur"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative flex max-h-[92vh] w-full max-w-[960px] flex-col overflow-hidden rounded-sm border border-gov-border bg-gov-surface shadow-2xl"
      >
        <div className="flex h-12 shrink-0 items-center justify-between border-b border-gov-border bg-gov-bg px-4">
          <div className="min-w-0">
            <span className="font-sans text-[11px] font-semibold uppercase tracking-wide text-gov-ink-muted">Evidence</span>
            <span className="ml-2 font-sans text-[13.5px] text-gov-ink">{target.sourceDoc}</span>
            <span className="ml-2 font-mono text-[12px] font-semibold text-gov-saffron">p.{target.page}</span>
          </div>
          <div className="flex items-center gap-3">
            {!loading && !error && !matched && (
              <span className="rounded-sm border border-gov-saffron/50 bg-gov-saffron-soft px-2 py-0.5 font-mono text-[10.5px] uppercase tracking-wide text-gov-ink">
                quote not located — showing the page
              </span>
            )}
            <button onClick={onClose} className="rounded-sm p-1.5 text-gov-ink-muted hover:bg-gov-bg hover:text-gov-ink">
              <X className="size-4" />
            </button>
          </div>
        </div>
        <div className="scrollbar-thin flex flex-1 items-start justify-center overflow-auto bg-gov-bg p-3">
          {loading && (
            <div className="flex h-72 items-center gap-2 font-mono text-[12px] text-gov-ink-muted">
              <Loader2 className="size-4 animate-spin text-gov-saffron" />
              Rendering p.{target.page} of {target.sourceDoc}…
            </div>
          )}
          {error && <p className="p-8 text-[13px] text-gov-maroon">{error}</p>}
          {url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={url}
              alt={`${target.sourceDoc} page ${target.page} with quote highlighted`}
              className="max-w-full rounded-sm border border-gov-border shadow-hair"
            />
          )}
        </div>
        {target.quote && (
          <div className="border-t border-gov-border bg-gov-surface px-4 py-3">
            <p className="font-sans text-[10.5px] font-semibold uppercase tracking-wide text-gov-ink-muted">
              Quote being matched
            </p>
            <p className="mt-1 font-serif italic text-[13px] leading-snug text-gov-ink-muted">
              “{target.quote.length > 380 ? target.quote.slice(0, 380) + "…" : target.quote}”
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
