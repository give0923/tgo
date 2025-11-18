"""Assignment endpoints."""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.models import Staff, Visitor, VisitorAssignment
from app.schemas import (
    AssignmentCreate,
    AssignmentListParams,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdate,
)

logger = get_logger("endpoints.assignments")
router = APIRouter()


@router.get("", response_model=AssignmentListResponse)
async def list_assignments(
    params: AssignmentListParams = Depends(),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AssignmentListResponse:
    """
    List assignments.
    
    Retrieve a paginated list of visitor assignments with optional filtering.
    """
    logger.info(f"User {current_user.username} listing assignments")
    
    # Build query
    query = db.query(VisitorAssignment).filter(
        VisitorAssignment.project_id == current_user.project_id
    )
    
    # Apply filters
    if params.visitor_id:
        query = query.filter(VisitorAssignment.visitor_id == params.visitor_id)
    if params.assigned_staff_id:
        query = query.filter(VisitorAssignment.assigned_staff_id == params.assigned_staff_id)
    if params.assignment_type:
        query = query.filter(VisitorAssignment.assignment_type == params.assignment_type)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering (most recent first)
    assignments = query.order_by(VisitorAssignment.timestamp.desc()).offset(params.offset).limit(params.limit).all()
    
    # Convert to response models
    assignment_responses = [AssignmentResponse.model_validate(assignment) for assignment in assignments]
    
    return AssignmentListResponse(
        data=assignment_responses,
        pagination={
            "total": total,
            "limit": params.limit,
            "offset": params.offset,
            "has_next": params.offset + params.limit < total,
            "has_previous": params.offset > 0,
        }
    )


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AssignmentResponse:
    """
    Create assignment.
    
    Create a new visitor assignment. Validates visitor and staff existence,
    and publishes assignment event for AI Service coordination.
    """
    logger.info(f"User {current_user.username} creating assignment for visitor: {assignment_data.visitor_id}")
    
    # Validate visitor exists and belongs to project
    visitor = db.query(Visitor).filter(
        Visitor.id == assignment_data.visitor_id,
        Visitor.project_id == current_user.project_id,
        Visitor.deleted_at.is_(None)
    ).first()
    
    if not visitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visitor not found"
        )
    
    # Validate assigned staff exists and belongs to project (if provided)
    if assignment_data.assigned_staff_id:
        assigned_staff = db.query(Staff).filter(
            Staff.id == assignment_data.assigned_staff_id,
            Staff.project_id == current_user.project_id,
            Staff.deleted_at.is_(None)
        ).first()
        
        if not assigned_staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned staff member not found"
            )
    
    # Validate previous staff exists and belongs to project (if provided)
    if assignment_data.previous_staff_id:
        previous_staff = db.query(Staff).filter(
            Staff.id == assignment_data.previous_staff_id,
            Staff.project_id == current_user.project_id,
            Staff.deleted_at.is_(None)
        ).first()
        
        if not previous_staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Previous staff member not found"
            )
    
    # Create assignment
    assignment = VisitorAssignment(
        project_id=current_user.project_id,
        visitor_id=assignment_data.visitor_id,
        assigned_staff_id=assignment_data.assigned_staff_id,
        previous_staff_id=assignment_data.previous_staff_id,
        assigned_by_staff_id=assignment_data.assigned_by_staff_id or current_user.id,
        assignment_type=assignment_data.assignment_type,
        notes=assignment_data.notes,
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    logger.info(f"Created assignment {assignment.id} for visitor {assignment.visitor_id}")
    
    return AssignmentResponse.model_validate(assignment)


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AssignmentResponse:
    """Get assignment details."""
    logger.info(f"User {current_user.username} getting assignment: {assignment_id}")
    
    assignment = db.query(VisitorAssignment).filter(
        VisitorAssignment.id == assignment_id,
        VisitorAssignment.project_id == current_user.project_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return AssignmentResponse.model_validate(assignment)


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    assignment_data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> AssignmentResponse:
    """
    Update assignment.
    
    Update assignment notes or other mutable fields.
    """
    logger.info(f"User {current_user.username} updating assignment: {assignment_id}")
    
    assignment = db.query(VisitorAssignment).filter(
        VisitorAssignment.id == assignment_id,
        VisitorAssignment.project_id == current_user.project_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Update fields
    update_data = assignment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    assignment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    
    logger.info(f"Updated assignment {assignment.id}")
    
    return AssignmentResponse.model_validate(assignment)
