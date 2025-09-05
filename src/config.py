"""Configuration management for the agent."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Google AI Configuration (Main LLM)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # MCP Configuration
    MCP_CONFIG_PATH: Path = Path("mcpserver.json")
    MCP_RUNNER_URL: str = os.getenv("MCP_RUNNER_URL", "http://localhost:10000")

    @classmethod
    def load_mcp_config(cls) -> dict[str, Any]:
        """Load MCP server configuration."""
        import json

        # Try relative to project root first
        project_root = Path(__file__).parent.parent
        config_path = project_root / "mcpserver.json"

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)

        # Fallback to original path
        if cls.MCP_CONFIG_PATH.exists():
            with open(cls.MCP_CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)

        return {"mcpServers": {}}

    def __init__(self):
        """Initialize configuration."""
        pass
