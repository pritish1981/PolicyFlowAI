"""Create policy RAG documents, chunks and search indexes."""

from alembic import op

revision = "20260913_0002"
down_revision = "df20455da62e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
    CREATE TABLE rag.policy_document (
      id uuid PRIMARY KEY,
      policy_code text NOT NULL,
      title text NOT NULL,
      domain text NOT NULL,
      version text NOT NULL,
      region text NOT NULL,
      travel_type text NOT NULL,
      status text NOT NULL,
      effective_date date NOT NULL,
      expiry_date date,
      source_uri text NOT NULL,
      content_hash char(64) NOT NULL,
      embedding_model text NOT NULL,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (policy_code, version)
    )
    """)
    op.execute("""
    CREATE TABLE rag.policy_chunk (
      id uuid PRIMARY KEY,
      document_id uuid NOT NULL REFERENCES rag.policy_document(id) ON DELETE CASCADE,
      chunk_index integer NOT NULL,
      section_id text NOT NULL,
      section_title text NOT NULL,
      content text NOT NULL,
      token_count integer NOT NULL,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      embedding vector(512) NOT NULL,
      search_vector tsvector GENERATED ALWAYS AS
        (to_tsvector('english'::regconfig, content)) STORED,
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (document_id, chunk_index)
    )
    """)
    op.execute("CREATE INDEX ix_policy_chunk_fts ON rag.policy_chunk USING gin (search_vector)")
    op.execute("CREATE INDEX ix_policy_chunk_vector ON rag.policy_chunk USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX ix_policy_chunk_metadata ON rag.policy_chunk USING gin (metadata)")
    op.execute("CREATE INDEX ix_policy_document_status_domain ON rag.policy_document (status, domain)")
    op.execute("CREATE INDEX ix_policy_document_region_travel ON rag.policy_document (region, travel_type)")
    op.execute("CREATE INDEX ix_policy_document_dates ON rag.policy_document (effective_date, expiry_date)")
    op.execute("CREATE INDEX ix_policy_chunk_document ON rag.policy_chunk (document_id)")


def downgrade() -> None:
    op.execute("DROP TABLE rag.policy_chunk")
    op.execute("DROP TABLE rag.policy_document")
