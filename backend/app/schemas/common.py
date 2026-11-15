"""
Common reusable schemas including base configuration, pagination, and error envelopes.
"""
from datetime import datetime
from typing import Annotated, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

T = TypeVar("T")

# Self-contained email string validator compliant with RFC 5322 pattern and max_length 255
EmailStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        max_length=255,
    ),
]


class BaseSchema(BaseModel):
    """Base schema configuring ORM attribute extraction for Pydantic v2."""
    model_config = ConfigDict(from_attributes=True)


class PaginationMetadata(BaseModel):
    """Standardized metadata envelope for paginated collection responses."""
    page: int = Field(..., ge=1, description="1-based page index")
    size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total count of matching records")
    total_pages: int = Field(..., ge=0, description="Total number of available pages")
    has_next: bool = Field(..., description="Whether a subsequent page exists")
    has_prev: bool = Field(..., description="Whether a previous page exists")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard generic envelope for paginated collection responses."""
    items: List[T] = Field(..., description="Page items array")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")


class ErrorDetail(BaseModel):
    """Field-level error descriptor."""
    field: Optional[str] = Field(None, description="Affected field name if applicable")
    issue: str = Field(..., description="Description of the error condition")


class ErrorBody(BaseModel):
    """Structured error payload body."""
    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable explanation of error")
    details: Optional[List[ErrorDetail]] = Field(None, description="Granular validation issues")
    timestamp: datetime = Field(..., description="Timestamp when error occurred")
    request_id: Optional[str] = Field(None, description="Correlation identifier")


class ErrorResponse(BaseModel):
    """Standardized error envelope matching Section 1.3 of API design."""
    error: ErrorBody


class MessageResponse(BaseModel):
    """Generic operational confirmation response."""
    message: str = Field(..., description="Status or acknowledgement message")
