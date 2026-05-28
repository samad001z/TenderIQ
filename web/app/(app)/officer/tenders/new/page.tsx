"use client";

import dynamic from "next/dynamic";
import { UploadCloud } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { StatusDot } from "@/components/ui/status-dot";
import { SchemaPreview } from "@/components/officer/schema-preview";
import { getAccessToken, parseTenderStream, uploadTender } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { TenderSchema } from "@/lib/tender-schema";

const PdfViewer = dynamic(
  () => import("@/components/officer/pdf-viewer").then((m) => m.PdfViewer),
  { ssr: false, loading: () => <p className="p-4 text-[13px] text-cream-muted">Loading viewer…</p> },
);

type Phase = "idle" | "working" | "done" | "error";
type Step = { stage: string; message: string };

export default function NewTenderPage() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [steps, setSteps] = useState<Step[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const [schema, setSchema] = useState<TenderSchema | null>(null);
  const [signedUrl, setSignedUrl] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState<number | undefined>(undefined);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const start = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setError("Please choose a PDF file.");
      setPhase("error");
      return;
    }
    setFileName(file.name);
    setError(null);
    setSchema(null);
    setSignedUrl(null);
    setPhase("working");
    setSteps([{ stage: "uploading", message: `Uploading ${file.name}…` }]);

    const token = await getAccessToken();
    if (!token) {
      setError("Your session expired — please sign in again.");
      setPhase("error");
      return;
    }
    try {
      const up = await uploadTender(file, token);
      await parseTenderStream(up.tender_id, token, (event, data) => {
        if (event === "progress") {
          setSteps((s) => [...s, { stage: String(data.stage), message: String(data.message) }]);
        } else if (event === "done") {
          setSchema(data.schema as TenderSchema);
          setSignedUrl((data.signed_url as string) ?? null);
          setPageCount(typeof data.page_count === "number" ? data.page_count : undefined);
          setPage(1);
          setPhase("done");
        } else if (event === "error") {
          setError(String(data.message));
          setPhase("error");
        }
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setPhase("error");
    }
  }, []);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) start(file);
  };

  // ---- Done: split PDF + schema ----
  if (phase === "done" && schema && signedUrl) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-gov-border pb-3">
          <div>
            <h1 className="font-serif text-[24px] font-semibold leading-tight text-gov-ink">
              {schema.title.value || fileName}
            </h1>
            <p className="mt-1 font-mono text-[12px] text-gov-ink-muted">
              {schema.reference_no.value || "—"} · saved as draft · click any{" "}
              <span className="text-gov-saffron font-semibold">p.N</span> to jump to the source page
            </p>
          </div>
          <button
            onClick={() => setPhase("idle")}
            className="inline-flex items-center gap-2 rounded-sm border border-gov-border bg-gov-surface px-3 py-1.5 font-sans text-[12px] text-gov-navy hover:border-gov-navy"
          >
            Upload another
          </button>
        </div>
        <div className="grid h-[calc(100vh-260px)] grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="overflow-hidden rounded-sm border border-gov-border bg-gov-surface">
            <PdfViewer url={signedUrl} page={page} pageCount={pageCount} />
          </div>
          <div className="overflow-y-auto scrollbar-thin rounded-sm border border-gov-border bg-gov-surface py-2">
            <SchemaPreview schema={schema} onJump={setPage} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="border-b border-gov-border pb-3">
        <h1 className="font-serif text-[24px] font-semibold leading-tight text-gov-ink">
          Upload a new tender
        </h1>
        <p className="mt-1 text-[13px] text-gov-ink-muted">
          Upload the tender PDF — the system extracts a page-cited schema (eligibility, technical, financial
          format, evaluation method) for officer review.
        </p>
      </div>

      {/* Dropzone */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-sm border border-dashed px-6 py-16 text-center transition-colors",
          dragging
            ? "border-gov-navy bg-gov-navy-soft"
            : "border-gov-border-strong bg-gov-surface hover:border-gov-navy/60 hover:bg-gov-bg",
        )}
      >
        <UploadCloud className={cn("size-8", dragging ? "text-gov-navy" : "text-gov-ink-faint")} />
        <div>
          <p className="font-sans text-[14px] font-medium text-gov-ink">
            Drag &amp; drop a tender PDF, or click to browse
          </p>
          <p className="mt-1 font-mono text-[11px] text-gov-ink-faint">PDF · up to 50 MB</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) start(f);
            e.target.value = "";
          }}
        />
      </div>

      {/* Progress */}
      {(phase === "working" || phase === "error") && (
        <div className="rounded-sm border border-gov-border bg-gov-surface p-5">
          <p className="mb-3 font-mono text-[11px] uppercase tracking-wide text-gov-ink-muted">
            {fileName}
          </p>
          <ul className="space-y-3">
            {steps.map((step, i) => {
              const isLast = i === steps.length - 1;
              const running = phase === "working" && isLast;
              return (
                <li key={i} className="flex items-center gap-3 text-[13px]">
                  <StatusDot status={running ? "running" : "done"} />
                  <span className={running ? "text-gov-ink" : "text-gov-ink-muted"}>{step.message}</span>
                </li>
              );
            })}
            {phase === "error" && (
              <li className="flex items-center gap-3 text-[13px]">
                <StatusDot status="error" />
                <span className="text-gov-maroon">{error}</span>
              </li>
            )}
          </ul>
          {phase === "error" && (
            <button
              onClick={() => setPhase("idle")}
              className="mt-4 inline-flex items-center gap-2 rounded-sm border border-gov-border bg-gov-surface px-3 py-1.5 font-sans text-[12px] text-gov-navy hover:border-gov-navy"
            >
              Try again
            </button>
          )}
        </div>
      )}
    </div>
  );
}
