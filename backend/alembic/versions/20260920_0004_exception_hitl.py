"""Add authoritative exception review and audit records."""
from alembic import op

revision = "20260920_0004"
down_revision = "20260917_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE app.exception_request (
      id uuid PRIMARY KEY, expense_id uuid NOT NULL UNIQUE REFERENCES app.expense(id),
      assessment_id uuid NOT NULL UNIQUE REFERENCES app.assessment(id), thread_id text NOT NULL UNIQUE,
      justification text NOT NULL, information_history jsonb NOT NULL DEFAULT '[]'::jsonb,
      variance_amount numeric(12,2), status text NOT NULL,
      summary_status text NOT NULL DEFAULT 'PENDING', summary_json jsonb,
      resume_status text NOT NULL DEFAULT 'NOT_REQUIRED', created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT ck_exception_status CHECK (status IN ('PENDING_REVIEW','MORE_INFORMATION_REQUIRED','APPROVED','REJECTED')),
      CONSTRAINT ck_exception_summary_status CHECK (summary_status IN ('PENDING','AVAILABLE','UNAVAILABLE'))
    )""")
    op.execute("CREATE INDEX ix_exception_status_created ON app.exception_request(status, created_at)")
    op.execute("""
    CREATE TABLE app.review (
      id uuid PRIMARY KEY, exception_id uuid NOT NULL REFERENCES app.exception_request(id),
      reviewer_id text NOT NULL, decision text NOT NULL, comments text NOT NULL,
      reviewed_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT ck_review_decision CHECK (decision IN ('APPROVE','REJECT','REQUEST_MORE_INFORMATION'))
    )""")
    op.execute("CREATE UNIQUE INDEX uq_review_final ON app.review(exception_id) WHERE decision IN ('APPROVE','REJECT')")
    op.execute("""
    CREATE TABLE app.audit_event (
      id uuid PRIMARY KEY, event_type text NOT NULL, request_id text, thread_id text,
      expense_id uuid, exception_id uuid, review_id uuid, actor_id text,
      metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
    )""")
    op.execute("CREATE INDEX ix_audit_exception_created ON app.audit_event(exception_id, created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE app.audit_event")
    op.execute("DROP TABLE app.review")
    op.execute("DROP TABLE app.exception_request")
