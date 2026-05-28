"use client";

import { CheckCircle2, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

import { getAccessToken, uploadBidDoc } from "@/lib/api";
import { cn } from "@/lib/utils";

export function BidDropzone({
  bidId,
  docType,
  label,
  onUploaded,
}: {
  bidId: string;
  docType: "technical" | "financial";
  label: string;
  onUploaded: (fileName: string) => void;
}) {
  const [state, setState] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function up(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setError("PDF only");
      setState("error");
      return;
    }
    setState("uploading");
    setError(null);
    const token = await getAccessToken();
    if (!token) {
      setError("Session expired");
      setState("error");
      return;
    }
    try {
      const r = await uploadBidDoc(bidId, docType, file, token);
      setName(r.file_name);
      setState("done");
      onUploaded(r.file_name);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setState("error");
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files?.[0];
        if (f) up(f);
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed px-4 py-8 text-center transition-colors",
        dragging
          ? "border-gold bg-gold-faint"
          : state === "done"
            ? "border-verdict-pass/50 bg-verdict-pass/5"
            : "border-smoke-strong bg-carbon-surface hover:border-gold/60",
      )}
    >
      {state === "done" ? (
        <>
          <CheckCircle2 className="size-6 text-verdict-pass" />
          <p className="font-sans text-[13px] font-medium text-cream">{label} uploaded</p>
          <p className="max-w-full truncate font-mono text-[11px] text-cream-faint">{name}</p>
          <p className="font-mono text-[10px] uppercase tracking-wide text-cream-faint">click to replace</p>
        </>
      ) : (
        <>
          <UploadCloud className={cn("size-6", dragging ? "text-gold" : "text-cream-faint")} />
          <p className="font-sans text-[13px] font-medium text-cream">{label}</p>
          <p className="font-mono text-[11px] text-cream-faint">
            {state === "uploading" ? "Uploading…" : "Drop PDF or click"}
          </p>
          {state === "error" && <p className="text-[11px] text-verdict-fail">{error}</p>}
        </>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) up(f);
          e.target.value = "";
        }}
      />
    </div>
  );
}
