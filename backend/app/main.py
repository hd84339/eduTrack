import logging
from typing import Any, Dict
from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db

logger = logging.getLogger("edutrack")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Centralized Multi-Center Student Learning & Activity Management Platform API",
    docs_url="/docs" if settings.DEBUG or settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.DEBUG or settings.APP_ENV != "production" else None,
)


@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Application liveness check",
    response_model=Dict[str, Any],
)
def health_check() -> Dict[str, Any]:
    """
    Basic application liveness endpoint confirming the API server is operational.
    """
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@app.get(
    "/health/db",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Database connectivity check",
    response_model=Dict[str, Any],
)
def database_health_check(db: Session = Depends(get_db)) -> Any:
    """
    Database readiness check executing a lightweight 'SELECT 1' query.
    Returns 200 OK when database is accessible.
    Returns 503 Service Unavailable on connection failure without exposing credentials or internal tracebacks.
    """
    try:
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            return {
                "status": "ok",
                "database": "connected",
            }
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "unexpected_result",
            },
        )
    except Exception as exc:
        logger.error("Database health probe failed: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "unavailable",
            },
        )

