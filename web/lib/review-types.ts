/** TenderIQ — Phase 6 review types. Mirrors api/services/review_pipeline + routes/review. */

export type Verdict = "PASS" | "FAIL" | "FLAG" | "INFO";
export type Severity = "low" | "medium" | "high" | "critical";

export type ClaimRow = {
  bid_id: string;
  agent_run_id: string | null;
  agent: string;
  claim: string;
  verdict: Verdict;
  source_doc: string;
  page_number: number;
  quote: string;
  confidence: number;
  tender_clause: string | null;
  tender_clause_page: number | null;
  severity: Severity;
};

export type RankingRow = {
  rank: number | null;
  bid_id: string;
  org_name: string;
  quoted_amount: number | null;
  technical_score: number | null;
  financial_score: number | null;
  combined_score: number | null;
  recommended_action: "award" | "shortlist" | "review" | "reject" | null;
  bid_status: string;
  needs_human_review: boolean;
  summary: string | null;
};

export type Disagreement = {
  type: string;
  bid_id?: string;
  org_name?: string;
  note?: string;
  conflicting_claims?: Array<{
    claim: string; verdict: Verdict; agent: string;
    source_doc: string; page_number: number; quote: string; severity: Severity;
  }>;
  bids?: Array<{ bid_id: string; org_name: string; quoted_amount: number }>;
  spread_pct?: number;
  threshold_pct?: number;
};

/** What review-summary returns (post-review snapshot). */
export type ReviewSummary = {
  tender_id: string;
  tender: {
    id: string;
    title: string | null;
    reference_no: string | null;
    ministry: string | null;
    department: string | null;
    estimated_value: number | null;
    evaluation_method: string | null;
    last_reviewed_at: string | null;
  };
  reviewed: boolean;
  ranking: RankingRow[];
  bids: Array<{
    bid_id: string;
    org_name: string;
    bid_status: string;
    quoted_amount: number | null;
    technical_score: number | null;
    financial_score: number | null;
    combined_score: number | null;
    review_rank: number | null;
    recommended_action: RankingRow["recommended_action"];
    summary: string | null;
    rationale: string | null;
    agents: Array<{ agent: string; verdict: Verdict; claims: ClaimRow[] }>;
  }>;
  recommended_award: string | null;
  human_review_required: string[];
};

/** SSE event payloads from POST /api/tenders/{id}/review. */
export type ReviewStartEvent      = { tender_id: string; evaluation_method: string; bids: number };
export type BidStartEvent         = { bid_id: string; org_name: string };
export type AgentStartEvent       = { bid_id?: string; agent: string; scope?: string };
export type ClaimEmittedEvent     = ClaimRow;
export type AgentCompleteEvent    = {
  bid_id?: string; agent: string; status: string; verdict: Verdict;
  claims: number; rejections?: number; elapsed_ms: number;
  agent_run_id?: string | null; error?: string | null;
};
export type OrchestratorCompleteEvent = {
  tender_id: string; evaluation_method: string; ranking: RankingRow[];
  disagreements: Disagreement[]; human_review_required: string[];
  recommended_award: string | null;
};

export type ReviewEvent =
  | { event: "review_start"; data: ReviewStartEvent }
  | { event: "bid_start"; data: BidStartEvent }
  | { event: "agent_start"; data: AgentStartEvent }
  | { event: "claim_emitted"; data: ClaimEmittedEvent }
  | { event: "agent_complete"; data: AgentCompleteEvent }
  | { event: "disagreement_detected"; data: Disagreement }
  | { event: "orchestrator_complete"; data: OrchestratorCompleteEvent }
  | { event: "review_error"; data: { message: string } };

/** Display order for the agent card grid + the comparison matrix columns. */
export const ALL_AGENTS = [
  "ingestion_agent",
  "tender_parser_agent",
  "eligibility_agent",
  "technical_agent",
  "compliance_agent",
  "financial_agent",
  "risk_agent",
] as const;

/** Five specialists + the synthesised Final column for the comparison matrix. */
export const MATRIX_COLUMNS = [
  { key: "eligibility_agent", label: "Eligibility" },
  { key: "technical_agent",   label: "Technical" },
  { key: "compliance_agent",  label: "Compliance" },
  { key: "financial_agent",   label: "Financial" },
  { key: "risk_agent",        label: "Risk" },
  { key: "final",             label: "Final" },
] as const;

/** Short human label for the agent column in the live grid. */
export const AGENT_LABEL: Record<string, string> = {
  ingestion_agent: "Ingestion",
  tender_parser_agent: "Tender Parser",
  eligibility_agent: "Eligibility",
  technical_agent: "Technical",
  compliance_agent: "Compliance",
  financial_agent: "Financial",
  risk_agent: "Risk",
  reasoning_agent: "Reasoning",
};
