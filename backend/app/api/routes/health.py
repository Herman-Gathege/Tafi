"""Liveness/readiness probe used by Docker Compose and the deployment."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.redis import get_redis
from app.db.session import get_db

router = APIRouter(tags=["health"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/health")
def health(db: DbSession) -> JSONResponse:
    """Return 200 only when both PostgreSQL and Redis answer."""
    database = "ok"
    redis_status = "ok"

    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any failure means "not ready"
        database = "error"

    try:
        get_redis().ping()
    except Exception:  # noqa: BLE001
        redis_status = "error"

    healthy = database == "ok" and redis_status == "ok"
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "error",
            "database": database,
            "redis": redis_status,
        },
    )
