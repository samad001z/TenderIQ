import { createClient } from "@/lib/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Current Supabase access token (sent as Bearer to the FastAPI backend). */
export async function getAccessToken(): Promise<string | null> {
  const { data } = await createClient().auth.getSession();
  return data.session?.access_token ?? null;
}

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

// ---- Tenders (officer) ----
export type UploadResult = { tender_id: string; storage_path: string; file_name: string };

export async function uploadTender(file: File, token: string): Promise<UploadResult> {
  const fd = new FormData();
  fd.append("file", file);
  return jsonOrThrow(
    await fetch(`${API_BASE}/api/tenders/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    }),
  );
}

export async function fetchTenderFileUrl(tenderId: string, token: string): Promise<string> {
  const data = await jsonOrThrow(
    await fetch(`${API_BASE}/api/tenders/${tenderId}/file-url`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  );
  return data.signed_url as string;
}

// ---- Bids (bidder) ----
export async function ensureBid(tenderId: string, token: string): Promise<{ bid_id: string; status: string }> {
  return jsonOrThrow(
    await fetch(`${API_BASE}/api/bids/ensure`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ tender_id: tenderId }),
    }),
  );
}

export async function uploadBidDoc(
  bidId: string,
  docType: "technical" | "financial",
  file: File,
  token: string,
): Promise<{ ok: boolean; doc_type: string; file_name: string }> {
  const fd = new FormData();
  fd.append("doc_type", docType);
  fd.append("file", file);
  return jsonOrThrow(
    await fetch(`${API_BASE}/api/bids/${bidId}/documents`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    }),
  );
}

export async function submitBid(bidId: string, token: string): Promise<{ status: string }> {
  return jsonOrThrow(
    await fetch(`${API_BASE}/api/bids/${bidId}/submit`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }),
  );
}

// ---- SSE (POST) ----
export type SSEHandler = (event: string, data: Record<string, unknown>) => void;

async function postSSE(path: string, token: string, onEvent: SSEHandler): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok || !res.body) throw new Error(`Request failed (${res.status})`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const messages = buf.split("\n\n");
    buf = messages.pop() ?? "";
    for (const msg of messages) {
      let event = "message";
      let dataStr = "";
      for (const line of msg.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataStr += line.slice(5).trim();
      }
      if (dataStr) onEvent(event, JSON.parse(dataStr));
    }
  }
}

export const parseTenderStream = (tenderId: string, token: string, onEvent: SSEHandler) =>
  postSSE(`/api/tenders/${tenderId}/parse`, token, onEvent);

export const eligibilityCheckStream = (bidId: string, token: string, onEvent: SSEHandler) =>
  postSSE(`/api/bids/${bidId}/eligibility-check`, token, onEvent);

export const complianceCheckStream = (bidId: string, token: string, onEvent: SSEHandler) =>
  postSSE(`/api/bids/${bidId}/compliance-check`, token, onEvent);

// ---- Officer review (Phase 6) ----
export const reviewTenderStream = (tenderId: string, token: string, onEvent: SSEHandler) =>
  postSSE(`/api/tenders/${tenderId}/review`, token, onEvent);

import type { ReviewSummary } from "@/lib/review-types";

export async function fetchReviewSummary(tenderId: string, token: string): Promise<ReviewSummary> {
  return jsonOrThrow(
    await fetch(`${API_BASE}/api/tenders/${tenderId}/review-summary`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  );
}

/** Fetch the highlighted-page PNG as a blob URL (so we can use it in <img src>). */
export async function fetchPageHighlightBlob(
  bidId: string,
  sourceDoc: string,
  page: number,
  quote: string,
  token: string,
): Promise<{ url: string; matched: boolean; pageCount: number }> {
  const params = new URLSearchParams({ source_doc: sourceDoc, page: String(page), quote });
  const res = await fetch(`${API_BASE}/api/bids/${bidId}/page-highlight?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Highlight failed (${res.status})`);
  const blob = await res.blob();
  return {
    url: URL.createObjectURL(blob),
    matched: res.headers.get("X-Highlight-Matched") === "1",
    pageCount: Number(res.headers.get("X-Page-Count") ?? "0") || 0,
  };
}

/** Open the audit PDF in a new tab. Requires the auth token in the URL path is awkward;
 *  we instead fetch the bytes and open a blob URL. */
export async function openAuditPdf(tenderId: string, token: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/tenders/${tenderId}/audit-pdf`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Audit PDF failed (${res.status})`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
