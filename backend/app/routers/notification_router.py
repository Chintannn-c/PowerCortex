import logging
from typing import List, Optional
from datetime import timedelta
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger("powercortex.routers.notifications")

from ..models.notification import NotificationCreate, NotificationResponse
from ..services.notification_service import NotificationService
from ..core.dependencies import get_current_user
from ..models.user import UserDocument
from ..core.database import get_database
from ..core.security import decode_access_token
from ..core.websocket import manager as ws_manager
from ..utils.helpers import utcnow

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

class TokenRequest(BaseModel):
    fcm_token: str

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(skip: int = 0, limit: int = 20, current_user: UserDocument = Depends(get_current_user)):
    """
    Retrieve notification history for the current user.
    """
    return await NotificationService.get_user_notifications(str(current_user["_id"]), skip=skip, limit=limit)

@router.post("/fcm-token")
async def register_fcm_token(request: TokenRequest, current_user: UserDocument = Depends(get_current_user)):
    """
    Register a device's FCM token for push notifications.
    """
    success = await NotificationService.register_device_token(str(current_user["_id"]), request.fcm_token)
    return {"success": True, "message": "Token registered"}

@router.put("/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: UserDocument = Depends(get_current_user)):
    """
    Mark a specific notification as read.
    """
    success = await NotificationService.mark_as_read(notification_id, str(current_user["_id"]))
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found or already read")
    return {"success": True, "message": "Marked as read"}

@router.post("/{notification_id}/acknowledge")
async def acknowledge_notification(notification_id: str, current_user: UserDocument = Depends(get_current_user)):
    """
    Instantly acknowledge a notification and resolve the underlying asset fault.
    """
    db = get_database()
    # 1. Mark notification as read
    notif_success = await NotificationService.mark_as_read(notification_id, str(current_user["_id"]))
    if not notif_success:
        raise HTTPException(status_code=404, detail="Notification not found")

    # 2. Try to resolve underlying fault/anomaly
    notif = await db.notifications.find_one({"_id": ObjectId(notification_id)})
    if notif and notif.get("entity_id"):
        entity_id = notif.get("entity_id")
        await db.faults.update_one(
            {"fault_id": entity_id},
            {"$set": {"status": "Resolved", "resolved_at": utcnow()}}
        )

    return {"success": True, "message": "Notification acknowledged and fault marked resolved."}

@router.post("/{notification_id}/dispatch")
async def dispatch_crew(notification_id: str, current_user: UserDocument = Depends(get_current_user)):
    """
    Automatically create and assign a field maintenance ticket in MongoDB for this notification.
    """
    db = get_database()
    notif = await db.notifications.find_one({"_id": ObjectId(notification_id)})
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    entity_id = notif.get("entity_id", "Unknown Asset")
    ticket = {
        "notification_id": notification_id,
        "entity_id": entity_id,
        "assigned_to": "Field Crew Delta",
        "status": "Dispatched",
        "created_at": utcnow(),
        "dispatched_by": str(current_user["_id"])
    }
    await db.maintenance_tickets.insert_one(ticket)

    # Mark notification read
    await NotificationService.mark_as_read(notification_id, str(current_user["_id"]))

    # Update fault status to "In Progress"
    if entity_id:
        await db.faults.update_one(
            {"fault_id": entity_id},
            {"$set": {"status": "In Progress"}}
        )

    # Convert objectId to string for response
    ticket["_id"] = str(ticket["_id"])
    return {"success": True, "message": "Crew successfully dispatched. Ticket created.", "ticket": ticket}

@router.post("/{notification_id}/snooze")
async def snooze_alert(notification_id: str, current_user: UserDocument = Depends(get_current_user)):
    """
    Snooze/mute subsequent notifications for the asset for 1 hour.
    """
    db = get_database()
    notif = await db.notifications.find_one({"_id": ObjectId(notification_id)})
    if not notif or not notif.get("entity_id"):
        raise HTTPException(status_code=404, detail="Notification or entity asset not found")

    entity_id = notif.get("entity_id")
    expires_at = utcnow() + timedelta(hours=1)

    await db.snoozed_assets.update_one(
        {"entity_id": entity_id},
        {"$set": {"expires_at": expires_at, "snoozed_by": str(current_user["_id"])}},
        upsert=True
    )

    # Mark notification read
    await NotificationService.mark_as_read(notification_id, str(current_user["_id"]))

    return {"success": True, "message": f"Notifications for asset {entity_id} snoozed for 1 hour."}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    Establish persistent WebSocket connection with Flutter client for instant notification broadcasts.
    """
    # Try to decode token for authentication if available
    user_id = None
    if token:
        try:
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("sub")
        except Exception as e:
            logger.error(f"Handled error: {e}") # fallback to anonymous connection

    await ws_manager.connect(websocket)
    try:
        while True:
            # Maintain active connection and listen for heartbeat
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@router.delete("/")
async def delete_all_notifications(current_user: UserDocument = Depends(get_current_user)):
    """
    Clear all notifications for the current user.
    """
    db = get_database()
    user_id = str(current_user["_id"])
    await db.notifications.delete_many({"$or": [{"user_id": user_id}, {"user_id": None}]})
    return {"success": True, "message": "Your notifications cleared successfully"}

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: UserDocument = Depends(get_current_user)):
    """
    Delete a specific notification by ID.
    """
    db = get_database()
    try:
        oid = ObjectId(notification_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")
        
    result = await db.notifications.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True, "message": "Notification deleted successfully"}

@router.post("/test", response_model=NotificationResponse)
async def test_trigger_notification(notif: NotificationCreate, current_user: UserDocument = Depends(get_current_user)):
    """
    Test endpoint to simulate ML triggering a notification. Requires authentication.
    """
    return await NotificationService.create_and_send_notification(notif)
