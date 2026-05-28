"use client";

/**
 * PDF viewer via the browser's native renderer in an <iframe>.
 * We had react-pdf/pdfjs here, but pdfjs-dist fails to initialize under Next's
 * bundler ("Object.defineProperty called on non-object"). The native viewer is
 * robust, renders crisply, and honors the #page=N fragment for click-to-jump.
 * Remounting via key={page} forces the viewer to the requested page (the PDF
 * bytes are browser-cached, so the jump is fast).
 */
export function PdfViewer({
  url,
  page,
  pageCount,
}: {
  url: string;
  page: number;
  pageCount?: number;
}) {
  const src = `${url}#page=${page}&toolbar=0&navpanes=0&view=FitH`;
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-9 shrink-0 items-center justify-between border-b border-smoke px-3">
        <span className="font-mono text-[11px] uppercase tracking-wide text-cream-muted">
          Source PDF
        </span>
        <span className="font-mono text-[11px] tabular-nums text-cream-faint">
          page {page}
          {pageCount ? ` / ${pageCount}` : ""}
        </span>
      </div>
      <iframe key={page} src={src} title="Tender PDF" className="h-full w-full flex-1 bg-white" />
    </div>
  );
}
