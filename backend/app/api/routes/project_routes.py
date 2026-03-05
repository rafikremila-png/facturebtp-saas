"""
Project Routes
API endpoints for project management (Chantiers)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.security import ROLE_USER, ROLE_ADMIN
from app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectMarginResponse,
    ProjectTaskCreate, ProjectTaskUpdate, ProjectTaskResponse
)
from app.services.project_service import project_service, project_task_service

router = APIRouter(prefix="/projects", tags=["Projects"])

# Dependency placeholder - will be injected from main app
async def get_current_user():
    pass

@router.post("", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, user: dict = Depends(get_current_user)):
    """Create a new project"""
    project = await project_service.create(user["id"], data.model_dump())
    return project

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """List all projects for the current user"""
    return await project_service.get_all(
        user["id"], 
        status=status, 
        client_id=client_id,
        skip=skip, 
        limit=limit
    )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    """Get a project by ID"""
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, data: ProjectUpdate, user: dict = Depends(get_current_user)):
    """Update a project"""
    project = await project_service.update(project_id, user["id"], data.model_dump(exclude_unset=True))
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    """Delete a project"""
    success = await project_service.delete(project_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return {"message": "Projet supprimé"}

@router.get("/{project_id}/margin", response_model=ProjectMarginResponse)
async def get_project_margin(project_id: str, user: dict = Depends(get_current_user)):
    """Get project margin/profitability"""
    margin = await project_service.get_margin(project_id, user["id"])
    if not margin:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return margin

# ============== PROJECT TASKS ==============

@router.post("/{project_id}/tasks", response_model=ProjectTaskResponse)
async def create_task(project_id: str, data: ProjectTaskCreate, user: dict = Depends(get_current_user)):
    """Create a task for a project"""
    # Verify project belongs to user
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    task = await project_task_service.create(project_id, data.model_dump())
    return task

@router.get("/{project_id}/tasks", response_model=List[ProjectTaskResponse])
async def list_tasks(project_id: str, user: dict = Depends(get_current_user)):
    """List all tasks for a project"""
    # Verify project belongs to user
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return await project_task_service.get_by_project(project_id)

@router.put("/{project_id}/tasks/{task_id}", response_model=ProjectTaskResponse)
async def update_task(project_id: str, task_id: str, data: ProjectTaskUpdate, 
                      user: dict = Depends(get_current_user)):
    """Update a task"""
    # Verify project belongs to user
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    task = await project_task_service.update(task_id, data.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task

@router.delete("/{project_id}/tasks/{task_id}")
async def delete_task(project_id: str, task_id: str, user: dict = Depends(get_current_user)):
    """Delete a task"""
    # Verify project belongs to user
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    success = await project_task_service.delete(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return {"message": "Tâche supprimée"}
