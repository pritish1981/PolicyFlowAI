import type { StatusValue } from "../hooks/usePlatformStatus";

interface StatusCardProps {
  name: string;
  description: string;
  status: StatusValue;
}

const labels: Record<StatusValue, string> = {
  loading: "Checking",
  available: "Available",
  unavailable: "Unavailable",
  error: "Unable to check",
};

export function StatusCard({ name, description, status }: StatusCardProps) {
  return (
    <article className="status-card" aria-label={`${name} status`}>
      <div className="status-card__top">
        <h2>{name}</h2>
        <span className={`status-badge status-badge--${status}`} role="status" aria-live="polite">
          <span className="status-badge__dot" aria-hidden="true" />
          {labels[status]}
        </span>
      </div>
      <p>{description}</p>
      {status === "error" && <p className="status-card__hint">Check that the API is reachable.</p>}
    </article>
  );
}
