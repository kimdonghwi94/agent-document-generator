"""Configuration management for the agent."""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # A2A Protocol Configuration
    A2A_AGENT_ID: str = os.getenv("A2A_AGENT_ID", "agent-document-generator")
    A2A_HOST_URL: str = os.getenv("A2A_HOST_URL", "http://localhost:8000")
    A2A_API_KEY: str = os.getenv("A2A_API_KEY", "")
    
    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4-turbo-preview")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8004"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Output Configuration
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./"))
    DEFAULT_FORMAT: str = os.getenv("DEFAULT_FORMAT", "html")
    
    # MCP Configuration
    MCP_CONFIG_PATH: Path = Path("mcpserver.json")
    
    @classmethod
    def load_mcp_config(cls) -> Dict[str, Any]:
        """Load MCP server configuration."""
        import json
        
        if cls.MCP_CONFIG_PATH.exists():
            with open(cls.MCP_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"mcpServers": {}}
    
    def __init__(self):
        pass
        """Initialize configuration and create directories."""
        # self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)