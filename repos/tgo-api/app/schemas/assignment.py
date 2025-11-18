"""Assignment schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.assignment import AssignmentType
from app.schemas.base import BaseSchema, PaginatedResponse, TimestampMixin


class AssignmentBase(BaseSchema):
    """Base assignment schema."""
    
    visitor_id: UUID = Field(..., description="Visitor to assign")
    assigned_staff_id: Optional[UUID] = Field(
        None,
        description="Staff member to assign (null for unassign)"
    )
    previous_staff_id: Optional[UUID] = Field(
        None,
        description="Previously assigned staff member (for reassign)"
    )
    assigned_by_staff_id: Optional[UUID] = Field(
        None,
        description="Staff member making the assignment"
    )
    assignment_type: AssignmentType = Field(
        ...,
        description="Type of assignment operation"
    )
    notes: Optional[str] = Field(
        None,
        description="Assignment notes"
    )


class AssignmentCreate(AssignmentBase):
    """Schema for creating an assignment."""
    pass


class AssignmentUpdate(BaseSchema):
    """Schema for updating an assignment."""
    
    notes: Optional[str] = Field(
        None,
        description="Updated assignment notes"
    )


class AssignmentInDB(AssignmentBase, TimestampMixin):
    """Schema for assignment in database."""
    
    id: UUID = Field(..., description="Assignment ID")
    project_id: UUID = Field(..., description="Associated project ID")
    timestamp: datetime = Field(..., description="When assignment was made")


class AssignmentResponse(AssignmentInDB):
    """Schema for assignment response."""
    pass


class AssignmentListParams(BaseSchema):
    """Parameters for listing assignments."""
    
    visitor_id: Optional[UUID] = Field(
        None,
        description="Filter assignments by visitor ID"
    )
    assigned_staff_id: Optional[UUID] = Field(
        None,
        description="Filter assignments by currently assigned staff member"
    )
    assignment_type: Optional[AssignmentType] = Field(
        None,
        description="Filter assignments by assignment type"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of assignments to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of assignments to skip"
    )


class AssignmentListResponse(PaginatedResponse):
    """Schema for assignment list response."""
    
    data: list[AssignmentResponse] = Field(..., description="List of assignments")
