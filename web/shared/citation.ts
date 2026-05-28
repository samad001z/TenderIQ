/**
 * TenderIQ — Citation contract (mirror of shared/citation.py).
 *
 * NON-NEGOTIABLE. Keep in manual sync with the Pydantic model in
 * `shared/citation.py`. Every AI-emitted claim conforms to this shape.
 *
 * Orchestrator (Python side) rejects + re-runs any citation with
 * page_number <= 0 or an empty quote; rejections log to agent_runs.rejections.
 */

export type Verdict = "PASS" | "FAIL" | "FLAG" | "INFO";
export type Severity = "low" | "medium" | "high" | "critical";

export interface Citation {
  /** Human-readable assertion. */
  claim: string;
  /** PASS | FAIL | FLAG | INFO. */
  verdict: Verdict;
  /** Source filename the quote is drawn from. */
  source_doc: string;
  /** 1-indexed page number in source_doc. */
  page_number: number;
  /** Exact, verbatim text from the source page. */
  quote: string;
  /** Model confidence, 0.0-1.0. */
  confidence: number;
  /** Referenced tender clause, if applicable. */
  tender_clause: string | null;
  /** 1-indexed page of the referenced tender clause, if applicable. */
  tender_clause_page: number | null;
  /** low | medium | high | critical. */
  severity: Severity;
  /** Identifier of the agent that emitted this. */
  agent: string;
}

export interface CitationList {
  citations: Citation[];
}

/** Orchestrator gate mirror — true if the citation passes the hard contract. */
export function isValidCitation(c: Citation): boolean {
  return c.page_number > 0 && c.quote.trim().length > 0;
}
