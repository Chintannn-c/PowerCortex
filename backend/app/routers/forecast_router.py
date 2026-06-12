from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from ..core.database import get_database
from ..core.dependencies import get_current_user
from ..repositories.forecast_repository import ForecastRepository
from ..services.forecasting_service import ForecastingService
from ..schemas.forecast_schema import (
    ForecastResponse, 
    ForecastInfo, 
    ForecastListResponse, 
    ChartDataResponse, 
    DashboardSummaryResponse,
    ForecastGenerateRequest
)

router = APIRouter(prefix="/api/v1/forecast", tags=["Forecasting"])

def get_forecasting_service() -> ForecastingService:
    """Dependency injection helper for forecasting service."""
    db = get_database()
    repository = ForecastRepository(db)
    return ForecastingService(repository)

@router.get(
    "/hour", 
    response_model=ForecastResponse, 
    summary="Get next hour electricity demand forecast",
    responses={
        200: {
            "description": "Successful retrieval of hourly forecast",
            "content": {
                "application/json": {
                    "example": {"success": True, "forecast": {"predicted_demand": 42000, "unit": "MW", "confidence": 96.4}}
                }
            }
        },
        500: {"description": "Internal Server Error"}
    }
)
async def get_hourly_forecast(
    current_user: dict = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service)
):
    """
    Returns the next hour's electricity demand forecast (MW) and model confidence.
    """
    try:
        data = await service.get_latest_forecast("hourly")
        return {
            "success": True,
            "forecast": {
                "predicted_demand": data["predicted_demand"],
                "unit": "MW",
                "confidence": data["confidence"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Error retrieving hourly forecast: {str(e)}"}
        )

@router.get(
    "/day", 
    response_model=ForecastResponse, 
    summary="Get tomorrow peak demand forecast",
    responses={
        200: {
            "description": "Successful retrieval of daily forecast",
            "content": {
                "application/json": {
                    "example": {"success": True, "forecast": {"predicted_demand": 44500, "unit": "MW", "confidence": 94.2}}
                }
            }
        }
    }
)
async def get_daily_forecast(
    current_user: dict = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service)
):
    """
    Returns tomorrow's peak demand forecast (MW) and model confidence.
    """
    try:
        data = await service.get_latest_forecast("daily")
        return {
            "success": True,
            "forecast": {
                "predicted_demand": data["predicted_demand"],
                "unit": "MW",
                "confidence": data["confidence"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Error retrieving daily forecast: {str(e)}"}
        )

@router.get(
    "/week", 
    response_model=ForecastResponse, 
    summary="Get next week average demand forecast",
    responses={
        200: {
            "description": "Successful retrieval of weekly forecast",
            "content": {
                "application/json": {
                    "example": {"success": True, "forecast": {"predicted_demand": 41200, "unit": "MW", "confidence": 89.5}}
                }
            }
        }
    }
)
async def get_weekly_forecast(
    current_user: dict = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service)
):
    """
    Returns next week's average demand forecast (MW) and model confidence.
    """
    try:
        data = await service.get_latest_forecast("weekly")
        return {
            "success": True,
            "forecast": {
                "predicted_demand": data["predicted_demand"],
                "unit": "MW",
                "confidence": data["confidence"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Error retrieving weekly forecast: {str(e)}"}
        )

@router.post(
    "/generate", 
    summary="Manually trigger new forecast generation run",
    responses={
        200: {
            "description": "Forecast successfully generated",
            "content": {
                "application/json": {
                    "example": {"success": True, "message": "Hourly forecast generated and saved.", "data": {"predicted_demand": 42100}}
                }
            }
        }
    }
)
async def generate_new_forecast(
    body: ForecastGenerateRequest,
    current_user: dict = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service)
):
    """
    Manually triggers weather retrieval, feature engineering, and predictive calculations.
    Saves the forecast run into MongoDB.
    """
    try:
        data = await service.generate_and_save_forecast(body.forecast_type)
        return {
            "success": True,
            "message": f"{body.forecast_type.capitalize()} forecast generated and saved.",
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Error generating forecast: {str(e)}"}
        )

@router.get("/history", response_model=ForecastListResponse, summary="Get historical forecast runs")
async def get_historical_runs(
    forecast_type: Optional[str] = Query(None, description="Filter by type (hourly, daily, weekly)"),
    limit: int = Query(20, description="Max records to return"),
    current_user: dict = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service)
):
    """
    Retrieves previous forecasting runs and details.
    """
    try:
        data = await service.get_forecast_history(forecast_type=forecast_type, limit=limit)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Error retrieving forecast history: {str(e)}"}
        )

@router.get("/chart", response_model=ChartDataResponse, summary="Get chart-ready actual vs predicted demand")
async def get_chart_points(
    current_user: dict = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service)
):
    """
    Returns actual vs predicted electricity demand data formatted for charting.
    """
    try:
        data = await service.get_chart_data()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Error retrieving chart data: {str(e)}"}
        )


@router.get("/dashboard", response_model=DashboardSummaryResponse, summary="Get forecasting metrics for dashboard cards")
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user),
    service: ForecastingService = Depends(get_forecasting_service)
):
    """
    Returns aggregated metrics for main dashboard widgets (KPIs, peak forecasts, renewable metrics, AI insights).
    """
    try:
        data = await service.get_dashboard_summary()
        return {
            "success": True,
            **data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Error retrieving dashboard metrics: {str(e)}"}
        )
