"""
Project Service (Chantiers)
Handles construction project management
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from app.core.database import db, is_mongodb

logger = logging.getLogger(__name__)

class ProjectService:
    """Service for managing construction projects"""
    
    @staticmethod
    async def generate_project_number(user_id: str) -> str:
        """Generate unique project number"""
        year = datetime.now().year
        
        if is_mongodb():
            count = await db.projects.count_documents({
                "user_id": user_id,
                "created_at": {"$regex": f"^{year}"}
            })
        else:
            count = 0
        
        return f"PROJ-{year}-{(count + 1):04d}"
    
    @staticmethod
    async def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project"""
        project_number = await ProjectService.generate_project_number(user_id)
        
        project = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "client_id": data.get("client_id"),
            "project_name": data["project_name"],
            "project_number": project_number,
            "description": data.get("description", ""),
            "address": data.get("address", ""),
            "city": data.get("city", ""),
            "postal_code": data.get("postal_code", ""),
            "status": data.get("status", "planning"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "estimated_duration_days": data.get("estimated_duration_days"),
            "budget": data.get("budget", 0),
            "estimated_cost": data.get("estimated_cost", 0),
            "actual_cost": 0,
            "total_invoiced": 0,
            "total_paid": 0,
            "permit_number": data.get("permit_number", ""),
            "insurance_number": data.get("insurance_number", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.projects.insert_one(project.copy())
        
        return project
    
    @staticmethod
    async def get_by_id(project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        if is_mongodb():
            project = await db.projects.find_one(
                {"id": project_id, "user_id": user_id},
                {"_id": 0}
            )
            if project and project.get("client_id"):
                client = await db.clients.find_one(
                    {"id": project["client_id"]},
                    {"_id": 0}
                )
                project["client"] = client
            return project
        return None
    
    @staticmethod
    async def get_all(user_id: str, status: Optional[str] = None, 
                      client_id: Optional[str] = None,
                      skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all projects for a user"""
        query = {"user_id": user_id}
        
        if status:
            query["status"] = status
        if client_id:
            query["client_id"] = client_id
        
        if is_mongodb():
            cursor = db.projects.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
            projects = await cursor.to_list(length=limit)
            
            # Fetch clients
            client_ids = list(set(p.get("client_id") for p in projects if p.get("client_id")))
            if client_ids:
                clients_cursor = db.clients.find({"id": {"$in": client_ids}}, {"_id": 0})
                clients = {c["id"]: c for c in await clients_cursor.to_list(length=100)}
                for project in projects:
                    if project.get("client_id"):
                        project["client"] = clients.get(project["client_id"])
            
            return projects
        return []
    
    @staticmethod
    async def update(project_id: str, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a project"""
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        if is_mongodb():
            result = await db.projects.update_one(
                {"id": project_id, "user_id": user_id},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return await ProjectService.get_by_id(project_id, user_id)
        return None
    
    @staticmethod
    async def delete(project_id: str, user_id: str) -> bool:
        """Delete a project"""
        if is_mongodb():
            result = await db.projects.delete_one(
                {"id": project_id, "user_id": user_id}
            )
            return result.deleted_count > 0
        return False
    
    @staticmethod
    async def get_margin(project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Calculate project margin"""
        project = await ProjectService.get_by_id(project_id, user_id)
        if not project:
            return None
        
        budget = project.get("budget", 0)
        actual_cost = project.get("actual_cost", 0)
        total_invoiced = project.get("total_invoiced", 0)
        total_paid = project.get("total_paid", 0)
        
        margin = total_invoiced - actual_cost
        margin_percentage = (margin / total_invoiced * 100) if total_invoiced > 0 else 0
        
        return {
            "id": project["id"],
            "project_name": project["project_name"],
            "budget": budget,
            "actual_cost": actual_cost,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "margin": margin,
            "margin_percentage": round(margin_percentage, 2)
        }
    
    @staticmethod
    async def update_financials(project_id: str, user_id: str) -> None:
        """Update project financial totals from invoices and payments"""
        if is_mongodb():
            # Calculate total invoiced
            invoices_cursor = db.invoices.find(
                {"project_id": project_id, "user_id": user_id, "status": {"$ne": "cancelled"}},
                {"total_ttc": 1, "amount_paid": 1}
            )
            invoices = await invoices_cursor.to_list(length=1000)
            
            total_invoiced = sum(inv.get("total_ttc", 0) for inv in invoices)
            total_paid = sum(inv.get("amount_paid", 0) for inv in invoices)
            
            await db.projects.update_one(
                {"id": project_id, "user_id": user_id},
                {
                    "$set": {
                        "total_invoiced": total_invoiced,
                        "total_paid": total_paid,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )


class ProjectTaskService:
    """Service for managing project tasks"""
    
    @staticmethod
    async def create(project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        task = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "status": data.get("status", "pending"),
            "priority": data.get("priority", "medium"),
            "start_date": data.get("start_date"),
            "due_date": data.get("due_date"),
            "completed_at": None,
            "assigned_to": data.get("assigned_to", ""),
            "progress_percentage": data.get("progress_percentage", 0),
            "sort_order": data.get("sort_order", 0),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.project_tasks.insert_one(task.copy())
        
        return task
    
    @staticmethod
    async def get_by_project(project_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a project"""
        if is_mongodb():
            cursor = db.project_tasks.find(
                {"project_id": project_id},
                {"_id": 0}
            ).sort([("sort_order", 1), ("created_at", 1)])
            return await cursor.to_list(length=500)
        return []
    
    @staticmethod
    async def update(task_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task"""
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Handle completion
        if data.get("status") == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            update_data["progress_percentage"] = 100
        
        if is_mongodb():
            result = await db.project_tasks.update_one(
                {"id": task_id},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return await db.project_tasks.find_one({"id": task_id}, {"_id": 0})
        return None
    
    @staticmethod
    async def delete(task_id: str) -> bool:
        """Delete a task"""
        if is_mongodb():
            result = await db.project_tasks.delete_one({"id": task_id})
            return result.deleted_count > 0
        return False


# Create singleton instances
project_service = ProjectService()
project_task_service = ProjectTaskService()
