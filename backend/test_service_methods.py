import os
import sys
import asyncio

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.forecasting_service import ForecastingService
from app.repositories.forecast_repository import ForecastRepository

class MockCollection:
    pass

class MockDB:
    def __init__(self):
        self.forecasts = MockCollection()

async def main():
    print("Initializing forecasting service...")
    db = MockDB()
    repo = ForecastRepository(db)
    service = ForecastingService(repo)
    
    print("Testing get_chart_data()...")
    chart_data = await service.get_chart_data()
    print("Chart data length:", len(chart_data))
    print("First point:", chart_data[0])
    print("Last point:", chart_data[-1])
    
    print("\nTesting get_dashboard_summary()...")
    summary = await service.get_dashboard_summary()
    print("Keys in summary:", list(summary.keys()))
    print("Current demand:", summary["current_demand"])
    print("Next hour:", summary["next_hour"])
    print("Next day peak:", summary["next_day"])
    print("Next week avg:", summary["next_week"])
    print("Peak time:", summary["peak_time"])
    print("Insights:", summary["insights"])

if __name__ == "__main__":
    asyncio.run(main())
