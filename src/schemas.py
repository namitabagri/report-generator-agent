from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, TypedDict
from datetime import datetime

#Document Chunk Schema
class DocumentChunk(BaseModel):
    """Represents a chunk of document content"""
    doc_id: str = Field(description="Document Identifier")
    content:str = Field(description="The actual text content.")
    metadata: Dict[str, Any] = Field(default_factory=lambda:{}, description="Additional metadata")
    relevance_Score: float = Field(default=0.0, description="Relevance score for retrieval")

#QA Schema
class AnswerResponse(BaseModel):
    """Structured Q/A responses"""
    question: str = Field(description="The original user question")
    answer: str = Field(description="The generated answer")
    sources: List[str] = Field(description="List of source document IDs used")
    confidence: float = Field(description="Confidence score between 0 and 1")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the response was generated")

#Summarization Schema
class SummarizationResponse(BaseModel):
    """Structured response for summarization response"""
    original_length: int = Field(description="Length of original text")
    summary: str = Field(description="The generated summary")
    key_points: List[str] = Field(description="List of key points extracted")
    document_ids: List[str] = Field(default_factory=lambda:[], description="Documents summarized")
    timestamp: datetime = Field(default_factory=datetime.now, description="The time")

#Calculation Schema
class CalculatorResponse(BaseModel):
    """Structured response for calculation task"""
    expression: str = Field(description="Mathematical expression")
    result: float = Field(decription="The calculated result")
    explanation: str = Field(description="The explanation")
    units: Optional[str] = Field(default=None, description="Units is applicable")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time")

# Conversation History Schema
class UpdateMemoryResponse(BaseModel):
    """Response after updating memory"""
    summary: str = Field(description="Summary of the conversation up to this point")
    document_ids: List[str] = Field(default_factory=lambda:[], description="List of document IDs that are relevant to the users last message")

#User Intent Classification Schema
class UserIntent(BaseModel):
    """Intent Classification to help the system understand the user's request type and route it to the appropriate agent"""
    intent_type: str = Field(description="The classification intent")
    confidence: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Explanation for the intent classification")

#Session State Schema
class SessionState(BaseModel):
    """Session State"""
    session_id: str = Field(description="ID of the session")
    user_id: str = Field(description="ID of User")
    conversation_history: List[Dict] = Field(default_factory=lambda:[], description="Conversation History")
    document_context: List[str] = Field(default_factory=lambda:[], description="Active document ID")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)