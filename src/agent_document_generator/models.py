"""Data models for A2A protocol and document generation."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class DocumentFormat(str, Enum):
    """Supported document output formats."""
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"


class A2AMessage(BaseModel):
    """A2A Protocol message structure."""
    id: str = Field(..., description="Unique message identifier")
    type: str = Field(..., description="Message type")
    source: str = Field(..., description="Source agent identifier")
    target: str = Field(..., description="Target agent identifier")
    timestamp: str = Field(..., description="ISO timestamp")
    data: Dict[str, Any] = Field(..., description="Message payload")


class UserQuery(BaseModel):
    """User query for document generation."""
    question: str = Field(..., description="User's question or request")
    format: DocumentFormat = Field(default=DocumentFormat.HTML, description="Desired output format")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class DocumentGenerationRequest(BaseModel):
    """Request for document generation."""
    query: UserQuery
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")


class DocumentGenerationResponse(BaseModel):
    """Response containing generated document."""
    content: str = Field(..., description="Generated document content")
    format: DocumentFormat = Field(..., description="Document format")
    title: Optional[str] = Field(default=None, description="Document title")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")
    file_path: Optional[str] = Field(default=None, description="Path to saved file")


class AgentCapabilities(BaseModel):
    """Agent capabilities description."""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    supported_formats: List[DocumentFormat] = Field(..., description="Supported output formats")
    mcp_servers: List[str] = Field(..., description="Available MCP servers")


class HealthStatus(BaseModel):
    """Health status response."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Agent version")
    uptime: float = Field(..., description="Uptime in seconds")
    mcp_status: Dict[str, str] = Field(..., description="MCP servers status")