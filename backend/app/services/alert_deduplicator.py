import os
import httpx
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from ..models.notification import NotificationCreate
from ..core.config import settings
from ..utils.helpers import utcnow

logger = logging.getLogger("powercortex.services.deduplicator")

class AlertDeduplicator:
    @classmethod
    def clean_title(cls, title: str) -> str:
        """Removes duplicate prepended prefixes like 'Grouped Alert:' or 'CRITICAL:'."""
        cleaned = title
        while True:
            prev = cleaned
            # Remove "grouped alert:" prefix case-insensitively
            if cleaned.lower().startswith("grouped alert:"):
                cleaned = cleaned[len("grouped alert:"):].strip()
            # Remove "critical:" prefix case-insensitively
            elif cleaned.lower().startswith("critical:"):
                cleaned = cleaned[len("critical:"):].strip()
            if cleaned == prev:
                break
        return cleaned

    @classmethod
    async def check_and_group(cls, db, new_notif: NotificationCreate) -> Optional[Dict[str, any]]:
        """
        Check recent notifications and group them via LLM if they are part of a cascade.
        Returns a dictionary with grouped 'title', 'message', and 'merged_ids' if grouped, else None.
        """
        # We only deduplicate grid faults or asset alarms
        if new_notif.type not in ["fault", "asset"]:
            return None

        # 1. Fetch recent alerts in the last 2 minutes
        time_threshold = utcnow() - timedelta(minutes=2)
        cursor = db.notifications.find({
            "type": {"$in": ["fault", "asset"]},
            "created_at": {"$gte": time_threshold},
            "is_read": False
        })
        recent_alerts = []
        async for doc in cursor:
            recent_alerts.append({
                "id": str(doc["_id"]),
                "title": doc.get("title", ""),
                "message": doc.get("message", ""),
                "type": doc.get("type", "")
            })

        if not recent_alerts:
            return None

        # 2. Call LLM to see if they cascade
        llm_response = await cls._query_llm(recent_alerts, new_notif)
        if not llm_response or not llm_response.get("cascade"):
            return None

        raw_title = llm_response.get("title", "")
        raw_message = llm_response.get("message", "")

        # Determine if any of the grouped alerts (or the LLM output) is critical
        is_critical = (
            "critical" in raw_title.lower() or 
            "critical" in raw_message.lower() or
            any("critical" in a["title"].lower() or "critical" in a["message"].lower() for a in recent_alerts) or
            "critical" in new_notif.title.lower() or
            "critical" in new_notif.message.lower()
        )

        root_title = cls.clean_title(raw_title)
        grouped_title = f"Grouped Alert: CRITICAL: {root_title}" if is_critical else f"Grouped Alert: {root_title}"

        return {
            "title": grouped_title,
            "message": raw_message,
            "merged_ids": llm_response.get("merged_ids", [])
        }

    @classmethod
    async def _query_llm(cls, recent_alerts: List[Dict], new_notif: NotificationCreate) -> Optional[Dict]:
        """Query LLM (Groq -> Gemini -> Heuristics) using API keys to cluster the alerts."""
        prompt = (
            "You are a critical grid operations AI router. Analyse if the new alert is a secondary cascading consequence of the recent alerts (e.g. substation trip causing secondary sags/voltage alerts).\n\n"
            "Recent Active Alerts:\n"
        )
        for alert in recent_alerts:
            # Clean titles before feeding to LLM to avoid confusing it with existing nested prefixes
            clean_title = cls.clean_title(alert['title'])
            prompt += f"- ID: {alert['id']}, Title: {clean_title}, Message: {alert['message']}\n"
        
        prompt += (
            f"\nNew Alert:\n- Title: {cls.clean_title(new_notif.title)}, Message: {new_notif.message}\n\n"
            "If they are part of a single cascading incident, group them and generate a single unified Title and Summary Message explaining the cascade.\n"
            "If they are not related or do not cascade, set cascade to false.\n\n"
            "Your output must be a strict JSON object with EXACTLY this structure:\n"
            "{\n"
            '  "cascade": true/false,\n'
            '  "title": "A concise title (e.g., Substation X Cascading Outage)",\n'
            '  "message": "A summary explaining the root event and secondary consequences.",\n'
            '  "merged_ids": ["list", "of", "ids", "from", "recent", "alerts", "that", "are", "grouped"]\n'
            "}\n"
            "Respond with ONLY the raw JSON object. Do not include any markdown format (like ```json), commentary, or extra characters."
        )

        # 1. Try Groq (using API Key)
        if settings.GROQ_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 512
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    res = await client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"].strip()
                        if content.startswith("```"):
                            content = content.split("```")[1]
                            if content.startswith("json"):
                                content = content[4:]
                        data = json.loads(content.strip())
                        return data
            except Exception as e:
                logger.error(f"Groq clustering failed: {e}")

        # 2. Try Gemini (using API Key)
        gemini_key = getattr(settings, "GEMINI_API_KEY", None)
        if gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        content = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if content.startswith("```"):
                            content = content.split("```")[1]
                            if content.startswith("json"):
                                content = content[4:]
                        data = json.loads(content.strip())
                        return data
            except Exception as e:
                logger.error(f"Gemini clustering failed: {e}")

        # Heuristic fallback if both AI models fail
        # If any titles contain similar keywords (e.g. Substation name, asset name), group them.
        for alert in recent_alerts:
            clean_old_title = cls.clean_title(alert["title"])
            clean_new_title = cls.clean_title(new_notif.title)
            
            words1 = set(clean_old_title.lower().split())
            words2 = set(clean_new_title.lower().split())
            overlap = words1.intersection(words2) - {"fault", "alert", "error", "substation", "warning", "failure", "risk"}
            if overlap:
                logger.info(f"Heuristics grouping matched: {overlap}")
                
                is_critical = (
                    "critical" in alert["title"].lower() or 
                    "critical" in alert["message"].lower() or
                    "critical" in new_notif.title.lower() or
                    "critical" in new_notif.message.lower()
                )
                
                root_title = clean_old_title
                grouped_title = f"Grouped Alert: CRITICAL: {root_title}" if is_critical else f"Grouped Alert: {root_title}"
                
                # Construct a clean, improved message
                grouped_message = (
                    f"Multiple cascading events detected on {root_title}. "
                    f"Root alert: {new_notif.message if 'temperature' in new_notif.message.lower() else alert['message']}"
                )
                
                return {
                    "cascade": True,
                    "title": grouped_title,
                    "message": grouped_message,
                    "merged_ids": [alert["id"]]
                }

        return {"cascade": False}
