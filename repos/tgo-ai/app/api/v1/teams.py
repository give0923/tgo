"""Team management API endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_pagination_params, get_team_service
from app.schemas.base import PaginationMetadata
from app.api.responses import build_error_responses
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate, TeamWithDetails
from app.schemas.agent import AgentWithDetails
from app.services.team_service import TeamService

router = APIRouter()


@router.get(
    "",
    response_model=dict,
    responses=build_error_responses([]),
)
async def list_teams(
    is_default: Optional[bool] = Query(default=None, description="Filter by default team status"),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    project_id: uuid.UUID = Query(..., description="Project ID"),
    team_service: TeamService = Depends(get_team_service),
) -> dict:
    """
    List teams for the specified project with filtering and pagination.

    Project Scope:
    - Only teams belonging to the provided project_id are returned
    """
    limit, offset = pagination
    teams, total_count = await team_service.list_teams(
        project_id=project_id,
        is_default=is_default,
        limit=limit,
        offset=offset,
    )

    return {
        "data": [TeamResponse.model_validate(team) for team in teams],
        "pagination": PaginationMetadata(
            total=total_count,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total_count,
            has_prev=offset > 0,
        ),
    }


@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    responses=build_error_responses([400, 409], {409: "Team name conflict"}),
)
async def create_team(
    team_data: TeamCreate,
    project_id: uuid.UUID = Query(..., description="Project ID"),
    team_service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    """
    Create a new team for the specified project.

    Team Configuration:
    - Specify LLM model in "provider:model_name" format
    - Configure team instructions and expected output format
    - Set default team status (only one default per project)
    - Optionally set session identifier for team context
    """
    team = await team_service.create_team(project_id, team_data)
    return TeamResponse.model_validate(team)


@router.get(
    "/{team_id}",
    response_model=TeamWithDetails,
    responses=build_error_responses([404], {404: "Team not found"}),
)
async def get_team(
    team_id: str,
    include_agents: bool = Query(default=True, description="Include associated agents with tools and collections in the response"),
    project_id: uuid.UUID = Query(..., description="Project ID"),
    team_service: TeamService = Depends(get_team_service),
) -> TeamWithDetails:
    """
    Retrieve detailed information about a specific team including
    associated agents with their tools and collections.

    **Agent Details:**
    - Each agent includes their bound tools with configurations
    - Each agent includes their accessible collections
    - Tools show enabled status, permissions, and tool-specific config
    - Collections show metadata and access permissions

    **Performance:**
    - Uses efficient eager loading to avoid N+1 query issues
    - Single database query loads team, agents, tools, and collections
    """
    if team_id == "default":
        agents = []
        if include_agents:
            agents = await team_service.get_unassigned_agents(project_id)

        now = datetime.now(timezone.utc)
        return TeamWithDetails(
            id=uuid.UUID(int=0),
            name="Unassigned Agents",
            model="unassigned:none",
            instruction=None,
            expected_output=None,
            session_id=None,
            is_default=False,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            agents=[AgentWithDetails.model_validate(agent) for agent in agents],
        )

    try:
        team_uuid = uuid.UUID(team_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid team_id") from exc
    team = await team_service.get_team(project_id, team_uuid)
    return TeamWithDetails.model_validate(team)


@router.patch(
    "/{team_id}",
    response_model=TeamResponse,
    responses=build_error_responses(
        [400, 404, 409],
        {404: "Team not found", 409: "Team name conflict"},
    ),
)
async def update_team(
    team_id: uuid.UUID,
    team_data: TeamUpdate,
    project_id: uuid.UUID = Query(..., description="Project ID"),
    team_service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    """
    Update team configuration, instructions, model, or settings.

    **Default Team Management:**
    - Setting is_default=true will unset other default teams
    - Only one default team allowed per project
    """
    team = await team_service.update_team(project_id, team_id, team_data)
    return TeamResponse.model_validate(team)


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=build_error_responses([404], {404: "Team not found"}),
)
async def delete_team(
    team_id: uuid.UUID,
    project_id: uuid.UUID = Query(..., description="Project ID"),
    team_service: TeamService = Depends(get_team_service),
) -> None:
    """
    Soft delete a team. Associated agents will have their team_id set to null
    but will remain active.
    """
    await team_service.delete_team(project_id, team_id)
