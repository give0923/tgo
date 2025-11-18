"""Tool query API endpoints (read-only)."""

import uuid
from datetime import datetime, timezone

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tool import Tool, ToolType
from app.schemas.tool import ToolResponse, ToolCreate, ToolUpdate


# Define router with prefix and tags as requested
router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=List[ToolResponse])
async def list_tools(
    project_id: uuid.UUID = Query(..., description="Project ID"),
    tool_type: Optional[ToolType] = Query(None, description="Filter by tool type"),
    include_deleted: bool = Query(False, description="Include soft-deleted tools"),
    db: AsyncSession = Depends(get_db),
) -> List[ToolResponse]:
    """List tools for the specified project with optional filters."""
    stmt = select(Tool).where(Tool.project_id == project_id)

    if not include_deleted:
        stmt = stmt.where(Tool.deleted_at.is_(None))

    if tool_type is not None:
        stmt = stmt.where(Tool.tool_type == tool_type)

    result = await db.execute(stmt)
    tools = result.scalars().all()
    return [ToolResponse.model_validate(tool) for tool in tools]


@router.post("", response_model=ToolResponse)
async def create_tool(
    tool_in: ToolCreate,
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """Create a new tool for the specified project."""
    tool = Tool(
        project_id=tool_in.project_id,
        name=tool_in.name,
        description=tool_in.description,
        tool_type=tool_in.tool_type,
        transport_type=tool_in.transport_type,
        endpoint=tool_in.endpoint,
        config=tool_in.config,
    )

    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    return ToolResponse.model_validate(tool)


@router.patch("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: uuid.UUID,
    tool_in: ToolUpdate,
    project_id: uuid.UUID = Query(..., description="Project ID"),
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """Update an existing tool for the specified project."""
    stmt = select(Tool).where(
        Tool.id == tool_id,
        Tool.project_id == project_id,
        Tool.deleted_at.is_(None),
    )

    result = await db.execute(stmt)
    tool = result.scalar_one_or_none()

    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    update_data = tool_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)

    await db.commit()
    await db.refresh(tool)

    return ToolResponse.model_validate(tool)



@router.delete("/{tool_id}", response_model=ToolResponse)
async def delete_tool(
    tool_id: uuid.UUID,
    project_id: uuid.UUID = Query(..., description="Project ID"),
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """Soft-delete a tool by setting its deleted_at timestamp."""
    stmt = select(Tool).where(
        Tool.id == tool_id,
        Tool.project_id == project_id,
        Tool.deleted_at.is_(None),
    )

    result = await db.execute(stmt)
    tool = result.scalar_one_or_none()

    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(tool)

    return ToolResponse.model_validate(tool)

