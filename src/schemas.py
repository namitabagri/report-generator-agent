from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, TypedDict
from datetime import datetime

class DocumentChunk(BaseModel):
    """Represents a chunk of document content"""
    doc_id: str = Field(description="Document Identifier")
    content:str = Field(description="The actual text content.")
    metadata: Dict[str, Any] = Field(default_factory=lambda:{}, description="Additional metadata")