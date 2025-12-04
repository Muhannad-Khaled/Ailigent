"""Common Pydantic Models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    error: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Success response model."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class DateRange(BaseModel):
    """Date range filter."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class EmployeeBasic(BaseModel):
    """Basic employee information."""

    id: int
    name: str
    email: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    job_title: Optional[str] = None


class DepartmentBasic(BaseModel):
    """Basic department information."""

    id: int
    name: str
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    employee_count: int = 0
