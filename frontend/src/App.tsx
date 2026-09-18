import { StatusCard } from "./components/StatusCard";
import { usePlatformStatus } from "./hooks/usePlatformStatus";
import "./App.css";
import { PolicyQAPage } from "./pages/PolicyQAPage";
import { ExpensePage } from "./pages/ExpensePage";

export default function App() {
  const { status, refresh } = usePlatformStatus();

  return (
    <main className="page-shell">
      <header className="page-header">
        <div className="brand-mark" aria-hidden="true">P</div>
        <span>PolicyFlow AI</span>
      </header>

      <PolicyQAPage />
      <ExpensePage />

      <section className="system-panel system-panel--compact" aria-labelledby="system-title">
        <div className="system-panel__heading">
          <div>
            <p className="eyebrow">Live checks</p>
            <h2 id="system-title">System status</h2>
          </div>
          <button type="button" onClick={refresh}>Refresh status</button>
        </div>
        <div className="status-grid">
          <StatusCard name="Backend" description="FastAPI application" status={status.backend} />
          <StatusCard name="PostgreSQL" description="Persistent database" status={status.postgresql} />
          <StatusCard name="Redis" description="Transient infrastructure" status={status.redis} />
        </div>
      </section>
    </main>
  );
}
