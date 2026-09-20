from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.v1.admin import router as policy_admin_router
from app.api.routes.policies import router as policy_router
from app.api.routes.expenses import router as expense_router
from app.api.routes.reviews import router as review_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="PolicyFlow AI platform foundation",
)

app.include_router(health_router)
app.include_router(policy_admin_router)
app.include_router(policy_router)
app.include_router(expense_router)
app.include_router(review_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "running",
    }
