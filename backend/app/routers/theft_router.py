from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..core.database import get_database
from ..core.dependencies import get_current_user
from ..repositories.theft_repository import TheftRepository
from ..services.theft_service import TheftDetectionService
from ..schemas.theft_schema import (
    TheftPredictRequest,
    TheftPredictResponse,
    TheftSuspiciousItem,
    TheftDashboardResponse,
    ConsumerInvestigationResponse,
    TheftDistributionItem,
    TheftTrendPoint
)

router = APIRouter(prefix="/api/v1/theft", tags=["Theft Detection"])

def get_theft_service() -> TheftDetectionService:
    """Dependency injection helper for theft service."""
    db = get_database()
    repository = TheftRepository(db)
    return TheftDetectionService(repository)

@router.post("/predict", response_model=TheftPredictResponse, summary="Run theft prediction")
async def predict_theft(
    body: TheftPredictRequest,
    current_user: dict = Depends(get_current_user),
    service: TheftDetectionService = Depends(get_theft_service)
):
    """Run model prediction on current telemetry and automatically log alerts."""
    try:
        result = await service.predict_and_save_theft(
            consumer_id=body.consumer_id,
            current_consumption=body.current_consumption,
            avg_consumption=body.avg_consumption,
            power_factor=body.power_factor
        )
        return {
            "success": True,
            "data": {
                "consumer_id": result["consumer_id"],
                "theft_probability": result["theft_probability"],
                "risk_level": result["risk_level"],
                "deviation_percentage": result["deviation_percentage"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running theft prediction: {str(e)}"
        )

@router.get("/suspicious", response_model=List[TheftSuspiciousItem], summary="Get suspicious consumers list")
async def get_suspicious(
    current_user: dict = Depends(get_current_user),
    service: TheftDetectionService = Depends(get_theft_service)
):
    """Retrieve all suspicious consumers sorted by probability descending."""
    try:
        alerts = await service.get_all_suspicious()
        mapped = []
        for a in alerts:
            mapped.append({
                "consumer_id": a["consumer_id"],
                "risk_level": a["risk_level"],
                "theft_probability": a["theft_probability"],
                "sector": a.get("sector"),
                "city": a.get("city"),
                "deviation_percentage": a.get("deviation_percentage")
            })
        return mapped
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving suspicious list: {str(e)}"
        )

@router.get("/dashboard", response_model=TheftDashboardResponse, summary="Get theft dashboard summary stats")
async def get_dashboard(
    current_user: dict = Depends(get_current_user),
    service: TheftDetectionService = Depends(get_theft_service)
):
    """Retrieve dashboard summary counts (suspicious, high-risk, resolved) and average probability."""
    try:
        return await service.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard summary: {str(e)}"
        )

@router.get("/consumer/{consumer_id}", response_model=ConsumerInvestigationResponse, summary="Get consumer investigation profile details")
async def get_consumer(
    consumer_id: str,
    current_user: dict = Depends(get_current_user),
    service: TheftDetectionService = Depends(get_theft_service)
):
    """Fetch all telemetry history and AI classification notes for consumer investigation."""
    try:
        res = await service.get_consumer_investigation(consumer_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consumer profile '{consumer_id}' not found."
            )
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving consumer details: {str(e)}"
        )

@router.get("/distribution", response_model=List[TheftDistributionItem], summary="Get risk distribution counts")
async def get_distribution(
    current_user: dict = Depends(get_current_user),
    service: TheftDetectionService = Depends(get_theft_service)
):
    """Fetch count statistics for risk distribution pie charts."""
    try:
        return await service.get_risk_distribution()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving risk distribution: {str(e)}"
        )

@router.get("/trend/{consumer_id}", response_model=List[TheftTrendPoint], summary="Get monthly consumption trend history")
async def get_trend(
    consumer_id: str,
    current_user: dict = Depends(get_current_user),
    service: TheftDetectionService = Depends(get_theft_service)
):
    """Retrieve actual vs expected consumption history trend points."""
    try:
        res = await service.get_consumer_investigation(consumer_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consumer '{consumer_id}' not found."
            )
        # Generate 5 trend points corresponding to monthly_usage
        months = ["Jan", "Feb", "Mar", "Apr", "May"]
        usage = res["monthly_usage"]
        avg = res["avg_consumption"]
        
        # Ensure we have at least 5 values in monthly_usage, otherwise fill/truncate
        while len(usage) < 5:
            usage.insert(0, avg)
        usage = usage[-5:]
        
        trend = []
        for idx, month in enumerate(months):
            # Expected usage is centered close to average consumption with a slight seasonal deviation
            expected = avg + (10 if idx % 2 == 0 else -15)
            trend.append({
                "month": month,
                "actual": float(usage[idx]),
                "expected": float(round(expected, 1))
            })
        return trend
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving trend points: {str(e)}"
        )
