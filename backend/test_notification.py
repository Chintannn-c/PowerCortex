import os
import sys
import unittest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.utils.helpers import utcnow

MOCK_USER_ID = "60d5ec4b9b1d8b2d888f4e12"
app.dependency_overrides[get_current_user] = lambda: {
    "_id": MOCK_USER_ID,
    "username": "admin",
    "email": "admin@guvnl.gov.in"
}

class TestNotificationsAdvanced(unittest.TestCase):
    def setUp(self):
        # Clear test database notifications, faults, maintenance_tickets, snoozed_assets before test
        async def clear_db():
            client = AsyncIOMotorClient(settings.MONGODB_URL)
            db = client[settings.DATABASE_NAME]
            await db.notifications.delete_many({})
            await db.faults.delete_many({"fault_id": "test_asset_123"})
            await db.maintenance_tickets.delete_many({"entity_id": "test_asset_123"})
            await db.snoozed_assets.delete_many({"entity_id": "test_asset_123"})
            client.close()
        asyncio.run(clear_db())

    def test_snooze_alert_flow(self):
        """Test POST /snooze endpoint and verify subsequent alerts are blocked."""
        with TestClient(app) as client:
            # 1. Create a notification first
            payload = {
                "title": "Voltage Sag Alert",
                "message": "Voltage dropped below 180V on test_asset_123",
                "type": "fault",
                "screen": "fault_detection",
                "entity_id": "test_asset_123"
            }
            res = client.post("/api/notifications/test", json=payload)
            self.assertEqual(res.status_code, 200)
            notif_id = res.json().get("id") or res.json().get("_id")

            # 2. Call snooze endpoint
            snooze_res = client.post(f"/api/notifications/{notif_id}/snooze")
            self.assertEqual(snooze_res.status_code, 200)
            self.assertTrue(snooze_res.json()["success"])

            # 3. Verify entry in snoozed_assets DB collection
            async def check_snooze():
                conn = AsyncIOMotorClient(settings.MONGODB_URL)
                db = conn[settings.DATABASE_NAME]
                doc = await db.snoozed_assets.find_one({"entity_id": "test_asset_123"})
                conn.close()
                return doc

            snooze_doc = asyncio.run(check_snooze())
            self.assertIsNotNone(snooze_doc)
            self.assertTrue(snooze_doc["expires_at"].replace(tzinfo=None) > utcnow().replace(tzinfo=None))

            # 4. Trigger subsequent alert, verify it gets blocked (returns "snoozed" id and marked is_read)
            res2 = client.post("/api/notifications/test", json=payload)
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            notif2_id = data2.get("id") or data2.get("_id")
            self.assertEqual(notif2_id, "snoozed")
            self.assertTrue(data2["is_read"])

    def test_acknowledge_and_resolve_flow(self):
        """Test POST /acknowledge endpoint and verify fault is resolved."""
        with TestClient(app) as client:
            # Seed a mock fault
            async def seed_fault():
                conn = AsyncIOMotorClient(settings.MONGODB_URL)
                db = conn[settings.DATABASE_NAME]
                await db.faults.insert_one({
                    "fault_id": "test_asset_123",
                    "asset_name": "Transformer A",
                    "fault_type": "Voltage Sag",
                    "status": "Active",
                    "severity": "High",
                    "probability": 85.0
                })
                conn.close()
            asyncio.run(seed_fault())

            # Trigger notification
            payload = {
                "title": "Voltage Sag Alert",
                "message": "Voltage dropped below 180V on test_asset_123",
                "type": "fault",
                "screen": "fault_detection",
                "entity_id": "test_asset_123"
            }
            res = client.post("/api/notifications/test", json=payload)
            self.assertEqual(res.status_code, 200)
            notif_id = res.json().get("id") or res.json().get("_id")

            # Call acknowledge
            ack_res = client.post(f"/api/notifications/{notif_id}/acknowledge")
            self.assertEqual(ack_res.status_code, 200)
            self.assertTrue(ack_res.json()["success"])

            # Verify fault marked resolved in database
            async def check_fault():
                conn = AsyncIOMotorClient(settings.MONGODB_URL)
                db = conn[settings.DATABASE_NAME]
                doc = await db.faults.find_one({"fault_id": "test_asset_123"})
                conn.close()
                return doc

            fault_doc = asyncio.run(check_fault())
            self.assertEqual(fault_doc["status"], "Resolved")
            self.assertIsNotNone(fault_doc.get("resolved_at"))

    def test_dispatch_crew_flow(self):
        """Test POST /dispatch endpoint and verify maintenance ticket is generated."""
        with TestClient(app) as client:
            # Trigger notification
            payload = {
                "title": "Substation Cable Fault",
                "message": "Line fault detected on test_asset_123",
                "type": "fault",
                "screen": "fault_detection",
                "entity_id": "test_asset_123"
            }
            res = client.post("/api/notifications/test", json=payload)
            self.assertEqual(res.status_code, 200)
            notif_id = res.json().get("id") or res.json().get("_id")

            # Call dispatch
            dispatch_res = client.post(f"/api/notifications/{notif_id}/dispatch")
            self.assertEqual(dispatch_res.status_code, 200)
            self.assertTrue(dispatch_res.json()["success"])
            self.assertEqual(dispatch_res.json()["ticket"]["status"], "Dispatched")

            # Verify ticket collection in DB
            async def check_ticket():
                conn = AsyncIOMotorClient(settings.MONGODB_URL)
                db = conn[settings.DATABASE_NAME]
                doc = await db.maintenance_tickets.find_one({"notification_id": notif_id})
                conn.close()
                return doc

            ticket_doc = asyncio.run(check_ticket())
            self.assertIsNotNone(ticket_doc)
            self.assertEqual(ticket_doc["assigned_to"], "Field Crew Delta")
            self.assertEqual(ticket_doc["status"], "Dispatched")

    def test_delete_notification_flow(self):
        """Test DELETE /api/notifications/{id} endpoint."""
        with TestClient(app) as client:
            # 1. Create a notification
            payload = {
                "title": "Voltage Swell Alert",
                "message": "Voltage rose above 250V on test_asset_123",
                "type": "fault",
                "screen": "fault_detection",
                "entity_id": "test_asset_123"
            }
            res = client.post("/api/notifications/test", json=payload)
            self.assertEqual(res.status_code, 200)
            notif_id = res.json().get("id") or res.json().get("_id")

            # 2. Delete the notification
            del_res = client.delete(f"/api/notifications/{notif_id}")
            self.assertEqual(del_res.status_code, 200)
            self.assertTrue(del_res.json()["success"])

            # 3. Verify it is removed from database
            async def find_notif():
                conn = AsyncIOMotorClient(settings.MONGODB_URL)
                db = conn[settings.DATABASE_NAME]
                doc = await db.notifications.find_one({"_id": ObjectId(notif_id)})
                conn.close()
                return doc

            notif_doc = asyncio.run(find_notif())
            self.assertIsNone(notif_doc)

    def test_clear_all_notifications_flow(self):
        """Test DELETE /api/notifications/ clear-all endpoint."""
        with TestClient(app) as client:
            # 1. Create multiple notifications
            payload1 = {
                "title": "Alert 1",
                "message": "Message 1",
                "type": "fault",
                "screen": "fault_detection",
                "entity_id": "test_asset_123"
            }
            payload2 = {
                "title": "Alert 2",
                "message": "Message 2",
                "type": "fault",
                "screen": "fault_detection",
                "entity_id": "test_asset_123"
            }
            client.post("/api/notifications/test", json=payload1)
            client.post("/api/notifications/test", json=payload2)

            # 2. Clear all
            clear_res = client.delete("/api/notifications/")
            self.assertEqual(clear_res.status_code, 200)
            self.assertTrue(clear_res.json()["success"])

            # 3. Verify collection is empty
            async def count_notifications():
                conn = AsyncIOMotorClient(settings.MONGODB_URL)
                db = conn[settings.DATABASE_NAME]
                cnt = await db.notifications.count_documents({})
                conn.close()
                return cnt

            count = asyncio.run(count_notifications())
            self.assertEqual(count, 0)

if __name__ == "__main__":
    unittest.main()
