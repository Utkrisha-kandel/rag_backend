import uuid
from datetime import datetime,date,time
from pydantic import BaseModel, Field
from typing import Literal

# Ingestion response schema
class IngestResponse(BaseModel):
    document_id: str = Field(alias="id")
    filename: str
    chunk_strategy: Literal["fixed", "sentence"]
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}

#chat
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique identifier for the chat session"),
    message: str = Field(..., description="The content of the chat message"),
    document_id: str|None = Field(None, description="The ID of the document associated with the message")

class SourceChunk(BaseModel):
    document_id: str
    filename:str
    chunk_index: int
    score: float
    text: str

class ChatResponse(BaseModel):
    session_id:str
    answer: str
    sources: list[SourceChunk]
    booking: "BookingResponse | None" = None

class ClearHistoryResponse(BaseModel):
    session_id: str
    cleared: bool 
    
class BookingResponse(BaseModel):
    id:str
    session_id:str
    name:str
    email:str
    interview_date:date
    interview_time:time
    created_at:datetime
    notes:str|None 

    model_config = {"from_attributes": True}


    
