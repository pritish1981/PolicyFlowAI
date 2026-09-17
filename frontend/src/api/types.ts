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
