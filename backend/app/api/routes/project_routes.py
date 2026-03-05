"""
Project Routes
API endpoints for project management (Chantiers)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user
from app.services.project_service import project_service, project_task_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("")
async def create_project(
    project_name: str,
    client_id: Optional[str] = None,
    description: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    postal_code: Optional[str] = None,
    status: Optional[str] = "planning",
    budget: Optional[float] = 0,
    user: dict = Depends(get_current_user)
):
    """Create a new project"""
    data = {
        "project_name": project_name,
        "client_id": client_id,
        "description": description,
        "address": address,
        "city": city,
        "postal_code": postal_code,
        "status": status,
        "budget": budget
    }
    project = await project_service.create(user["id"], data)
    return project


@router.get("")
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


@router.get("/{project_id}")
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    """Get a project by ID"""
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_name: Optional[str] = None,
    client_id: Optional[str] = None,
    description: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    postal_code: Optional[str] = None,
    status: Optional[str] = None,
    budget: Optional[float] = None,
    actual_cost: Optional[float] = None,
    user: dict = Depends(get_current_user)
):
    """Update a project"""
    data = {}
    if project_name is not None:
        data["project_name"] = project_name
    if client_id is not None:
        data["client_id"] = client_id
    if description is not None:
        data["description"] = description
    if address is not None:
        data["address"] = address
    if city is not None:
        data["city"] = city
    if postal_code is not None:
        data["postal_code"] = postal_code
    if status is not None:
        data["status"] = status
    if budget is not None:
        data["budget"] = budget
    if actual_cost is not None:
        data["actual_cost"] = actual_cost
    
    project = await project_service.update(project_id, user["id"], data)
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


@router.get("/{project_id}/margin")
async def get_project_margin(project_id: str, user: dict = Depends(get_current_user)):
    """Get project margin/profitability"""
    margin = await project_service.get_margin(project_id, user["id"])
    if not margin:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return margin


# ============== PROJECT TASKS ==============

@router.post("/{project_id}/tasks")
async def create_task(
    project_id: str,
    title: str,
    description: Optional[str] = None,
    status: Optional[str] = "pending",
    priority: Optional[str] = "medium",
    assigned_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Create a task for a project"""
    # Verify project belongs to user
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    data = {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "assigned_to": assigned_to
    }
    
    task = await project_task_service.create(project_id, data)
    return task


@router.get("/{project_id}/tasks")
async def list_tasks(project_id: str, user: dict = Depends(get_current_user)):
    """List all tasks for a project"""
    # Verify project belongs to user
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return await project_task_service.get_by_project(project_id)


@router.put("/{project_id}/tasks/{task_id}")
async def update_task(
    project_id: str,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    progress_percentage: Optional[int] = None,
    user: dict = Depends(get_current_user)
):
    """Update a task"""
    # Verify project belongs to user
    project = await project_service.get_by_id(project_id, user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    data = {}
    if title is not None:
        data["title"] = title
    if description is not None:
        data["description"] = description
    if status is not None:
        data["status"] = status
    if priority is not None:
        data["priority"] = priority
    if progress_percentage is not None:
        data["progress_percentage"] = progress_percentage
    
    task = await project_task_service.update(task_id, data)
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
