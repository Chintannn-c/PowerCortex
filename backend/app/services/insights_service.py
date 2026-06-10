import logging
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
    CACHE_TTL_SECONDS = 15

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
        
        raw_insights = []

        # 1. Fault Detection Insights (Anomalies)
        try:
            active_faults = await fault_service.get_active_faults(limit=5)
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
            critical_assets = await transformer_service.get_critical_assets()
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
            suspicious_consumers = await theft_service.get_all_suspicious(limit=5)
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
            dashboard_summary = await forecast_service.get_dashboard_summary()
            general_insights = dashboard_summary.get('insights', [])
            
            for index, gi_text in enumerate(general_insights):
                # We'll just fake a slightly staggered timestamp for presentation
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
