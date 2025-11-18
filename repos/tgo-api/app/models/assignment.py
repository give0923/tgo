"""Visitor assignment model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssignmentType(str, Enum):
    """Assignment type enumeration."""
    
    ASSIGN = "assign"
    REASSIGN = "reassign"
    UNASSIGN = "unassign"
    AUTO_ASSIGN = "auto_assign"


class VisitorAssignment(Base):
    """Visitor assignment model for tracking visitor-to-staff assignments."""

    __tablename__ = "api_visitor_assignments"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign keys
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Associated project ID for multi-tenant isolation"
    )
    visitor_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_visitors.id", ondelete="CASCADE"),
        nullable=False,
        comment="Assigned visitor"
    )
    assigned_staff_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("api_staff.id"),
        nullable=True,
        comment="Currently assigned staff member"
    )
    previous_staff_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("api_staff.id"),
        nullable=True,
        comment="Previously assigned staff member"
    )
    assigned_by_staff_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("api_staff.id"),
        nullable=True,
        comment="Staff member who made the assignment"
    )

    # Basic fields
    assignment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type of assignment: assign, reassign, unassign, auto_assign"
    )
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
        comment="When assignment was made"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Assignment notes"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
        comment="Creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="visitor_assignments",
        lazy="select"
    )
    
    visitor: Mapped["Visitor"] = relationship(
        "Visitor",
        back_populates="assignments",
        lazy="select"
    )
    
    assigned_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys=[assigned_staff_id],
        back_populates="assigned_visitors",
        lazy="select"
    )
    
    previous_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys=[previous_staff_id],
        back_populates="previous_assignments",
        lazy="select"
    )
    
    assigned_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys=[assigned_by_staff_id],
        back_populates="created_assignments",
        lazy="select"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            assignment_type.in_([
                "assign",
                "reassign",
                "unassign",
                "auto_assign"
            ]),
            name="chk_api_visitor_assignments_type"
        ),
    )

    def __repr__(self) -> str:
        """String representation of the assignment."""
        return (
            f"<VisitorAssignment(id={self.id}, "
            f"visitor_id={self.visitor_id}, "
            f"type='{self.assignment_type}')>"
        )

    @property
    def is_active_assignment(self) -> bool:
        """Check if this is an active assignment (not unassign)."""
        return self.assignment_type != AssignmentType.UNASSIGN
