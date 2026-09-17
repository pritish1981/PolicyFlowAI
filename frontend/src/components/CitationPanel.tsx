import type { PolicyCitation } from "../api/types";

export function CitationPanel({ citations }: { citations: PolicyCitation[] }) {
  if (!citations.length) return null;
  return (
    <section className="citations" aria-labelledby="citation-title">
      <h3 id="citation-title">Verified policy evidence</h3>
      <div className="citation-grid">
        {citations.map((citation) => (
          <article className="citation-card" key={citation.chunk_id}>
            <div className="citation-meta">
              <strong>{citation.policy_code}</strong>
              <span>Version {citation.policy_version}</span>
            </div>
            <h4>{citation.section_title}</h4>
            <p>{citation.excerpt}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
