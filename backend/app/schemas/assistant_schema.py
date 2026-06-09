from pydantic import BaseModel
from typing import List, Optional, Dict

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class AssistantChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class AssistantChatResponse(BaseModel):
    success: bool
    reply: str
    confidence: float

class SmartSearchRequest(BaseModel):
    query: str

class SmartSearchResponse(BaseModel):
    success: bool
    intent: str  # "filter" or "answer"
    tab: Optional[int] = None
    query: Optional[str] = None
    text: Optional[str] = None

