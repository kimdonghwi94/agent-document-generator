"""Function-based toolset for direct agent tools."""

import asyncio
import time
from collections.abc import Callable
from typing import Any

from ..models import ToolExecutionResult
from .base_toolset import BaseTool, BaseToolset


class FunctionTool(BaseTool):
    """A tool that wraps a Python function."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        schema: dict[str, Any] | None = None,
    ):
        super().__init__(name, description, schema)
        self.func = func

    async def run(self, arguments: dict[str, Any]) -> ToolExecutionResult:
        """Execute the function with given arguments."""
        start_time = time.time()

        try:
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(arguments)
            else:
                result = self.func(arguments)

            execution_time = time.time() - start_time

            return ToolExecutionResult(
                success=True,
                result=result,
                error=None,
                execution_time=execution_time,
                tool_name=self.name,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolExecutionResult(
                success=False,
                result=f"Function '{self.name}' execution failed: {str(e)}",
                error=str(e),
                execution_time=execution_time,
                tool_name=self.name,
            )


class FunctionToolset(BaseToolset):
    """Toolset for function-based tools."""

    def __init__(self, tool_filter: list[str] | None = None):
        super().__init__(tool_filter)
        self._function_tools: list[FunctionTool] = []

    def add_function(
        self,
        name: str,
        description: str,
        func: Callable,
        schema: dict[str, Any] | None = None,
    ) -> None:
        """Add a function as a tool."""
        tool = FunctionTool(name, description, func, schema)
        self._function_tools.append(tool)

    async def get_tools(self) -> list[BaseTool]:
        """Get all function tools."""
        return self._function_tools.copy()

    async def close(self) -> None:
        """Close the function toolset."""
        self._function_tools = []
        await super().close()


# Asyncio import moved to top for PEP8 compliance
