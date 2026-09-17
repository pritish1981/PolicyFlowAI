import { useEffect, useRef, useState } from "react";
import { queryPolicy } from "../api/policyApi";
import type { PolicyAnswerResponse } from "../api/types";
import { CitationPanel } from "../components/CitationPanel";
import { PolicyQuestion } from "../components/PolicyQuestion";

export function PolicyQAPage() {
  const [result, setResult] = useState<PolicyAnswerResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  async function submit(question: string, category?: string, region?: string) {
    controller.current?.abort();
    controller.current = new AbortController();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await queryPolicy({ question, category, region }, controller.current.signal));
    } catch (reason) {
      if (!controller.current.signal.aborted) {
        setError(reason instanceof Error ? reason.message : "Unable to answer the policy question.");
      }
    } finally {
      setLoading(false);
    }
  }

  const grounded = result?.evidence_status === "GROUNDED" && result.citations.length > 0;
  return (
    <section className="qa-layout" aria-labelledby="qa-title">
      <div className="qa-intro">
        <p className="eyebrow">Verified policy answers</p>
        <h1 id="qa-title">Ask an expense-policy question.</h1>
        <p>Answers are generated only from active policy evidence and include verified citations.</p>
      </div>
      <PolicyQuestion loading={loading} onSubmit={submit} />
      {error && <div className="answer-card answer-card--error" role="alert">{error}</div>}
      {result && (
        <div className={`answer-card ${grounded ? "answer-card--grounded" : "answer-card--abstain"}`}>
          <span className="evidence-badge">{result.evidence_status.replace(/_/g, " ")}</span>
          <h2>{grounded ? "Policy answer" : "More evidence is needed"}</h2>
          <p>{result.answer}</p>
          {grounded && <CitationPanel citations={result.citations} />}
        </div>
      )}
    </section>
  );
}
