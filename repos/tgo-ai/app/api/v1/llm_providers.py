"""LLM Provider sync API for tgo-api -> tgo-ai."""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status

from app.api.responses import build_error_responses
from app.schemas.llm_provider import (
    LLMProviderResponse,
    LLMProviderSyncRequest,
    LLMProviderSyncResponse,
)
from app.services.llm_provider_service import LLMProviderService
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


def get_llm_provider_service(db: AsyncSession = Depends(get_db)) -> LLMProviderService:
    return LLMProviderService(db)


@router.post(
    "/sync",
    response_model=LLMProviderSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk upsert LLM Providers",
    description="Upsert LLM Providers. Each item must include id and project_id; if a provider (project_id, alias) exists it will be updated, otherwise created. The id is provided by tgo-api.",
    responses=build_error_responses([400]),
)
async def sync_llm_providers(
    request: LLMProviderSyncRequest,
    service: LLMProviderService = Depends(get_llm_provider_service),
) -> LLMProviderSyncResponse:
    providers = await service.sync_providers(
        [p.model_dump() for p in request.providers],
    )
    return LLMProviderSyncResponse(data=[LLMProviderResponse.from_orm_model(p) for p in providers])

