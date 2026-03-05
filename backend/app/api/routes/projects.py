"""
Project Routes (Chantiers)
CRUD operations for projects and tasks with BTP-specific features
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.project_service import get_project_service
from app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectTaskCreate, ProjectTaskUpdate, ProjectTaskResponse,
    ProjectMarginResponse
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects (Chantiers)"])


# ============== PROJECTS ==============

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project (chantier)."""
    project_service = get_project_service(db)
    project = await project_service.create_project(current_user["id"], project_data)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects for the current user."""
    project_service = get_project_service(db)
    projects = await project_service.list_projects(
        user_id=current_user["id"],
        skip=skip,
        limit=limit,
        status=status,
        client_id=client_id,
        include_client=True
    )
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/timeline")
async def get_projects_timeline(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get timeline view of all projects with tasks."""
    project_service = get_project_service(db)
    return await project_service.get_project_timeline(current_user["id"])


@router.get("/margins", response_model=List[ProjectMarginResponse])
async def get_all_margins(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get margin calculations for all projects."""
    project_service = get_project_service(db)
    return await project_service.get_all_margins(current_user["id"])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project."""
    project_service = get_project_service(db)
    project = await project_service.get_project_by_id(
        project_id, 
        current_user["id"],
        include_client=True,
        include_tasks=True
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/margin", response_model=ProjectMarginResponse)
async def get_project_margin(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get margin calculation for a specific project."""
    project_service = get_project_service(db)
    margin = await project_service.get_project_margin(project_id, current_user["id"])
    
    if not margin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    return margin


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a project."""
    project_service = get_project_service(db)
    project = await project_service.update_project(project_id, current_user["id"], project_data)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project."""
    project_service = get_project_service(db)
    success = await project_service.delete_project(project_id, current_user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    return {"message": "Chantier supprimé"}


@router.post("/{project_id}/recalculate")
async def recalculate_financials(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recalculate project financial totals from invoices."""
    project_service = get_project_service(db)
    
    # Verify ownership
    project = await project_service.get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    await project_service.update_project_financials(project_id)
    return {"message": "Finances recalculées"}


# ============== TASKS ==============

@router.post("/{project_id}/tasks", response_model=ProjectTaskResponse)
async def create_task(
    project_id: str,
    task_data: ProjectTaskCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task for a project."""
    project_service = get_project_service(db)
    
    # Override project_id from URL
    task_data.project_id = project_id
    
    task = await project_service.create_task(project_id, current_user["id"], task_data)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    return ProjectTaskResponse.model_validate(task)


@router.get("/{project_id}/tasks", response_model=List[ProjectTaskResponse])
async def list_tasks(
    project_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tasks for a project."""
    project_service = get_project_service(db)
    
    # Verify project ownership
    project = await project_service.get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    tasks = await project_service.list_tasks(project_id, status, priority)
    return [ProjectTaskResponse.model_validate(t) for t in tasks]


@router.put("/tasks/{task_id}", response_model=ProjectTaskResponse)
async def update_task(
    task_id: str,
    task_data: ProjectTaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    project_service = get_project_service(db)
    
    # Get task and verify ownership via project
    task = await project_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tâche non trouvée"
        )
    
    # Verify project ownership
    project = await project_service.get_project_by_id(task.project_id, current_user["id"])
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    updated_task = await project_service.update_task(task_id, task_data)
    return ProjectTaskResponse.model_validate(updated_task)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task."""
    project_service = get_project_service(db)
    
    # Get task and verify ownership via project
    task = await project_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tâche non trouvée"
        )
    
    # Verify project ownership
    project = await project_service.get_project_by_id(task.project_id, current_user["id"])
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    await project_service.delete_task(task_id)
    return {"message": "Tâche supprimée"}
