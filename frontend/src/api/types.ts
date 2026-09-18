export interface HealthResponse {
  status: "ok";
  service: string;
}

export type DependencyStatus = "ready" | "down";

export interface ReadinessResponse {
  status: "ready" | "unavailable";
  components: {
    postgresql: DependencyStatus;
    redis: DependencyStatus;
  };
}

export type EvidenceStatus = "GROUNDED" | "INSUFFICIENT_INFORMATION";

export interface PolicyQueryRequest {
  question: string;
  category?: string;
  region?: string;
}

export interface PolicyCitation {
  chunk_id: string;
  policy_code: string;
  policy_version: string;
  section_id: string;
  section_title: string;
  excerpt: string;
}

export interface PolicyAnswerResponse {
  request_id: string;
  answer: string;
  citations: PolicyCitation[];
  evidence_status: EvidenceStatus;
}

export type ExpenseDecision = "COMPLIANT" | "NON_COMPLIANT" | "NEEDS_REVIEW" | "INSUFFICIENT_INFORMATION";
export interface ExpenseRequest {
  expense_type?: "HOTEL" | "MEAL" | "TAXI";
  amount?: string;
  currency?: "INR";
  location?: string;
  travel_type?: "DOMESTIC" | "INTERNATIONAL";
  purpose?: string;
  receipt_available?: boolean;
}
export interface ExpenseAssessment {
  expense_id: string;
  thread_id: string;
  request_id: string;
  decision: ExpenseDecision;
  policy_limit: string | null;
  confidence: string;
  explanation: string;
  citations: PolicyCitation[];
  next_action: "NONE" | "PROVIDE_CLARIFICATION" | "SUBMIT_EXCEPTION_JUSTIFICATION" | "RETRY_LATER";
  missing_fields: string[];
}
