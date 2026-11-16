"""
Authentication and User Session API routes.
Implements POST /auth/login, POST /auth/refresh, and GET /auth/me per API_DESIGN.md Module 1.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    TokenTypeMismatchError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.session import get_db
from app.models.enums import UserStatus
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    TokenRefreshResponse,
    TokenResponse,
    UserCenterSummary,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def serialize_user_response(user: User) -> UserResponse:
    """Safely converts User ORM instance into UserResponse, resolving assigned center summaries."""
    assigned_centers_list = []
    if hasattr(user, "assigned_centers") and user.assigned_centers:
        for uc in user.assigned_centers:
            if hasattr(uc, "center") and uc.center:
                assigned_centers_list.append(
                    UserCenterSummary(
                        id=uc.center.id,
                        code=uc.center.code,
                        name=uc.center.name,
                    )
                )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        assigned_centers=assigned_centers_list,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT token pair",
    description="Validates staff credentials and returns an access token and refresh token.",
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status == UserStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please contact your administrator.",
        )

    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=serialize_user_response(user),
    )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Rotate access token using a valid refresh token",
)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenRefreshResponse:
    try:
        payload = decode_token(refresh_data.refresh_token, expected_type="refresh")
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (TokenInvalidError, TokenTypeMismatchError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    access_token = create_access_token(subject=user.id)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenRefreshResponse(
        access_token=access_token,
        expires_in=expires_in,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get currently authenticated staff user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return serialize_user_response(current_user)

