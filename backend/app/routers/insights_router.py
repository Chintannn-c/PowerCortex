from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Any
import asyncio
from ..core.dependencies import get_current_user
from ..core.security import decode_access_token
from ..services.insights_service import InsightsService

router = APIRouter(prefix="/api/v1/insights", tags=["AI Insights"])

@router.get("", response_model=Dict[str, Any], summary="Get aggregated AI Insights")
async def get_insights(current_user: dict = Depends(get_current_user)):
    """Retrieve an aggregated stream of AI insights from all predictive models."""
    try:
        data = await InsightsService.get_aggregated_insights()
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving insights: {str(e)}"
        )

@router.websocket("/ws")
async def websocket_insights(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for real-time live insights streaming.
    Authenticates via JWT token query parameter.
    Pushes cached insights to the client every 15 seconds.
    """
    # 1. Authenticate Token
    payload = decode_access_token(token)
    if payload is None or payload.get("sub") is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await websocket.accept()
    try:
        while True:
            # InsightsService uses an internal 15s cache, so calling this in a loop
            # is extremely cheap and won't hit the DB constantly.
            data = await InsightsService.get_aggregated_insights()
            await websocket.send_json({"success": True, "data": data})
            # Sleep for 15 seconds before pushing again
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Unexpected error
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
