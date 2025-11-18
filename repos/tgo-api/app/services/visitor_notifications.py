"""Visitor update notification helpers."""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable
import uuid

from sqlalchemy.orm import Session

from app.models import ChannelMember, Visitor
from app.services.wukongim_client import wukongim_client
from app.utils.const import CHANNEL_TYPE_CUSTOMER_SERVICE, MEMBER_TYPE_STAFF
from app.utils.encoding import build_visitor_channel_id

logger = logging.getLogger("services.visitor_notifications")

PROFILE_UPDATED_EVENT = "visitor.profile.updated"


async def notify_visitor_profile_updated(db: Session, visitor: Visitor) -> None:
    """
    Notify all staff associated with the visitor's customer-service channel that the profile was updated.
    """
    channel_id = build_visitor_channel_id(visitor.id)


    payload = {
        "visitor_id": str(visitor.id),
        "channel_id": channel_id,
        "channel_type": CHANNEL_TYPE_CUSTOMER_SERVICE,
    }
    
    print("payload--->",payload)

    tasks = [
        wukongim_client.send_event(
            client_msg_no=f"profile-update-{uuid.uuid4().hex}",
            channel_id=channel_id,
            channel_type=CHANNEL_TYPE_CUSTOMER_SERVICE,
            event_type=PROFILE_UPDATED_EVENT,
            data=payload,
            force=False,
        )
    ]


    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.error(
                "Failed to dispatch visitor profile update notification",
                exc_info=result,
                extra={"visitor_id": str(visitor.id)},
            )
