import logging
import asyncio
from typing import List, Dict
from datetime import datetime

from ..core.database import get_database
from ..repositories.fault_repository import FaultRepository
from ..services.fault_service import FaultDetectionService
from ..repositories.theft_repository import TheftRepository
from ..services.theft_service import TheftDetectionService
from ..repositories.transformer_repository import TransformerRepository
from ..services.transformer_service import TransformerService
from ..repositories.forecast_repository import ForecastRepository
from ..services.forecasting_service import ForecastingService

import time

logger = logging.getLogger("powercortex.services.insights")

class InsightsService:
    """Service to aggregate AI Insights from all ML modules into a unified stream."""
    
    _cache = {
        "data": [],
        "timestamp": 0
    }
    CACHE_TTL_SECONDS = 60

    @classmethod
    async def get_aggregated_insights(cls) -> List[Dict]:
        current_time = time.time()
        if current_time - cls._cache["timestamp"] < cls.CACHE_TTL_SECONDS and cls._cache["data"]:
            return cls._cache["data"]

        db = get_database()
        
        # Initialize repositories and services
        fault_service = FaultDetectionService(FaultRepository(db))
        theft_service = TheftDetectionService(TheftRepository(db))
        transformer_service = TransformerService(TransformerRepository(db))
        forecast_service = ForecastingService(ForecastRepository(db))
        
        # Run tasks concurrently to avoid sequential latency accumulation
        try:
            results = await asyncio.gather(
                fault_service.get_active_faults(limit=5),
                transformer_service.get_critical_assets(),
                theft_service.get_all_suspicious(limit=5),
                forecast_service.get_dashboard_summary(),
                return_exceptions=True
            )
        except Exception as gather_err:
            logger.error(f"Error in asyncio.gather for insights: {gather_err}")
            results = [[], [], [], {}]

        active_faults = results[0] if len(results) > 0 and not isinstance(results[0], Exception) else []
        critical_assets = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else []
        suspicious_consumers = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []
        dashboard_summary = results[3] if len(results) > 3 and not isinstance(results[3], Exception) else {}

        # Log exceptions if any occurred in the gather list
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Insight component task {idx} failed with: {res}")
        
        raw_insights = []

        # 1. Fault Detection Insights (Anomalies)
        try:
            for fault in active_faults:
                severity = fault.get('severity', 'High')
                fault_type = fault.get('fault_type', 'Unknown Fault')
                asset_name = fault.get('asset_name', 'Unknown Asset')
                fault_id = fault.get('fault_id', '')
                prob = fault.get('probability', 0.0)
                dt = fault.get('detected_at', datetime.now())
                
                text = f"{severity} priority: {fault_type} detected on {asset_name} ({fault_id}). Model confidence is {prob:.1f}%."
                
                raw_insights.append({
                    "text": text,
                    "type": "Anomaly Alert",
                    "timestamp": dt,
                    "source": "Fault Detection Engine"
                })
        except Exception as e:
            logger.error(f"Error fetching faults for insights: {e}")

        # 2. Transformer Diagnostics Insights (Equipment)
        try:
            for asset in critical_assets[:5]:  # limit to 5
                asset_id = asset.get('asset_id', '')
                failure_prob = asset.get('failure_probability', 0.0)
                dt = asset.get('last_updated', datetime.now())
                
                text = f"Critical equipment warning: Asset {asset_id} has a {failure_prob:.1f}% probability of failure. Maintenance recommended immediately."
                
                raw_insights.append({
                    "text": text,
                    "type": "Equipment Warning",
                    "timestamp": dt,
                    "source": "Transformer AI"
                })
        except Exception as e:
            logger.error(f"Error fetching transformers for insights: {e}")

        # 3. Theft Detection Insights (Revenue Risk)
        try:
            for consumer in suspicious_consumers:
                consumer_id = consumer.get('consumer_id', '')
                prob = consumer.get('theft_probability', 0.0)
                dt = consumer.get('created_at', datetime.now())
                
                text = f"Revenue protection: Potential theft case active. Check consumer {consumer_id} with bypass probability {prob:.0f}%."
                
                raw_insights.append({
                    "text": text,
                    "type": "Revenue Risk",
                    "timestamp": dt,
                    "source": "Theft Detection Engine"
                })
        except Exception as e:
            logger.error(f"Error fetching thefts for insights: {e}")

        # 4. General Forecasting / Weather Insights
        try:
            general_insights = dashboard_summary.get('insights', [])
            
            for index, gi_text in enumerate(general_insights):
                # Use current system time for the live dashboard stream
                dt = datetime.now()
                
                raw_insights.append({
                    "text": gi_text,
                    "type": "Weather Impact" if "temperature" in gi_text.lower() else "System Forecast",
                    "timestamp": dt,
                    "source": "Predictive Models"
                })
        except Exception as e:
            logger.error(f"Error fetching forecasts for insights: {e}")

        # Sort by timestamp descending
        raw_insights.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Serialize datetime objects to ISO strings
        for insight in raw_insights:
            if isinstance(insight["timestamp"], datetime):
                insight["timestamp"] = insight["timestamp"].isoformat()

        cls._cache["data"] = raw_insights
        cls._cache["timestamp"] = time.time()

        return raw_insights
