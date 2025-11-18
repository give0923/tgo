"""Manual service request model."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.visitor import Visitor


class ManualServiceRequest(Base):
    """Records requests for manual (human) customer service intervention."""

    __tablename__ = "api_manual_service_requests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Associated project ID for multi-tenant isolation",
    )
    visitor_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("api_visitors.id", ondelete="SET NULL"),
        nullable=True,
        comment="Visitor that triggered the manual service request",
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Reason for requesting manual assistance",
    )
    urgency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="normal",
        comment="Urgency level: low | normal | high | urgent",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Status of the manual service request: pending, notified, in_progress, resolved, rejected",
    )
    channel: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Preferred manual service channel (phone/wechat/email/ticket/etc.)",
    )
    notification_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Notification modality used to alert staff (e.g., sms, email, slack)",
    )
    channel_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Associated communication channel identifier",
    )
    channel_type: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Associated communication channel type code",
    )
    request_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional contextual metadata for the request",
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
        comment="Creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Soft deletion timestamp",
    )

    visitor: Mapped[Optional["Visitor"]] = relationship(
        "Visitor",
        back_populates="manual_service_requests",
        lazy="select",
    )

    __table_args__ = (
        CheckConstraint(
            "urgency IN ('low', 'normal', 'high', 'urgent')",
            name="chk_manual_service_requests_urgency",
        ),
        CheckConstraint(
            "status IN ('pending', 'notified', 'in_progress', 'resolved', 'rejected')",
            name="chk_manual_service_requests_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<ManualServiceRequest(id={self.id}, urgency='{self.urgency}')>"
