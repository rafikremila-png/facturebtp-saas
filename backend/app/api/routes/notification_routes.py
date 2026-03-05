"""
Marketing Notification Routes
API endpoints for marketing notifications
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.marketing_notification_service import marketing_notification_service

router = APIRouter(prefix="/notifications", tags=["Marketing Notifications"])

# Dependency placeholder
async def get_current_user():
    pass

@router.get("")
async def list_notifications(
    include_read: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """List notifications for current user"""
    notifications = await marketing_notification_service.get_user_notifications(
        user["id"], include_read, limit
    )
    return {"notifications": notifications}

@router.get("/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    count = await marketing_notification_service.get_unread_count(user["id"])
    return {"count": count}

@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    success = await marketing_notification_service.mark_as_read(notification_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    return {"message": "Notification marquée comme lue"}

@router.post("/read-all")
async def mark_all_as_read(user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    count = await marketing_notification_service.mark_all_as_read(user["id"])
    return {"message": f"{count} notifications marquées comme lues"}

@router.post("/{notification_id}/dismiss")
async def dismiss_notification(notification_id: str, user: dict = Depends(get_current_user)):
    """Dismiss a notification"""
    success = await marketing_notification_service.dismiss_notification(notification_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    return {"message": "Notification ignorée"}

@router.post("/check-automated")
async def check_automated_notifications(user: dict = Depends(get_current_user)):
    """Check and create automated notifications based on user activity"""
    created = await marketing_notification_service.check_and_create_automated_notifications(user["id"])
    return {"created": len(created), "notifications": created}
