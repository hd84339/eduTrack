"""
Student Enrollment & Transfers API Router.
Implements transfer requests, listings, and review decisions per API_DESIGN.md Module 4.
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import require_center_manager
from app.db.session import get_db
from app.models.enums import TransferStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMetadata
from app.schemas.transfer import (
    TransferRequestCreate,
    TransferResponse,
    TransferReviewRequest,
    TransferReviewResponse,
)
from app.services import transfer_service
from app.services.transfer_service import (
    DestinationCapacityExceededError,
    TransferNotFoundError,
    TransferValidationError,
    serialize_transfer_response,
)

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post(
    "",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate student transfer request",
)
def create_transfer(
    payload: TransferRequestCreate,
    request: Request,
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> TransferResponse:
    """Initiates an inter-center transfer request for a student."""
    client_ip = request.client.host if request.client else None
    try:
        transfer = transfer_service.create_transfer_request(
            db=db,
            payload=payload,
            current_user=current_user,
            client_ip=client_ip,
        )
        return serialize_transfer_response(transfer)
    except TransferValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=PaginatedResponse[TransferResponse],
    status_code=status.HTTP_200_OK,
    summary="List student transfer requests",
)
def list_transfers(
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
    status_filter: Optional[TransferStatus] = Query(None, alias="status"),
    direction: Optional[str] = Query(None, description="'incoming' or 'outgoing'"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[TransferResponse]:
    """Lists transfer requests filterable by status and direction."""
    transfers, total_items = transfer_service.list_transfers(
        db=db,
        current_user=current_user,
        status=status_filter,
        direction=direction,
        page=page,
        size=size,
    )
    total_pages = math.ceil(total_items / size) if total_items > 0 else 0
    return PaginatedResponse(
        items=[serialize_transfer_response(t) for t in transfers],
        pagination=PaginationMetadata(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1 and total_pages > 0,
        ),
    )


@router.post(
    "/{transfer_id}/review",
    response_model=TransferReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve or reject a pending transfer request",
)
def review_transfer(
    transfer_id: UUID,
    payload: TransferReviewRequest,
    request: Request,
    current_user: User = Depends(require_center_manager),
    db: Session = Depends(get_db),
) -> TransferReviewResponse:
    """Approves or rejects a pending transfer within an atomic transaction."""
    client_ip = request.client.host if request.client else None
    try:
        return transfer_service.review_transfer_request(
            db=db,
            transfer_id=transfer_id,
            payload=payload,
            current_user=current_user,
            client_ip=client_ip,
        )
    except TransferNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except DestinationCapacityExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except TransferValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

