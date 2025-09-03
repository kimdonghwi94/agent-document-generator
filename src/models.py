"""Data models for A2A protocol and document generation."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentFormat(str, Enum):
    """Supported document output formats."""

    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"


class ActionType(str, Enum):
    """ReAct action types."""

    THINK = "think"
    USE_TOOL = "use_tool"
    FINISH = "finish"


class A2AMessage(BaseModel):
    """A2A Protocol message structure."""

    id: str = Field(..., description="Unique message identifier")
    type: str = Field(..., description="Message type")
    source: str = Field(..., description="Source agent identifier")
    target: str = Field(..., description="Target agent identifier")
    timestamp: str = Field(..., description="ISO timestamp")
    data: dict[str, Any] = Field(..., description="Message payload")


class ConversationMessage(BaseModel):
    """A message in the conversation history."""

    role: str = Field(description="Message role (user/assistant/system)")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Message timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional message metadata"
    )


class ConversationContext(BaseModel):
    """Conversation context with message history."""

    messages: list[ConversationMessage] = Field(
        default_factory=list, description="Message history"
    )
    session_id: str | None = Field(None, description="Session identifier")
    max_history: int = Field(
        default=20, description="Maximum number of messages to keep"
    )

    def add_message(
        self, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a message to the context."""
        message = ConversationMessage(
            role=role, content=content, metadata=metadata or {}
        )
        self.messages.append(message)

        # Keep only recent messages to prevent token overflow
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history :]

    def get_openai_messages(
        self, system_prompt: str | None = None
    ) -> list[dict[str, str]]:
        """Convert to OpenAI API message format."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for msg in self.messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()


class ReActAction(BaseModel):
    """ReAct agent action."""

    action: ActionType = Field(description="Type of action to take")
    reasoning: str = Field(description="Reasoning behind the action")
    tool: str | None = Field(None, description="Tool to use (if USE_TOOL)")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the tool"
    )
    result: str | None = Field(None, description="Final result (if FINISH)")


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""

    success: bool = Field(description="Whether the tool executed successfully")
    result: Any = Field(description="The result of the tool execution")
    error: str | None = Field(None, description="Error message if execution failed")
    execution_time: float | None = Field(
        None, description="Time taken to execute in seconds"
    )
    tool_name: str | None = Field(
        None, description="Name of the tool that was executed"
    )


class UserQuery(BaseModel):
    """User query for document generation."""

    question: str = Field(..., description="User's question or request")
    format: DocumentFormat = Field(
        default=DocumentFormat.HTML, description="Desired output format"
    )
    context: ConversationContext | None = Field(
        default=None, description="Conversation context"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class DocumentGenerationRequest(BaseModel):
    """Request for document generation."""

    query: UserQuery
    session_id: str | None = Field(default=None, description="Session identifier")
    user_id: str | None = Field(default=None, description="User identifier")


class DocumentGenerationResponse(BaseModel):
    """Response containing generated document."""

    content: str = Field(..., description="Generated document content")
    format: DocumentFormat = Field(..., description="Document format")
    title: str | None = Field(default=None, description="Document title")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Document metadata"
    )
    file_path: str | None = Field(default=None, description="Path to saved file")


class AgentCapabilities(BaseModel):
    """Agent capabilities description."""

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    supported_formats: list[DocumentFormat] = Field(
        ..., description="Supported output formats"
    )
    mcp_servers: list[str] = Field(..., description="Available MCP servers")


class HealthStatus(BaseModel):
    """Health status response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Agent version")
    uptime: float = Field(..., description="Uptime in seconds")
    mcp_status: dict[str, str] = Field(..., description="MCP servers status")


class AgentProcessingResult(BaseModel):
    """Result of agent processing."""

    success: bool = Field(description="Whether processing was successful")
    response: str | DocumentGenerationResponse = Field(
        description="Agent response"
    )
    action_taken: ActionType | None = Field(
        None, description="Final action taken by agent"
    )
    tools_used: list[str] = Field(
        default_factory=list, description="List of tools used"
    )
    processing_time: float | None = Field(None, description="Total processing time")
    iterations_used: int = Field(
        default=0, description="Number of ReAct iterations used"
    )
    context: ConversationContext = Field(description="Updated conversation context")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
