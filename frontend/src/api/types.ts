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

export type ExceptionStatus = "PENDING_REVIEW" | "MORE_INFORMATION_REQUIRED" | "APPROVED" | "REJECTED";
export type ReviewDecision = "APPROVE" | "REJECT" | "REQUEST_MORE_INFORMATION";
export interface ExceptionOutcome {
  exception_id: string; expense_id: string; thread_id: string; status: ExceptionStatus;
  variance_amount: string | null; next_action: "WAIT_FOR_REVIEW" | "PROVIDE_MORE_INFORMATION" | "COMPLETE";
  reviewer_comments: string | null;
}
export interface ReviewListItem {
  exception_id: string; expense_id: string; expense_type: string; amount: string; currency: string;
  policy_limit: string | null; variance_amount: string | null; justification: string; created_at: string;
}
export interface ReviewSummary {
  summary: string; key_facts: string[]; risk_or_attention_points: string[]; citation_chunk_ids: string[];
}
export interface ReviewDetail extends ReviewListItem {
  thread_id: string; status: ExceptionStatus; purpose: string; location: string;
  summary_status: "AVAILABLE" | "UNAVAILABLE" | "PENDING"; review_summary: ReviewSummary | null;
  citations: PolicyCitation[]; information_history: string[]; latest_reviewer_comments: string | null;
}
