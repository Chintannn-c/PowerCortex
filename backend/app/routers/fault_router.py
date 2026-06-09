from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..core.database import get_database
from ..core.dependencies import get_current_user
from ..repositories.fault_repository import FaultRepository
from ..services.fault_service import FaultDetectionService
from ..schemas.fault_schema import (
    FaultPredictRequest,
    FaultPredictResponse,
    FaultResponse,
    FaultDashboardResponse,
    FaultAnomaliesResponse,
    FaultTimelineItem,
    FaultListResponse
)

router = APIRouter(prefix="/api/v1/faults", tags=["Fault Detection"])

def get_fault_service() -> FaultDetectionService:
    """Dependency injection helper for fault service."""
    db = get_database()
    repository = FaultRepository(db)
    return FaultDetectionService(repository)

@router.get("", response_model=FaultListResponse, summary="Get all faults")
async def get_all_faults(
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Retrieve all logged faults."""
    try:
        data = await service.get_all_faults()
        mapped_data = []
        for doc in data:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            mapped_data.append(doc_copy)
            
        return {"success": True, "data": mapped_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving faults: {str(e)}"
        )

@router.get("/active", response_model=FaultListResponse, summary="Get active faults")
async def get_active_faults(
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Retrieve active faults currently on the grid."""
    try:
        data = await service.get_active_faults()
        mapped_data = []
        for doc in data:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            mapped_data.append(doc_copy)
            
        return {"success": True, "data": mapped_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving active faults: {str(e)}"
        )

@router.get("/history", response_model=FaultListResponse, summary="Get historical resolved faults")
async def get_historical_faults(
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Retrieve historical resolved faults."""
    try:
        data = await service.get_historical_faults()
        mapped_data = []
        for doc in data:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            mapped_data.append(doc_copy)
            
        return {"success": True, "data": mapped_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving historical faults: {str(e)}"
        )

@router.get("/dashboard", response_model=FaultDashboardResponse, summary="Get dashboard summary stats")
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Retrieve summary counts (active, resolved, severities) for dashboard widgets."""
    try:
        return await service.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard summary: {str(e)}"
        )

@router.get("/anomalies", response_model=FaultAnomaliesResponse, summary="Get anomalies list")
async def get_anomalies(
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Retrieve anomaly dashboard representation."""
    try:
        summary = await service.get_dashboard_summary()
        active_list = await service.get_active_faults()
        
        mapped_faults = []
        for f in active_list:
            mapped_faults.append({
                "fault_type": f["fault_type"],
                "asset_name": f["asset_name"],
                "severity": f["severity"],
                "probability": f["probability"]
            })
            
        return {
            "active_faults": summary["active_faults"],
            "resolved_today": summary["resolved_today"],
            "faults": mapped_faults
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving anomalies: {str(e)}"
        )

@router.get("/timeline", response_model=List[FaultTimelineItem], summary="Get timeline statistics")
async def get_timeline(
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Retrieve fault frequency timeline data grouped by date."""
    try:
        return await service.get_timeline_data()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving timeline data: {str(e)}"
        )

@router.get("/{id}", response_model=FaultResponse, summary="Get fault details by ID")
async def get_fault_details(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Fetch details for a specific fault by ID or fault_id."""
    try:
        doc = await service.get_fault_by_id(id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fault with ID '{id}' not found."
            )
        doc["_id"] = str(doc["_id"])
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving fault details: {str(e)}"
        )

@router.post("/predict", response_model=FaultPredictResponse, summary="Run fault prediction")
async def predict_fault(
    body: FaultPredictRequest,
    current_user: dict = Depends(get_current_user),
    service: FaultDetectionService = Depends(get_fault_service)
):
    """Run model prediction on current telemetry and automatically log faults."""
    try:
        result = await service.predict_and_save_fault(
            voltage=body.voltage,
            current=body.current,
            frequency=body.frequency,
            asset_name=body.asset_name
        )
        return {
            "fault_type": result["fault_type"],
            "severity": result["severity"],
            "probability": result["probability"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting fault: {str(e)}"
        )
