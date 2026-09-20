from collections.abc import Generator

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def demo_employee(x_demo_role: str = Header(default="EMPLOYEE", alias="X-Demo-Role")) -> str:
    if x_demo_role.upper() != "EMPLOYEE":
        raise HTTPException(403, detail="Employee role required")
    return "employee-demo"


def demo_reviewer(x_demo_role: str = Header(default="REVIEWER", alias="X-Demo-Role"),
                  x_demo_user: str = Header(default="reviewer-demo", alias="X-Demo-User")) -> str:
    if x_demo_role.upper() != "REVIEWER":
        raise HTTPException(403, detail="Reviewer role required")
    return x_demo_user.strip() or "reviewer-demo"
