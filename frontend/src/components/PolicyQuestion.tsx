import { FormEvent, useState } from "react";

interface Props {
  loading: boolean;
  onSubmit: (question: string, category?: string, region?: string) => void;
}

const EXAMPLE = "What is the maximum hotel reimbursement allowed for domestic travel?";

export function PolicyQuestion({ loading, onSubmit }: Props) {
  const [question, setQuestion] = useState(EXAMPLE);
  const [category, setCategory] = useState("HOTEL");
  const [region, setRegion] = useState("INDIA");
  const trimmed = question.trim();
  const error = trimmed.length > 0 && (trimmed.length < 3 || trimmed.length > 2000)
    ? "Question must contain between 3 and 2,000 characters."
    : "";

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!loading && !error && trimmed.length >= 3) {
      onSubmit(trimmed, category.trim() || undefined, region.trim() || undefined);
    }
  }

  return (
    <form className="policy-form" onSubmit={submit}>
      <label htmlFor="policy-question">Policy question</label>
      <textarea
        id="policy-question"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        maxLength={2000}
        aria-describedby={error ? "question-error" : undefined}
        rows={4}
      />
      {error && <p id="question-error" className="field-error" role="alert">{error}</p>}
      <div className="filter-row">
        <label>Category<input value={category} onChange={(event) => setCategory(event.target.value)} /></label>
        <label>Region<input value={region} onChange={(event) => setRegion(event.target.value)} /></label>
      </div>
      <button type="submit" disabled={loading || !!error || trimmed.length < 3}>
        {loading ? "Checking policy…" : "Ask PolicyFlow"}
      </button>
    </form>
  );
}
