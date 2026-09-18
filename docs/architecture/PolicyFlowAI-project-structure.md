PolicyFlow-AI/
│
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
├── pyproject.toml
│
├── openspec/
│   ├── project.md
│   ├── specs/
│   │   ├── expense-compliance/
│   │   ├── policy-rag/
│   │   ├── exception-review/
│   │   └── model-governance/
│   │
│   └── changes/
│       ├── 001-platform-foundation/
│       ├── 002-policy-ingestion-and-hybrid-rag/
│       ├── 003-policy-qa/
│       ├── 004-expense-compliance-assessment/
│       ├── 005-exception-hitl/
│       ├── 006-model-gateway-guardrails/
│       ├── 007-observability-evaluation/
│       └── 008-aws-deployment-hardening/
│
├── docs/
│   ├── requirements/
│   │   └── PolicyFlow_AI_FRD_v1.0.docx
│   │
│   ├── architecture/
│   │   ├── PolicyFlow_AI_HLD_v1.0.docx
│   │   ├── PolicyFlow_AI_LLD_v1.0.docx
│   │   ├── architecture.md
│   │   └── sequence-diagram.md
│   │
│   └── adr/
│       ├── ADR-001-langgraph.md
│       ├── ADR-002-postgresql-pgvector.md
│       ├── ADR-003-hybrid-rag.md
│       ├── ADR-004-model-gateway.md
│       └── ADR-005-hitl.md
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       │
│       ├── api/
│       │   ├── client.ts
│       │   ├── expenseApi.ts
│       │   ├── policyApi.ts
│       │   └── reviewApi.ts
│       │
│       ├── components/
│       │   ├── ExpenseForm.tsx
│       │   ├── PolicyQuestion.tsx
│       │   ├── DecisionCard.tsx
│       │   ├── CitationPanel.tsx
│       │   ├── ExceptionForm.tsx
│       │   └── ReviewPanel.tsx
│       │
│       ├── pages/
│       │   ├── HomePage.tsx
│       │   ├── ExpenseAssessmentPage.tsx
│       │   ├── PolicyQApage.tsx
│       │   └── ReviewerPage.tsx
│       │
│       ├── hooks/
│       ├── types/
│       └── utils/
│
├── backend/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── requirements.txt
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── api/
│       │   ├── dependencies.py
│       │   └── routes/
│       │       ├── health.py
│       │       ├── expenses.py
│       │       ├── policies.py
│       │       ├── reviews.py
│       │       └── workflows.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── logging.py
│       │   ├── exceptions.py
│       │   └── constants.py
│       │
│       ├── schemas/
│       │   ├── expense.py
│       │   ├── policy.py
│       │   ├── review.py
│       │   ├── workflow.py
│       │   └── model_output.py
│       │
│       ├── models/
│       │   ├── expense.py
│       │   ├── assessment.py
│       │   ├── exception_request.py
│       │   ├── review.py
│       │   ├── policy_document.py
│       │   ├── policy_chunk.py
│       │   └── audit_event.py
│       │
│       ├── repositories/
│       │   ├── expense_repository.py
│       │   ├── review_repository.py
│       │   ├── policy_repository.py
│       │   └── audit_repository.py
│       │
│       ├── services/
│       │   ├── expense_service.py
│       │   ├── policy_service.py
│       │   ├── exception_service.py
│       │   └── audit_service.py
│       │
│       ├── graph/
│       │   ├── state.py
│       │   ├── graph.py
│       │   ├── routing.py
│       │   ├── checkpointer.py
│       │   │
│       │   └── nodes/
│       │       ├── validate_request.py
│       │       ├── detect_missing_fields.py
│       │       ├── build_filters.py
│       │       ├── retrieve_policy.py
│       │       ├── rerank_policy.py
│       │       ├── extract_policy_rule.py
│       │       ├── evaluate_expense.py
│       │       ├── validate_citations.py
│       │       ├── collect_exception.py
│       │       ├── human_review.py
│       │       ├── finalize_decision.py
│       │       └── audit_event.py
│       │
│       ├── rag/
│       │   ├── ingestion/
│       │   │   ├── loader.py
│       │   │   ├── chunker.py
│       │   │   └── metadata.py
│       │   │
│       │   ├── embeddings/
│       │   │   └── embedding_provider.py
│       │   │
│       │   ├── retrieval/
│       │   │   ├── lexical_retriever.py
│       │   │   ├── vector_retriever.py
│       │   │   ├── hybrid_retriever.py
│       │   │   └── rrf.py
│       │   │
│       │   ├── reranking/
│       │   │   ├── base.py
│       │   │   ├── cohere_reranker.py
│       │   │   └── bge_reranker.py
│       │   │
│       │   └── citations/
│       │       └── validator.py
│       │
│       ├── gateway/
│       │   ├── model_gateway.py
│       │   ├── routing.py
│       │   ├── token_control.py
│       │   ├── retry.py
│       │   │
│       │   └── providers/
│       │       ├── base.py
│       │       └── openai_provider.py
│       │
│       ├── guardrails/
│       │   ├── input_guard.py
│       │   ├── output_guard.py
│       │   └── policy_guard.py
│       │
│       ├── cache/
│       │   └── redis_client.py
│       │
│       ├── observability/
│       │   ├── tracing.py
│       │   ├── metrics.py
│       │   └── langwatch.py
│       │
│       └── db/
│           ├── session.py
│           ├── base.py
│           └── postgres.py
│
├── policies/
│   ├── raw/
│   │   ├── travel_expense_policy.md
│   │   ├── hotel_policy.md
│   │   ├── meal_policy.md
│   │   ├── transportation_policy.md
│   │   ├── receipt_policy.md
│   │   └── exception_policy.md
│   │
│   └── processed/
│
├── evaluation/
│   ├── datasets/
│   │   ├── policy_qa_golden.json
│   │   └── expense_cases.json
│   │
│   ├── ragas/
│   │   └── evaluate_rag.py
│   │
│   ├── deepeval/
│   │   └── evaluate_agent.py
│   │
│   └── reports/
│
├── tests/
│   ├── unit/
│   │   ├── test_rrf.py
│   │   ├── test_expense_rules.py
│   │   └── test_citation_validator.py
│   │
│   ├── integration/
│   │   ├── test_hybrid_retrieval.py
│   │   ├── test_model_gateway.py
│   │   └── test_checkpoint_resume.py
│   │
│   └── e2e/
│       ├── test_compliant_expense.py
│       └── test_exception_hitl.py
│
├── infrastructure/
│   ├── aws/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── redis/
│   │   ├── alb/
│   │   └── secrets/
│   │
│   └── cloudflare/
│
├── scripts/
│   ├── bootstrap.ps1
│   ├── bootstrap.sh
│   ├── ingest_policies.py
│   ├── seed_data.py
│   └── run_evaluation.py
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── rag-evaluation.yml
        └── deploy-aws.yml