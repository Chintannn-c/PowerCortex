from fastapi import APIRouter, Depends, HTTPException, status
from ..core.database import get_database
from ..core.dependencies import get_current_user
from ..services.assistant_service import AssistantService
from ..schemas.assistant_schema import AssistantChatRequest, AssistantChatResponse, SmartSearchRequest, SmartSearchResponse

router = APIRouter(prefix="/api/v1/assistant", tags=["AI Assistant"])

def get_assistant_service() -> AssistantService:
    db = get_database()
    return AssistantService(db)

@router.post("/chat", response_model=AssistantChatResponse, summary="Send message to AI assistant")
async def chat_with_assistant(
    body: AssistantChatRequest,
    current_user: dict = Depends(get_current_user),
    service: AssistantService = Depends(get_assistant_service)
):
    try:
        res = await service.generate_response(body.message, body.history, user=current_user)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat response: {str(e)}"
        )

@router.post("/search", response_model=SmartSearchResponse, summary="Process smart search query using AI or heuristics")
async def smart_search(
    body: SmartSearchRequest,
    current_user: dict = Depends(get_current_user),
    service: AssistantService = Depends(get_assistant_service)
):
    try:
        res = await service.parse_smart_search(body.query)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing smart search: {str(e)}"
        )

