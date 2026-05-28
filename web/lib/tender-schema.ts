// Mirrors api/models/tender_schema.py (TenderSchema). Kept in manual sync.

export type Sourced<T> = { value: T; source_page: number; quote: string };
export type EvaluationMethod = "L1" | "QCBS" | "LCS" | "unknown";
export type MIIClass = "I" | "II" | "none" | "unknown";

export interface EligibilityCriterion {
  description: string;
  source_page: number;
  quote: string;
}
export interface TechnicalCriterion {
  description: string;
  weight: number | null;
  source_page: number;
  quote: string;
}

export interface TenderSchema {
  title: Sourced<string>;
  reference_no: Sourced<string>;
  ministry: Sourced<string>;
  department: Sourced<string>;
  value_estimate: Sourced<number | null>;
  evaluation_method: EvaluationMethod;
  evaluation_method_source_page: number;
  evaluation_method_quote: string;
  qcbs_weights: { technical: number; financial: number; source_page: number };
  eligibility_criteria: EligibilityCriterion[];
  technical_criteria: TechnicalCriterion[];
  financial_format: Sourced<string>;
  emd_amount: Sourced<number | null>;
  pbg_percentage: Sourced<number | null>;
  integrity_pact_required: Sourced<boolean>;
  ppp_mii_class: MIIClass;
  ppp_mii_source_page: number;
  ppp_mii_quote: string;
  submission_deadline: Sourced<string>;
}
