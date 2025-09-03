"""Base toolset interface inspired by Google ADK BaseToolset."""

from abc import ABC, abstractmethod
from typing import Any

from ..models import ToolExecutionResult


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(
        self, name: str, description: str, schema: dict[str, Any] | None = None
    ):
        self.name = name
        self.description = description
        self.schema = schema or {}

    @abstractmethod
    async def run(self, arguments: dict[str, Any]) -> ToolExecutionResult:
        """Execute the tool with given arguments."""
        pass


class BaseToolset(ABC):
    """Base interface for toolsets, inspired by Google ADK BaseToolset."""

    def __init__(self, tool_filter: list[str] | None = None):
        """Initialize toolset with optional tool filter."""
        self.tool_filter = tool_filter or []
        self._is_initialized = False
        self._tools_cache: list[BaseTool] = []

    @abstractmethod
    async def get_tools(self) -> list[BaseTool]:
        """Get available tools from the toolset."""
        pass

    async def initialize(self) -> bool:
        """Initialize the toolset."""
        if self._is_initialized:
            return True

        try:
            tools = await self.get_tools()
            self._tools_cache = self._apply_tool_filter(tools)
            self._is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize toolset {self.__class__.__name__}: {e}")
            return False

    def _apply_tool_filter(self, tools: list[BaseTool]) -> list[BaseTool]:
        """Apply tool filter if specified."""
        if not self.tool_filter:
            return tools

        return [tool for tool in tools if tool.name in self.tool_filter]

    async def close(self) -> None:
        """Close the toolset and release resources."""
        self._is_initialized = False
        self._tools_cache = []

    def is_initialized(self) -> bool:
        """Check if toolset is initialized."""
        return self._is_initialized

    def get_cached_tools(self) -> list[BaseTool]:
        """Get cached tools without re-initialization."""
        return self._tools_cache.copy()
