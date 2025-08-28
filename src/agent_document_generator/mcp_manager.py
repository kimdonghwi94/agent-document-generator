"""MCP Server management and integration."""

import asyncio
import subprocess
import json
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from .config import Config

logger = logging.getLogger(__name__)


class MCPServer:
    """Represents a single MCP server instance."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.command = config.get("command")
        self.args = config.get("args", [])
        self.env = config.get("env", {})
        self.description = config.get("description", "")
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
    
    async def start(self) -> bool:
        """Start the MCP server."""
        try:
            env = {**dict(os.environ), **self.env}
            logger.info(f"Starting MCP server {self.name} with command: {self.command} {' '.join(self.args)}")
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Give it a moment to start and check if it's still running
            await asyncio.sleep(0.5)
            if self.process.poll() is not None:
                # Process has already exited
                stdout, stderr = self.process.communicate()
                logger.error(f"MCP server {self.name} exited immediately. Stdout: {stdout}, Stderr: {stderr}")
                return False
            
            self.is_running = True
            logger.info(f"Started MCP server: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start MCP server {self.name}: {e}")
            return False
    
    async def stop(self):
        """Stop the MCP server."""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(asyncio.create_task(self._wait_for_process()), timeout=10.0)
            except asyncio.TimeoutError:
                self.process.kill()
            self.is_running = False
            logger.info(f"Stopped MCP server: {self.name}")
    
    async def _wait_for_process(self):
        """Wait for process to terminate."""
        while self.process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the MCP server."""
        if not self.is_running or not self.process:
            logger.warning(f"MCP server {self.name} is not running")
            return None
        
        try:
            request_json = json.dumps(request) + "\n"
            
            # Check if stdin is available
            if self.process.stdin is None:
                logger.error(f"MCP server {self.name} stdin is not available")
                return None
                
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # Wait for response with timeout
            import asyncio
            try:
                response_line = await asyncio.wait_for(
                    asyncio.create_task(self._read_response()), 
                    timeout=5.0
                )
                if response_line:
                    return json.loads(response_line.strip())
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for response from MCP server {self.name}")
                
        except Exception as e:
            logger.error(f"Failed to communicate with MCP server {self.name}: {e}")
        
        return None
    
    async def _read_response(self) -> Optional[str]:
        """Read response from MCP server stdout."""
        try:
            # Read in a loop to handle blocking
            import asyncio
            loop = asyncio.get_event_loop()
            response_line = await loop.run_in_executor(None, self.process.stdout.readline)
            return response_line
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            return None


class MCPManager:
    """Manages all MCP servers."""
    
    def __init__(self, config: Config):
        self.config = config
        self.servers: Dict[str, MCPServer] = {}
        self._load_servers()
    
    def _load_servers(self):
        """Load MCP servers from configuration."""
        mcp_config = self.config.load_mcp_config()
        servers_config = mcp_config.get("mcpServers", {})
        
        for name, config in servers_config.items():
            self.servers[name] = MCPServer(name, config)
    
    async def start_all(self):
        """Start all MCP servers."""
        tasks = []
        for server in self.servers.values():
            tasks.append(server.start())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        started_count = sum(1 for result in results if result is True)
        logger.info(f"Started {started_count}/{len(self.servers)} MCP servers")
    
    async def stop_all(self):
        """Stop all MCP servers."""
        tasks = []
        for server in self.servers.values():
            if server.is_running:
                tasks.append(server.stop())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All MCP servers stopped")
    
    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get MCP server by name."""
        return self.servers.get(name)
    
    def get_server_status(self) -> Dict[str, str]:
        """Get status of all MCP servers."""
        return {
            name: "running" if server.is_running else "stopped"
            for name, server in self.servers.items()
        }
    
    async def convert_with_pandoc(self, content: str, from_format: str, to_format: str) -> Optional[str]:
        """Convert content using pandoc MCP server."""
        pandoc_server = self.get_server("mcp-pandoc")
        if not pandoc_server:
            logger.error("Pandoc MCP server not available")
            return None
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "pandoc_convert",
                "arguments": {
                    "text": content,
                    "from_format": from_format,
                    "to_format": to_format
                }
            }
        }
        
        response = await pandoc_server.send_request(request)
        if response and response.get("result"):
            return response["result"].get("content", {}).get("text")
        
        return None
    
    async def save_file(self, file_path: str, content: str) -> bool:
        """Save file using filesystem MCP server with fallback to direct file write."""
        # Try MCP filesystem server first
        fs_server = self.get_server("mcp-filesystem")
        if fs_server and fs_server.is_running:
            try:
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "write_file",
                        "arguments": {
                            "path": file_path,
                            "contents": content
                        }
                    }
                }
                
                response = await fs_server.send_request(request)
                if response and response.get("result") is not None:
                    logger.info(f"File saved via MCP filesystem server: {file_path}")
                    return True
            except Exception as e:
                logger.warning(f"MCP filesystem server failed: {e}, falling back to direct file write")
        
        # Fallback to direct file writing
        try:
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"File saved via direct write: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            return False