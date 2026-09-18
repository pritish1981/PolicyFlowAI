"""Create authoritative expense assessment storage and checkpoint schema."""

from alembic import op

revision = "20260917_0003"
down_revision = "20260913_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS checkpoint")
    op.execute("""
    CREATE TABLE app.expense (
      id uuid PRIMARY KEY,
      employee_id uuid,
      thread_id text NOT NULL UNIQUE,
      request_id text NOT NULL,
      expense_type text,
      amount numeric(12,2),
      currency text,
      location text,
      travel_type text,
      purpose text,
      receipt_available boolean,
      status text NOT NULL,
      version integer NOT NULL DEFAULT 1,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )
    """)
    op.execute("""
    CREATE TABLE app.assessment (
      id uuid PRIMARY KEY,
      expense_id uuid NOT NULL UNIQUE REFERENCES app.expense(id),
      decision text NOT NULL,
      policy_rule_json jsonb NOT NULL DEFAULT '{}'::jsonb,
      citations_json jsonb NOT NULL DEFAULT '[]'::jsonb,
      policy_limit numeric(12,2),
      confidence numeric(5,4) NOT NULL,
      explanation text NOT NULL,
      next_action text NOT NULL,
      model_name text,
      prompt_version text,
      created_at timestamptz NOT NULL DEFAULT now()
    )
    """)
    op.execute("""
    CREATE TABLE app.expense_idempotency (
      idempotency_key text PRIMARY KEY,
      request_hash char(64) NOT NULL,
      expense_id uuid NOT NULL UNIQUE REFERENCES app.expense(id),
      created_at timestamptz NOT NULL DEFAULT now()
    )
    """)
    op.execute("CREATE INDEX ix_expense_status ON app.expense (status, created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE app.expense_idempotency")
    op.execute("DROP TABLE app.assessment")
    op.execute("DROP TABLE app.expense")
    op.execute("DROP SCHEMA checkpoint CASCADE")
