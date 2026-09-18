Act as a Principal AI Systems Architect. Help me design 1 focused, portfolio-ready Proof-of-Concept (POC) AI Agent project that I can build in 15–20 days and deploy to AWS.

--- PROJECT GOAL & SCOPE BOUNDARIES ---
- Focus: Exactly 1 or 2 tight end-to-end scenarios so the architecture remains crisp and easy to draw/explain in interviews.
- Dev Timeline: 15–20 days max for a single engineer.
- Deployment Target: Containerized deployment on AWS behind Cloudflare.

--- MY FIXED TECH STACK ---
- Frontend: React + TypeScript
- Backend & Validation: Python 3.12 + FastAPI + Pydantic + OpenSpec
- Agent Orchestration: LangGraph (State Machine, persistence/checkpointing)
- Database Layer: PostgreSQL (Business state + separate LangGraph checkpoint store + pgvector for Hybrid RAG)
- Caching/Queueing: Redis (Locks, rate limits, transient coordination)
- Data Ingestion & RAG: Policy RAG (Deterministic metadata filtering, Hybrid Lexical+Vector retrieval, Cohere/BGE Reranking, Strict Citations)
- AI Gateway & LLMs: Central Model Gateway (Provider abstraction, OpenAI primary, token controls, guardrails, fallback routing)
- Observability: LangSmith + LangWatch (Tracing, step latency, evaluation metrics)
- Developer Tooling & DevOps: Docker Compose (Local), Alembic (Migrations), Pytest + Ragas/DeepEval (E2E & RAG Testing), GitHub Actions (CI/CD), Cloudflare (DNS/WAF/Zero Trust)

--- REQUIRED OUTPUT FORMAT ---
Please generate a single, highly structured system design document covering:

1. Project Title & Business Domain (e.g., Enterprise Policy Compliance Agent or Automated Claim Audit Assistant).
2. The 2 Bounded Scenarios: Walk through the exact step-by-step user interactions for both flows.
3. System Architecture & Schema Breakdown:
   - LangGraph State Machine: State schema (`TypedDict`), exact node definitions, conditional edge logic, and postgreSQL checkpointer integration.
   - Dual-Store PostgreSQL & pgvector Schema: Table structure for business entities vs. `pgvector` hybrid search tables (metadata indexing, chunking strategy).
   - Central AI Model Gateway & Guardrails: How OpenAI API calls are managed, validated with Pydantic, routed, and traced via LangSmith/LangWatch.
4. Interview Sequence Diagram Narrative: A numbered, 8-to-10 step trace of a request (React UI -> Cloudflare -> FastAPI -> LangGraph -> pgvector/OpenAI -> Ragas Eval -> React Response) so I can easily draw it on a whiteboard.
5. 20-Day Sourced Development & AWS Cloud Roadmap:
   - Sprints 1–4 (5 days each): From OpenSpec/Alembic setup to LangGraph implementation, pgvector ingestion, RAG evals, and AWS deployment.
6. 3-Minute Interview Talking Points: How to explain the trade-offs of using pgvector over standalone vector DBs, state separation, and observability choices to a hiring panel.
