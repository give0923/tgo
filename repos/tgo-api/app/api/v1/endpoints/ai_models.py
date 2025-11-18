"""AI Model catalog CRUD endpoints (global, not project-scoped)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.common_responses import CREATE_RESPONSES, CRUD_RESPONSES, DELETE_RESPONSES, LIST_RESPONSES, UPDATE_RESPONSES
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.models import AIModel, Staff
from app.schemas import (
    AIModelCreate,
    AIModelListParams,
    AIModelListResponse,
    AIModelResponse,
    AIModelUpdate,
)

logger = get_logger("endpoints.ai_models")
router = APIRouter()


def _to_response(item: AIModel) -> AIModelResponse:
    return AIModelResponse.model_validate({
        "id": item.id,
        "provider": item.provider,
        "model_id": item.model_id,
        "model_name": item.model_name,
        "model_type": item.model_type,
        "description": item.description,
        "capabilities": item.capabilities,
        "context_window": item.context_window,
        "max_tokens": item.max_tokens,
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "deleted_at": item.deleted_at,
    })


@router.get("", response_model=AIModelListResponse, responses=LIST_RESPONSES)
async def list_ai_models(
    provider: Optional[str] = Query(None),
    model_type: Optional[str] = Query(None, pattern="^(chat|embedding)$"),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AIModelListResponse:
    """List models with pagination and optional filtering/search."""
    query = db.query(AIModel).filter(AIModel.deleted_at.is_(None))

    if provider:
        query = query.filter(AIModel.provider == provider)
    if model_type:
        query = query.filter(AIModel.model_type == model_type)
    if is_active is not None:
        query = query.filter(AIModel.is_active == is_active)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(AIModel.model_id.ilike(like), AIModel.model_name.ilike(like)))

    total = query.count()
    items = (
        query.order_by(AIModel.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    data = [_to_response(x) for x in items]
    return AIModelListResponse(
        data=data,
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_prev": offset > 0,
        },
    )


@router.get("/{model_id}", response_model=AIModelResponse, responses=CRUD_RESPONSES)
async def get_ai_model(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AIModelResponse:
    item = db.query(AIModel).filter(AIModel.id == model_id, AIModel.deleted_at.is_(None)).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI model not found")
    return _to_response(item)


@router.post("", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED, responses=CREATE_RESPONSES)
async def create_ai_model(
    payload: AIModelCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AIModelResponse:
    exists = (
        db.query(AIModel)
        .filter(AIModel.provider == payload.provider, AIModel.model_id == payload.model_id, AIModel.deleted_at.is_(None))
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model already exists for this provider")

    item = AIModel(
        provider=payload.provider,
        model_id=payload.model_id,
        model_name=payload.model_name,
        model_type=payload.model_type,
        description=payload.description,
        capabilities=payload.capabilities,
        context_window=payload.context_window,
        max_tokens=payload.max_tokens,
        is_active=payload.is_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.patch("/{model_id}", response_model=AIModelResponse, responses=UPDATE_RESPONSES)
async def update_ai_model(
    model_id: UUID,
    payload: AIModelUpdate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AIModelResponse:
    item = db.query(AIModel).filter(AIModel.id == model_id, AIModel.deleted_at.is_(None)).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI model not found")

    data = payload.model_dump(exclude_unset=True)

    # Enforce uniqueness on (provider, model_id) if either changes
    new_provider = data.get("provider", item.provider)
    new_model_id = data.get("model_id", item.model_id)
    if new_provider != item.provider or new_model_id != item.model_id:
        dup = (
            db.query(AIModel)
            .filter(
                AIModel.provider == new_provider,
                AIModel.model_id == new_model_id,
                AIModel.deleted_at.is_(None),
                AIModel.id != item.id,
            )
            .first()
        )
        if dup:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model already exists for this provider")

    for field, value in data.items():
        setattr(item, field, value)
    item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT, responses=DELETE_RESPONSES)
async def delete_ai_model(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> None:
    item = db.query(AIModel).filter(AIModel.id == model_id, AIModel.deleted_at.is_(None)).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI model not found")

    item.deleted_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()
    db.commit()
    return None
