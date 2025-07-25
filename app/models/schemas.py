from pydantic import BaseModel, Field
from typing import Optional, Dict
from enum import Enum
import time


class ResponseCategory(str, Enum):
    """Response categories for non-FAQ responses."""
    DATABASE_STATS = "database_stats"
    OUT_OF_SCOPE = "out_of_scope"


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    category: str  # Changed from ResponseCategory to str to support dynamic FAQ categories
    conversation_id: str
    processing_time: float


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    error_code: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class FunctionCallRequest(BaseModel):
    function_name: str
    arguments: Dict


class DatabaseStatsResponse(BaseModel):
    count: int
    details: Optional[Dict] = None
    
    
class OrganismSearchResponse(BaseModel):
    found: bool
    organism_data: Optional[Dict] = None 