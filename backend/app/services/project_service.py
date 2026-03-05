"""
Project Service - CRUD operations for projects (chantiers)
PostgreSQL/Supabase implementation
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Project, ProjectTask, Client, Invoice, Quote
from app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectTaskCreate, ProjectTaskUpdate, ProjectTaskResponse,
    ProjectMarginResponse
)
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project (chantier) database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_project(self, user_id: str, project_data: ProjectCreate) -> Project:
        """Create a new project"""
        # Generate project number
        count = await self.count_projects(user_id)
        project_number = f"PROJ-{count + 1:04d}"
        
        project = Project(
            id=generate_uuid(),
            user_id=user_id,
            client_id=project_data.client_id,
            project_name=project_data.project_name,
            project_number=project_number,
            description=project_data.description,
            address=project_data.address,
            city=project_data.city,
            postal_code=project_data.postal_code,
            status=project_data.status or "planning",
            start_date=project_data.start_date,
            end_date=project_data.end_date,
            estimated_duration_days=project_data.estimated_duration_days,
            budget=project_data.budget or 0,
            estimated_cost=project_data.estimated_cost or 0,
            actual_cost=0,
            total_invoiced=0,
            total_paid=0,
            permit_number=project_data.permit_number,
            insurance_number=project_data.insurance_number,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(project)
        await self.db.flush()
        return project
    
    async def get_project_by_id(
        self, 
        project_id: str, 
        user_id: Optional[str] = None,
        include_client: bool = False,
        include_tasks: bool = False
    ) -> Optional[Project]:
        """Get project by ID"""
        query = select(Project).where(Project.id == project_id)
        
        if user_id:
            query = query.where(Project.user_id == user_id)
        
        if include_client:
            query = query.options(selectinload(Project.client))
        
        if include_tasks:
            query = query.options(selectinload(Project.tasks))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_project(
        self, 
        project_id: str, 
        user_id: str, 
        project_data: ProjectUpdate
    ) -> Optional[Project]:
        """Update project information"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        
        update_data = project_data.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in update_data.items():
            setattr(project, key, value)
        
        await self.db.flush()
        return project
    
    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """Delete a project"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False
        
        await self.db.delete(project)
        return True
    
    async def list_projects(
        self, 
        user_id: str,
        skip: int = 0, 
        limit: int = 50,
        status: Optional[str] = None,
        client_id: Optional[str] = None,
        include_client: bool = False
    ) -> List[Project]:
        """List projects for a user"""
        query = select(Project).where(Project.user_id == user_id)
        
        if status:
            query = query.where(Project.status == status)
        
        if client_id:
            query = query.where(Project.client_id == client_id)
        
        if include_client:
            query = query.options(selectinload(Project.client))
        
        query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_projects(
        self, 
        user_id: str,
        status: Optional[str] = None
    ) -> int:
        """Count projects for a user"""
        query = select(func.count(Project.id)).where(Project.user_id == user_id)
        
        if status:
            query = query.where(Project.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_project_margin(self, project_id: str, user_id: str) -> Optional[ProjectMarginResponse]:
        """Calculate project margin"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        
        # Calculate margin
        revenue = project.total_invoiced or 0
        costs = project.actual_cost or 0
        margin = revenue - costs
        margin_percentage = (margin / revenue * 100) if revenue > 0 else 0
        
        return ProjectMarginResponse(
            id=project.id,
            project_name=project.project_name,
            budget=project.budget or 0,
            actual_cost=costs,
            total_invoiced=revenue,
            total_paid=project.total_paid or 0,
            margin=margin,
            margin_percentage=round(margin_percentage, 2)
        )
    
    async def get_all_margins(self, user_id: str) -> List[ProjectMarginResponse]:
        """Get margins for all projects"""
        projects = await self.list_projects(user_id, limit=1000)
        
        margins = []
        for project in projects:
            revenue = project.total_invoiced or 0
            costs = project.actual_cost or 0
            margin = revenue - costs
            margin_percentage = (margin / revenue * 100) if revenue > 0 else 0
            
            margins.append(ProjectMarginResponse(
                id=project.id,
                project_name=project.project_name,
                budget=project.budget or 0,
                actual_cost=costs,
                total_invoiced=revenue,
                total_paid=project.total_paid or 0,
                margin=margin,
                margin_percentage=round(margin_percentage, 2)
            ))
        
        return margins
    
    async def update_project_financials(self, project_id: str) -> bool:
        """Recalculate project financial totals from invoices"""
        project = await self.get_project_by_id(project_id)
        if not project:
            return False
        
        # Get totals from invoices
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(Invoice.total_ttc), 0).label('total_invoiced'),
                func.coalesce(func.sum(Invoice.amount_paid), 0).label('total_paid')
            ).where(Invoice.project_id == project_id)
        )
        stats = result.one()
        
        project.total_invoiced = float(stats.total_invoiced)
        project.total_paid = float(stats.total_paid)
        project.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return True
    
    # ============== PROJECT TASKS ==============
    
    async def create_task(self, project_id: str, user_id: str, task_data: ProjectTaskCreate) -> Optional[ProjectTask]:
        """Create a task for a project"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        
        # Get next sort order
        count_result = await self.db.execute(
            select(func.count(ProjectTask.id)).where(ProjectTask.project_id == project_id)
        )
        count = count_result.scalar() or 0
        
        task = ProjectTask(
            id=generate_uuid(),
            project_id=project_id,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status or "pending",
            priority=task_data.priority or "medium",
            start_date=task_data.start_date,
            due_date=task_data.due_date,
            assigned_to=task_data.assigned_to,
            progress_percentage=task_data.progress_percentage or 0,
            sort_order=count,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(task)
        await self.db.flush()
        return task
    
    async def get_task_by_id(self, task_id: str) -> Optional[ProjectTask]:
        """Get task by ID"""
        result = await self.db.execute(
            select(ProjectTask).where(ProjectTask.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def update_task(self, task_id: str, task_data: ProjectTaskUpdate) -> Optional[ProjectTask]:
        """Update a task"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        # Mark as completed if status changed to completed
        if update_data.get('status') == 'completed' and task.status != 'completed':
            update_data['completed_at'] = datetime.now(timezone.utc)
            update_data['progress_percentage'] = 100
        
        for key, value in update_data.items():
            setattr(task, key, value)
        
        await self.db.flush()
        return task
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False
        
        await self.db.delete(task)
        return True
    
    async def list_tasks(
        self, 
        project_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[ProjectTask]:
        """List tasks for a project"""
        query = select(ProjectTask).where(ProjectTask.project_id == project_id)
        
        if status:
            query = query.where(ProjectTask.status == status)
        
        if priority:
            query = query.where(ProjectTask.priority == priority)
        
        query = query.order_by(ProjectTask.sort_order)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_project_timeline(self, user_id: str) -> List[dict]:
        """Get timeline data for all projects"""
        projects = await self.list_projects(user_id, include_client=True, limit=100)
        
        timeline = []
        for project in projects:
            tasks = await self.list_tasks(project.id)
            
            timeline.append({
                'project_id': project.id,
                'project_name': project.project_name,
                'project_number': project.project_number,
                'client_name': project.client.name if project.client else None,
                'status': project.status,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'progress': sum(t.progress_percentage or 0 for t in tasks) / len(tasks) if tasks else 0,
                'tasks': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'status': t.status,
                        'start_date': t.start_date.isoformat() if t.start_date else None,
                        'due_date': t.due_date.isoformat() if t.due_date else None,
                        'progress': t.progress_percentage
                    }
                    for t in tasks
                ]
            })
        
        return timeline


def get_project_service(db: AsyncSession) -> ProjectService:
    """Factory function for dependency injection"""
    return ProjectService(db)
