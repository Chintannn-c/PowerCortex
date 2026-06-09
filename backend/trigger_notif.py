import asyncio
import sys
import os
import httpx

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.notification import NotificationCreate
from app.services.notification_service import NotificationService
from app.core.database import connect_to_mongo, close_mongo_connection

async def main():
    # Construct a critical priority grid alert
    notif = NotificationCreate(
        title="CRITICAL: Substation Delta Transformer Failure Risk",
        message="Transformer oil temperature has reached 112°C with high risk of explosion. Immediate dispatch required.",
        type="fault",
        screen="fault_detection",
        entity_id="FLT-001"
    )
    
    print("Triggering critical notification...")
    
    # Try sending via HTTP POST to uvicorn server so it triggers WebSocket broadcasts to the app
    sent_via_http = False
    res_id, res_title, res_message, res_type = "", "", "", ""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8000/api/notifications/test",
                json={
                    "title": notif.title,
                    "message": notif.message,
                    "type": notif.type,
                    "screen": notif.screen,
                    "entity_id": notif.entity_id
                },
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                res_id = data.get("id") or data.get("_id")
                res_title = data.get("title")
                res_message = data.get("message")
                res_type = data.get("type")
                sent_via_http = True
                print("Successfully triggered alert via HTTP POST to FastAPI server.")
    except Exception as http_err:
        print(f"FastAPI server not reachable via HTTP ({http_err}). Falling back to local database invocation...")

    if not sent_via_http:
        await connect_to_mongo()
        res = await NotificationService.create_and_send_notification(notif)
        res_id = res.id
        res_title = res.title
        res_message = res.message
        res_type = res.type
        await close_mongo_connection()
    
    print("\nNotification sent successfully!")
    print(f"Result ID: {res_id}")
    print(f"Result Title: {res_title}")
    print(f"Result Message: {res_message}")
    print(f"Result Type: {res_type}")

if __name__ == "__main__":
    asyncio.run(main())
