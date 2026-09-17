from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PolicyFlow AI"
    app_env: str = "local"

    database_url: str
    redis_url: str

    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
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
    model_timeout_seconds: float = 30.0
    model_max_retries: int = 2
    max_output_tokens: int = 1000
    thread_token_budget: int = 12000

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        case_sensitive=False,
        extra="ignore",
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
