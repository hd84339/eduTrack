import logging
from typing import Any, Dict
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.activities import router as activities_router
from app.api.analytics import router as analytics_router
from app.api.attendance import router as attendance_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.centers import router as centers_router
from app.api.competencies import router as competencies_router
from app.api.progress import router as progress_router
from app.api.reports import router as reports_router
from app.api.sessions import router as sessions_router
from app.api.students import router as students_router
from app.api.transfers import router as transfers_router
from app.api.users import router as users_router
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

# CORS Middleware for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all domain API routers under /api/v1
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(centers_router, prefix=settings.API_V1_PREFIX)
app.include_router(students_router, prefix=settings.API_V1_PREFIX)
app.include_router(transfers_router, prefix=settings.API_V1_PREFIX)
app.include_router(attendance_router, prefix=settings.API_V1_PREFIX)
app.include_router(competencies_router, prefix=settings.API_V1_PREFIX)
app.include_router(activities_router, prefix=settings.API_V1_PREFIX)
app.include_router(sessions_router, prefix=settings.API_V1_PREFIX)
app.include_router(progress_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_logs_router, prefix=settings.API_V1_PREFIX)


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
