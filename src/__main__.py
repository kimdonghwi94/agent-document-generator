import json
import os
from pathlib import Path

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.responses import JSONResponse, RedirectResponse

from src.executor.dh_executor import DhAgentExecutor
from src.config import Config


async def get_mcp_tools_info():
    """mcpserver.json을 읽어서 자동으로 MCP 서버 연결하고 도구 정보 가져오기"""
    from src.mcp_client.simple_mcp_client import PersistentMCPClient

    client = PersistentMCPClient()
    
    try:
        available_tools = await client.get_available_tools_from_config()
        await client.cleanup()  # 정리 작업
        return available_tools
    except Exception as e:
        try:
            await client.cleanup()
        except:
            pass
        return {}


def create_mcp_skills_from_tools(server_name: str, tools: list[dict]) -> list[AgentSkill]:
    """Create individual AgentSkill objects for each MCP tool - each tool represents a distinct capability"""
    if not tools:
        return []
    
    skills = []
    
    for tool in tools:
        tool_name = tool.get("name", "")
        tool_desc = tool.get("description", "")
        
        if not tool_name:
            continue
        
        # Generate skill ID based on tool name
        skill_id = f"mcp_{server_name}_{tool_name}"
        
        # Generate human-readable skill name
        skill_name = tool_name.replace('_', ' ').replace('-', ' ').title()
        
        # Use tool's actual description
        description = tool_desc if tool_desc else f"{tool_name} 도구 기능"
        
        # Generate tags based on tool name and server
        tags = ["mcp", server_name, tool_name]
        
        skill = AgentSkill(
            id=skill_id,
            name=skill_name,
            description=description,
            tags=tags,
            examples=[],  # Remove examples as requested
        )
        
        skills.append(skill)
    
    return skills


async def create_agent_skills():
    """Create agent skills - only MCP-specific skills (document generation and QA are basic capabilities)"""
    # Get actual MCP tools information
    mcp_tools = await get_mcp_tools_info()
    mcp_skills = []
    
    # Create skills based on actual available tools
    for server_name, tools in mcp_tools.items():
        if tools:  # Only create skills for servers with actual tools
            server_skills = create_mcp_skills_from_tools(server_name, tools)
            mcp_skills.extend(server_skills)
    
    return mcp_skills


async def create_app():
    all_skills = await create_agent_skills()

    agent_card = AgentCard(
        name="Advanced Document Generator Agent",
        description="HTML, Markdown 문서 생성과 일반 질의응답이 가능한 AI 에이전트입니다.",
        url="https://agent-document-generator.vercel.app/",
        version="2.1.0",
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text/plain", "text/html", "text/markdown", "application/json", "image/png"],
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=False,
            extensions=None
        ),
        skills=all_skills,
    )

    # Create agent executor and initialize it
    agent_executor = DhAgentExecutor()
    await agent_executor.startup()

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    app = server.build()

    @app.route("/health")
    async def health(request):
        return JSONResponse({"status": "healthy"})

    @app.route("/", methods=["GET"])
    async def root(request):
        return RedirectResponse(
            url="https://kimdonghwi94.github.io/dhkim", status_code=302
        )

    return app


def main():
    import asyncio

    import uvicorn

    config = Config()

    # Create and run the app synchronously
    app = asyncio.run(create_app())

    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
