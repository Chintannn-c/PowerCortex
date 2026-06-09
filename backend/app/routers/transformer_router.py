from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..core.database import get_database
from ..core.dependencies import get_current_user
from ..repositories.transformer_repository import TransformerRepository
from ..services.transformer_service import TransformerService
from ..services.prediction_service import TransformerPredictionService
from ..schemas.transformer_schema import (
    TransformerPredictRequest,
    TransformerPredictResponse,
    TransformerResponse,
    TransformerDashboardResponse,
    TransformerListResponse
)

router = APIRouter(prefix="/api/v1/transformers", tags=["Transformer Diagnostics"])

def get_transformer_service() -> TransformerService:
    """Dependency injection helper for transformer service."""
    db = get_database()
    repository = TransformerRepository(db)
    return TransformerService(repository)

@router.get("", response_model=TransformerListResponse, summary="Get all transformer assets")
async def get_transformers(
    current_user: dict = Depends(get_current_user),
    service: TransformerService = Depends(get_transformer_service)
):
    """Retrieves all asset telemetry and diagnostics data."""
    try:
        data = await service.get_all_assets()
        # Map ObjectId to string
        mapped_data = []
        for doc in data:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            mapped_data.append(doc_copy)
            
        return {
            "success": True,
            "data": mapped_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assets: {str(e)}"
        )

@router.get("/dashboard", response_model=TransformerDashboardResponse, summary="Get asset status distribution counts")
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    service: TransformerService = Depends(get_transformer_service)
):
    """Returns the count of healthy, warning, and critical assets."""
    try:
        return await service.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard summary: {str(e)}"
        )

@router.get("/critical", response_model=TransformerListResponse, summary="Get critical assets only")
async def get_critical_assets(
    current_user: dict = Depends(get_current_user),
    service: TransformerService = Depends(get_transformer_service)
):
    """Retrieves assets currently flagged with Critical status."""
    try:
        data = await service.get_critical_assets()
        mapped_data = []
        for doc in data:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            mapped_data.append(doc_copy)
            
        return {
            "success": True,
            "data": mapped_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving critical assets: {str(e)}"
        )

@router.get("/warning", response_model=TransformerListResponse, summary="Get warning assets only")
async def get_warning_assets(
    current_user: dict = Depends(get_current_user),
    service: TransformerService = Depends(get_transformer_service)
):
    """Retrieves assets currently flagged with Warning status."""
    try:
        data = await service.get_warning_assets()
        mapped_data = []
        for doc in data:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            mapped_data.append(doc_copy)
            
        return {
            "success": True,
            "data": mapped_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving warning assets: {str(e)}"
        )

@router.get("/{id}", response_model=TransformerResponse, summary="Get asset details by ID")
async def get_transformer_details(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: TransformerService = Depends(get_transformer_service)
):
    """Fetch telemetry and diagnostic details for a specific transformer asset."""
    try:
        doc = await service.get_asset_by_id(id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with ID '{id}' not found."
            )
        doc["_id"] = str(doc["_id"])
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving asset details: {str(e)}"
        )

@router.post("/predict", response_model=TransformerPredictResponse, summary="Predict health stats from telemetry")
async def predict_telemetry(
    body: TransformerPredictRequest,
    current_user: dict = Depends(get_current_user)
):
    """Evaluates telemetry inputs and predicts health score, risk, and status using the trained Random Forest model."""
    try:
        result = TransformerPredictionService.run_inference(
            temperature=body.temperature,
            voltage=body.voltage,
            current=body.current,
            oil_level=body.oil_level,
            load_percentage=body.load_percentage
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running model prediction: {str(e)}"
        )

@router.post("/{id}/telemetry", response_model=TransformerResponse, summary="Upload new telemetry and trigger live re-prediction")
async def update_telemetry_prediction(
    id: str,
    body: TransformerPredictRequest,
    current_user: dict = Depends(get_current_user),
    service: TransformerService = Depends(get_transformer_service)
):
    """Receives live telemetry for a transformer, executes RF prediction, saves it to database, and returns updated document."""
    try:
        updated_doc = await service.predict_and_save_telemetry(id, body.model_dump())
        if not updated_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with ID '{id}' not found."
            )
        return updated_doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating telemetry: {str(e)}"
        )
