"""Tag schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.tag import TagCategory
from app.schemas.base import BaseSchema, PaginatedResponse, SoftDeleteMixin, TimestampMixin


class TagBase(BaseSchema):
    """Base tag schema."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Tag name"
    )
    category: TagCategory = Field(
        ...,
        description="Tag category"
    )
    weight: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Tag importance/priority weight (0-10)"
    )
    color: Optional[str] = Field(
        None,
        max_length=20,
        description="Tag color"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Tag description"
    )


class TagCreate(TagBase):
    """Schema for creating a tag."""
    pass


class TagUpdate(BaseSchema):
    """Schema for updating a tag."""
    
    weight: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Updated tag weight"
    )
    color: Optional[str] = Field(
        None,
        max_length=20,
        description="Updated tag color"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated tag description"
    )

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate color format (hex color)."""
        if v is None:
            return v
        if not v.startswith('#') or len(v) not in [4, 7]:
            raise ValueError('Color must be a valid hex color (e.g., #FF5733 or #F53)')
        return v


class TagInDB(TagBase, TimestampMixin, SoftDeleteMixin):
    """Schema for tag in database."""
    
    id: str = Field(..., description="Base64 encoded tag ID")
    project_id: UUID = Field(..., description="Associated project ID")


class TagResponse(TagInDB):
    """Schema for tag response."""
    pass


class TagListParams(BaseSchema):
    """Parameters for listing tags."""
    
    category: Optional[TagCategory] = Field(
        None,
        description="Filter tags by category"
    )
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Search tags by name"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of tags to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of tags to skip"
    )


class TagListResponse(PaginatedResponse):
    """Schema for tag list response."""
    
    data: list[TagResponse] = Field(..., description="List of tags")


class VisitorTagCreate(BaseSchema):
    """Schema for creating a visitor-tag relationship."""
    
    visitor_id: UUID = Field(..., description="Visitor ID")
    tag_id: str = Field(..., description="Tag ID (Base64 encoded)")


class VisitorTagResponse(BaseSchema):
    """Schema for visitor-tag relationship response."""

    id: UUID = Field(..., description="Visitor-tag relationship ID")
    project_id: UUID = Field(..., description="Associated project ID")
    visitor_id: UUID = Field(..., description="Associated visitor ID")
    tag_id: str = Field(..., description="Associated tag ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft deletion timestamp")
