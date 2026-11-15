"""
Central export for all EduTrack Pydantic v2 data transfer schemas.
"""
from app.schemas.common import (
    BaseSchema,
    PaginationMetadata,
    PaginatedResponse,
    ErrorDetail,
    ErrorBody,
    ErrorResponse,
    MessageResponse,
)
from app.schemas.user import (
    UserCenterSummary,
    UserBase,
    UserCreate,
    UserUpdate,
    UserCenterAssign,
    UserResponse,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    TokenRefreshResponse,
)
from app.schemas.center import (
    CenterBase,
    CenterCreate,
    CenterUpdate,
    CenterResponse,
    CenterDetailResponse,
    CenterSummary,
)
from app.schemas.student import (
    StudentBase,
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListItemResponse,
    StudentDetailResponse,
)
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
)
from app.schemas.transfer import (
    TransferRequestCreate,
    TransferReviewRequest,
    TransferResponse,
    TransferReviewResponse,
)
from app.schemas.attendance import (
    AttendanceItem,
    BulkAttendanceCreate,
    BulkAttendanceResponse,
    AttendanceCorrectionRequest,
    AttendanceRecordResponse,
    AttendanceAuditLogResponse,
)
from app.schemas.competency import (
    CompetencyCreate,
    CompetencyUpdate,
    CompetencyResponse,
    StudentSkillProgressResponse,
    StudentProgressOverviewResponse,
)
from app.schemas.activity import (
    ActivityCompetencyItem,
    ActivityCompetencyResponse,
    ActivityTemplateCreate,
    ActivityTemplateUpdate,
    ActivityTemplateResponse,
)
from app.schemas.session import (
    SessionStudentEvaluationItem,
    SessionStudentItem,
    SessionCreate,
    SessionStudentEvaluationResponse,
    SessionStudentResponse,
    SessionResponse,
)
from app.schemas.audit import (
    AuditLogCreate,
    AuditLogResponse,
)

__all__ = [
    # Common
    "BaseSchema",
    "PaginationMetadata",
    "PaginatedResponse",
    "ErrorDetail",
    "ErrorBody",
    "ErrorResponse",
    "MessageResponse",
    # User / Auth
    "UserCenterSummary",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserCenterAssign",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "TokenRefreshResponse",
    # Center
    "CenterBase",
    "CenterCreate",
    "CenterUpdate",
    "CenterResponse",
    "CenterDetailResponse",
    "CenterSummary",
    # Student
    "StudentBase",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentListItemResponse",
    "StudentDetailResponse",
    # Enrollment
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "EnrollmentResponse",
    # Transfer
    "TransferRequestCreate",
    "TransferReviewRequest",
    "TransferResponse",
    "TransferReviewResponse",
    # Attendance
    "AttendanceItem",
    "BulkAttendanceCreate",
    "BulkAttendanceResponse",
    "AttendanceCorrectionRequest",
    "AttendanceRecordResponse",
    "AttendanceAuditLogResponse",
    # Competency & Progress
    "CompetencyCreate",
    "CompetencyUpdate",
    "CompetencyResponse",
    "StudentSkillProgressResponse",
    "StudentProgressOverviewResponse",
    # Activity
    "ActivityCompetencyItem",
    "ActivityCompetencyResponse",
    "ActivityTemplateCreate",
    "ActivityTemplateUpdate",
    "ActivityTemplateResponse",
    # Session
    "SessionStudentEvaluationItem",
    "SessionStudentItem",
    "SessionCreate",
    "SessionStudentEvaluationResponse",
    "SessionStudentResponse",
    "SessionResponse",
    # Audit
    "AuditLogCreate",
    "AuditLogResponse",
]
