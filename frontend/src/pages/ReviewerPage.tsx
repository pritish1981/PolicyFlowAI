import { useEffect, useState } from "react";
import { pendingReviews, reviewDetail, submitReview } from "../api/reviewApi";
import type { ReviewDecision, ReviewDetail, ReviewListItem } from "../api/types";
import { CitationPanel } from "../components/CitationPanel";

export function ReviewerPage() {
  const [items, setItems] = useState<ReviewListItem[]>([]);
  const [detail, setDetail] = useState<ReviewDetail | null>(null);
  const [comments, setComments] = useState(""); const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function refresh() { setItems(await pendingReviews()); }
  useEffect(() => { void refresh(); }, []);
  async function open(id: string) { setDetail(await reviewDetail(id)); setMessage(""); }
  async function act(decision: ReviewDecision) {
    if (!detail) return; setBusy(true);
    try { const result = await submitReview(detail.exception_id, decision, comments);
      setMessage(`${result.status.replace(/_/g, " ")}: human decision recorded.`); setDetail(null); await refresh(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Review failed."); }
    finally { setBusy(false); }
  }
  return <section className="qa-layout" aria-labelledby="review-title"><div className="qa-intro">
    <p className="eyebrow">Human authority</p><h1 id="review-title">Exception review queue.</h1>
    <p>AI summaries are non-authoritative. A reviewer makes every final exception decision.</p></div>
    {message && <p className="answer-card" role="status">{message}</p>}
    <div className="review-grid"><div>{items.length === 0 ? <p>No pending exceptions.</p> : items.map(item =>
      <button className="review-row" key={item.exception_id} onClick={() => void open(item.exception_id)}>
        {item.expense_type} · INR {item.amount} · variance {item.variance_amount ?? "n/a"}</button>)}</div>
      {detail && <article className="answer-card"><h2>{detail.expense_type} · INR {detail.amount}</h2>
        <p>Policy limit: {detail.policy_limit ?? "Not numeric"} · Variance: {detail.variance_amount ?? "Not available"}</p>
        <p><strong>Employee justification:</strong> {detail.justification}</p>
        {detail.review_summary ? <div><p className="eyebrow">AI-generated non-authoritative summary</p>
          <p>{detail.review_summary.summary}</p></div> : <p>AI summary unavailable. Review the authoritative facts.</p>}
        <CitationPanel citations={detail.citations} />
        <label>Reviewer comments<textarea value={comments} minLength={3} maxLength={2000} onChange={e => setComments(e.target.value)} /></label>
        <div className="review-actions">{(["APPROVE", "REJECT", "REQUEST_MORE_INFORMATION"] as ReviewDecision[]).map(action =>
          <button type="button" disabled={busy || comments.trim().length < 3} key={action} onClick={() => void act(action)}>{action.replace(/_/g, " ")}</button>)}</div>
      </article>}</div>
  </section>;
}
