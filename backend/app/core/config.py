from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PolicyFlow AI"
    app_env: str = "local"

    database_url: str
    redis_url: str

    cors_origins: str = "http://localhost:5173"
    trusted_hosts: str = "localhost,127.0.0.1,testserver"
    enable_api_docs: bool = True
    log_level: str = "INFO"
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=5, ge=0, le=50)
    database_pool_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60)
    database_connect_timeout_seconds: int = Field(default=5, ge=1, le=60)
    redis_connect_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    redis_socket_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    policy_admin_token: str | None = None
    embedding_model: str = "jinaai/jina-embeddings-v2-small-en"
    embedding_dimension: int = 512
    rerank_provider: str = "cohere"
    cohere_api_key: str | None = None
    cohere_rerank_model: str = "rerank-v4.0-pro"
    bge_rerank_model: str = "BAAI/bge-reranker-base"
    rrf_k: int = 60
    retrieval_top_n: int = 20
    rerank_top_k: int = 5
    rerank_fallback_to_rrf: bool = True
    citation_required: bool = True
    citation_excerpt_chars: int = 600
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_primary_model: str | None = None
    openai_fallback_model: str | None = None
    policy_qa_model: str | None = None
    expense_rule_model: str | None = None
    exception_summary_model: str | None = None
    model_timeout_seconds: float = 30.0
    model_max_retries: int = 2
    model_retry_base_delay_ms: int = 250
    model_validation_retries: int = 1
    max_output_tokens: int = 1000
    policy_qa_max_input_tokens: int = 8000
    policy_qa_max_output_tokens: int = 1000
    expense_rule_max_input_tokens: int = 8000
    expense_rule_max_output_tokens: int = 1200
    exception_summary_max_input_tokens: int = 5000
    exception_summary_max_output_tokens: int = 600
    thread_token_budget: int = 12000
    thread_budget_ttl_seconds: int = 3600
    model_context_max_chunks: int = 5
    model_context_max_chars: int = 24000
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "policyflow-ai-local"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    enable_ai_evaluation: bool = False
    evaluation_dataset_path: str = "evaluation/datasets"
    evaluation_report_path: str = "evaluation/reports"
    evaluation_precision_at_5_threshold: float = Field(default=0.80, ge=0, le=1)
    evaluation_recall_at_10_threshold: float = Field(default=0.90, ge=0, le=1)
    evaluation_citation_correctness_threshold: float = Field(default=0.95, ge=0, le=1)
    evaluation_decision_accuracy_threshold: float = Field(default=1.0, ge=0, le=1)

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        case_sensitive=False,
        extra="ignore",
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]


settings = Settings()
