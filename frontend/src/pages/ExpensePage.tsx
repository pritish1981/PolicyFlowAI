import { useState } from "react";
import { clarifyExpense, submitExpense } from "../api/expenseApi";
import type { ExpenseAssessment, ExpenseRequest } from "../api/types";
import { CitationPanel } from "../components/CitationPanel";

const labels: Record<string, string> = {
  expense_type: "Expense type", amount: "Amount (INR)", currency: "Currency",
  location: "Location", travel_type: "Travel type", purpose: "Purpose",
  receipt_available: "Receipt available",
};

export function ExpensePage() {
  const [form, setForm] = useState<ExpenseRequest>({ currency: "INR" });
  const [result, setResult] = useState<ExpenseAssessment | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [key, setKey] = useState(() => crypto.randomUUID());
  const change = (patch: ExpenseRequest) => setForm(previous => ({ ...previous, ...patch }));

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const request = { ...form };
      if (!request.amount) delete request.amount;
      if (!request.location) delete request.location;
      if (!request.purpose) delete request.purpose;
      const response = result?.missing_fields.length
        ? await clarifyExpense(result.expense_id, Object.fromEntries(
            result.missing_fields.map(field => [field, request[field as keyof ExpenseRequest]])
              .filter(([, value]) => value !== undefined)) as ExpenseRequest)
        : await submitExpense(request, key);
      setResult(response);
      if (response.missing_fields.length === 0) setKey(crypto.randomUUID());
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Assessment failed."); }
    finally { setBusy(false); }
  }

  return <section className="qa-layout" aria-labelledby="expense-title">
    <div className="qa-intro"><p className="eyebrow">Expense compliance</p>
      <h1 id="expense-title">Assess an expense.</h1>
      <p>Enter the expense details to check the active policy rules and supporting evidence.</p></div>
    <form className="policy-form" onSubmit={submit}>
      <div className="filter-row"><label>Expense type
        <select value={form.expense_type ?? ""} onChange={e => change({ expense_type: e.target.value as ExpenseRequest["expense_type"] })}>
          <option value="">Select type</option><option>HOTEL</option><option>MEAL</option><option>TAXI</option>
        </select></label><label>Travel type
        <select value={form.travel_type ?? ""} onChange={e => change({ travel_type: e.target.value as ExpenseRequest["travel_type"] })}>
          <option value="">Select travel</option><option>DOMESTIC</option><option>INTERNATIONAL</option>
        </select></label></div>
      <div className="filter-row"><label>Amount (INR)
        <input type="number" min="0.01" step="0.01" value={form.amount ?? ""}
          onChange={e => change({ amount: e.target.value })} /></label>
        <label>Location<input value={form.location ?? ""} maxLength={200}
          onChange={e => change({ location: e.target.value })} /></label></div>
      <label>Purpose<textarea value={form.purpose ?? ""} maxLength={1000}
        onChange={e => change({ purpose: e.target.value })} /></label>
      <label>Receipt available
        <select value={form.receipt_available === undefined ? "" : String(form.receipt_available)}
          onChange={e => change({ receipt_available: e.target.value === "" ? undefined : e.target.value === "true" })}>
          <option value="">Select receipt status</option><option value="true">Yes</option><option value="false">No</option>
        </select></label>
      <button disabled={busy} type="submit">{busy ? "Assessing…" : result?.missing_fields.length ? "Continue assessment" : "Assess expense"}</button>
    </form>
    {error && <div className="answer-card answer-card--error" role="alert">{error}</div>}
    {result && <div className={`answer-card expense-result expense-result--${result.decision.toLowerCase()}`} aria-live="polite">
      <span className="evidence-badge">{result.decision.replace(/_/g, " ")}</span>
      <h2>{result.decision === "NEEDS_REVIEW" ? "Human review required" : "Assessment result"}</h2>
      <p>{result.explanation}</p>
      {result.missing_fields.length > 0 && <p>Provide: {result.missing_fields.map(field => labels[field] ?? field).join(", ")}.</p>}
      {result.policy_limit !== null && <p>Policy limit: INR {result.policy_limit}</p>}
      <p>Confidence: {result.confidence} · Next action: {result.next_action.replace(/_/g, " ")}</p>
      <CitationPanel citations={result.citations} />
    </div>}
  </section>;
}
