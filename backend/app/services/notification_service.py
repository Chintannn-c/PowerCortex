import os
import logging
from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime

from ..core.database import get_database
from ..models.notification import NotificationCreate, NotificationResponse
from ..utils.helpers import utcnow

# Firebase Admin SDK Setup
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger("powercortex.services.notifications")

# Initialize Firebase Admin inside try/except block to be fully crash-safe
try:
    # Use google-services.json if it's actually a service account file, 
    # or fallback to environment path, or initialize without credentials (ADC)
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "android/app/google-services.json")
    if os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized successfully using Certificate.")
        except Exception as cert_err:
            logger.warning(f"Failed to load certificate {cred_path}: {cert_err}. Falling back to default app initialization.")
            firebase_admin.initialize_app()
    else:
        firebase_admin.initialize_app()
        logger.info("Firebase Admin initialized using default credentials.")
except Exception as e:
    logger.warning(f"Firebase Admin SDK initialization skipped or failed: {e}. Simulated push alerts will be used.")

class NotificationService:
    @staticmethod
    async def create_and_send_notification(data: NotificationCreate) -> NotificationResponse:
        """
        Stores the notification in MongoDB, handles AI grouping, and sends broadcasts via WebSockets/FCM.
        """
        db = get_database()

        # 0. Check if asset/entity is snoozed/muted
        if data.entity_id:
            try:
                snooze_doc = await db.snoozed_assets.find_one({"entity_id": data.entity_id})
                if snooze_doc:
                    expires_at = snooze_doc.get("expires_at")
                    if expires_at:
                        expires_at_naive = expires_at.replace(tzinfo=None)
                        utcnow_naive = utcnow().replace(tzinfo=None)
                        if expires_at_naive > utcnow_naive:
                            logger.info(f"Notification for asset {data.entity_id} skipped due to active snooze.")
                            # Return a response marked as read and not persisted
                            dummy_doc = data.model_dump(by_alias=True)
                            dummy_doc["_id"] = "snoozed"
                            dummy_doc["is_read"] = True
                            dummy_doc["created_at"] = utcnow()
                            return NotificationResponse(**dummy_doc)
            except Exception as snooze_err:
                logger.error(f"Snooze check failed: {snooze_err}")

        # 1. AI Grouping / Deduplication for Cascading Alerts
        from .alert_deduplicator import AlertDeduplicator
        grouped_result = await AlertDeduplicator.check_and_group(db, data)
        
        merged_ids = []
        if grouped_result:
            # We have a cascade event! Modify the title and message to the grouped ones.
            logger.info(f"Grouped cascading alerts. Title: {grouped_result['title']}")
            data.title = grouped_result["title"]
            data.message = grouped_result["message"]
            merged_ids = grouped_result["merged_ids"]

            # Mark old merged notifications as read/grouped in DB
            if merged_ids:
                try:
                    await db.notifications.update_many(
                        {"_id": {"$in": [ObjectId(mid) for mid in merged_ids]}},
                        {"$set": {"is_read": True, "grouped_under": "cascade"}}
                    )
                except Exception as db_err:
                    logger.error(f"Failed to mark merged notifications read: {db_err}")

        # 2. Save new notification to MongoDB
        notif_doc = data.model_dump(by_alias=True)
        notif_doc["is_read"] = False
        notif_doc["created_at"] = utcnow()
        if grouped_result:
            notif_doc["merged_ids"] = merged_ids

        result = await db.notifications.insert_one(notif_doc)
        notif_doc["_id"] = str(result.inserted_id)

        # 3. Retrieve user FCM tokens
        target_tokens = []
        if data.user_id:
            user = await db.users.find_one({"_id": ObjectId(data.user_id)})
            if user and "fcm_tokens" in user:
                target_tokens.extend(user["fcm_tokens"])
        else:
            # Broadcast to all users
            async for u in db.users.find({"fcm_tokens": {"$exists": True, "$not": {"$size": 0}}}):
                target_tokens.extend(u.get("fcm_tokens", []))

        # 4. Broadcast via WebSockets
        try:
            from ..core.websocket import manager as ws_manager
            payload = {
                "id": notif_doc["_id"],
                "title": notif_doc.get("title"),
                "message": notif_doc.get("message"),
                "type": notif_doc.get("type"),
                "screen": notif_doc.get("screen"),
                "entity_id": notif_doc.get("entity_id"),
                "is_read": notif_doc.get("is_read"),
                "created_at": notif_doc.get("created_at").isoformat() if isinstance(notif_doc.get("created_at"), datetime) else notif_doc.get("created_at")
            }
            if grouped_result:
                payload["merged_ids"] = merged_ids
            await ws_manager.broadcast(payload)
        except Exception as ws_err:
            logger.error(f"WebSocket broadcast failed: {ws_err}")

        # 5. Send FCM Push Notification
        if target_tokens:
            try:
                # Check if firebase app is initialized
                if firebase_admin._apps:
                    message = messaging.MulticastMessage(
                        notification=messaging.Notification(
                            title=data.title,
                            body=data.message,
                        ),
                        data={
                            "id": notif_doc["_id"],
                            "screen": data.screen,
                            "entity_id": str(data.entity_id) if data.entity_id else ""
                        },
                        tokens=target_tokens
                    )
                    messaging.send_multicast(message)
                    logger.info(f"FCM multicast sent to {len(target_tokens)} devices.")
                else:
                    logger.info(f"[FCM Simulation] Firebase not initialized. Sending push to {len(target_tokens)} tokens.")
            except Exception as fcm_err:
                logger.error(f"FCM sending failed: {fcm_err}. Fell back to simulated push.")

        # 6. Voice Escalation for Critical Alerts (SMS disabled)
        is_critical = "critical" in data.title.lower() or "critical" in data.message.lower() or "explosion" in data.message.lower()
        if is_critical:
            try:
                from .twilio_service import TwilioService
                voice_text = f"Attention. A critical grid alert has been detected: {data.title}. Please review the operations dashboard immediately."
                await TwilioService.trigger_voice_call(voice_text)
            except Exception as twilio_err:
                logger.error(f"Twilio escalation failed: {twilio_err}")

        return NotificationResponse(**notif_doc)

    @staticmethod
    async def get_user_notifications(user_id: str, skip: int = 0, limit: int = 20) -> List[NotificationResponse]:
        """
        Retrieve notifications targeted at a specific user or global broadcasts.
        """
        db = get_database()
        query = {
            "$or": [
                {"user_id": user_id},
                {"user_id": None}
            ]
        }
        cursor = db.notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
        notifications = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            notifications.append(NotificationResponse(**doc))
        return notifications

    @staticmethod
    async def mark_as_read(notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read.
        """
        if notification_id == "snoozed":
            return True
        try:
            oid = ObjectId(notification_id)
        except Exception:
            return False

        db = get_database()
        result = await db.notifications.update_one(
            {"_id": oid},
            {"$set": {"is_read": True}}
        )
        return result.matched_count > 0

    @staticmethod
    async def register_device_token(user_id: str, token: str) -> bool:
        """
        Add an FCM token to a user's array of tokens.
        """
        db = get_database()
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"fcm_tokens": token}}
        )
        return result.modified_count > 0
