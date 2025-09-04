"""
MCP 클라이언트 - 실제 도구 실행이 가능한 persistent session 기반 클라이언트
"""

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool
from mcp.client.streamable_http import streamablehttp_client
from src.config import Config


logger = logging.getLogger(__name__)


class PersistentMCPClient:
    """지속적 연결을 유지하는 MCP 클라이언트 - 실제 도구 실행 가능"""
    
    def __init__(self):
        self.sessions: Dict[str, Any] = {}  # 서버별 세션과 컨텍스트
        self.tools: Dict[str, List[Tool]] = {}  # 서버별 MCP Tool 객체
        self._initialized = False
        self._cleanup_tasks: List[asyncio.Task] = []
        self._background_tasks: Dict[str, asyncio.Task] = {}  # 서버별 백그라운드 태스크 추적

    async def initialize_from_config(self) -> Dict[str, List[Tool]]:
        """mcpserver.json에서 모든 서버를 초기화하고 도구들을 로드"""
        server_name = "Web Analyzer MCP"

        config = Config()
        url = config.SMITHERY_BASE_URL
        profile = config.SMITHERY_PROFILE
        api_key = config.SMITHERY_API_KEY

        all_tools = {}
        try:
            tools = await self._initialize_server(url, api_key, profile)
            if tools:
                all_tools[server_name] = tools
                logger.info(f"MCP 서버 '{server_name}' 초기화 완료: {len(tools)}개 도구")
        except Exception as e:
            logger.error(f"MCP 서버 '{server_name}' 초기화 실패: {e}")

        self._initialized = True
        return all_tools

    async def _initialize_server(self, base_url: str, api_key: str, profile: str) -> List[Tool]:
        """개별 MCP 서버 초기화 및 persistent session 생성"""
        server_name = "Web Analyzer MCP"

        try:
            from urllib.parse import urlencode
            
            # URL 파라미터 구성
            params = {"api_key": api_key, "profile": profile}
            url = f"{base_url}?{urlencode(params)}"
            
            # 백그라운드 태스크로 MCP 서버 관리 - 독립적인 컨텍스트에서 실행
            task = asyncio.create_task(self._run_persistent_mcp_server(url))
            self._background_tasks[server_name] = task

            # 초기화 완료 대기 (최대 15초)
            tools = await asyncio.wait_for(self._wait_for_server_ready(server_name), timeout=15.0)

            logger.info(f"서버 '{server_name}' 정상 초기화: {len(tools)}개 도구")
            return tools

        except asyncio.TimeoutError:
            logger.error(f"서버 '{server_name}' 초기화 시간 초과")
            await self._cleanup_server_task(server_name)
            return []
        except Exception as e:
            logger.error(f"서버 '{server_name}' 연결 실패: {e}")
            await self._cleanup_server_task(server_name)
            return []

    async def _run_persistent_mcp_server(self, url):
        """독립적인 컨텍스트에서 MCP 서버를 영구적으로 실행"""
        server_name = "Web Analyzer MCP"  # 기본값 설정

        try:
            # MCP 기본 연결 (헤더 없이)
            async with streamablehttp_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await asyncio.sleep(0.5)
                    rest = await session.initialize()
                    server_name = rest.serverInfo.name  # 실제 서버 이름으로 업데이트
                    
                    # 도구 목록 가져오기
                    tool_list = await session.list_tools()
                    tools = list(tool_list.tools)

                    # 세션 정보 저장 (ready 상태로 표시)
                    self.sessions[server_name] = {
                        'session': session,
                        'tools': tools,
                        'initialized': True,
                        'ready': True
                    }
                    self.tools[server_name] = tools

                    logger.info(f"MCP 서버 '{server_name}' 준비 완료: {len(tools)}개 도구")
                    for tool in tools:
                        logger.info(f"  - {tool.name}: {tool.description}")

                    # 서버가 종료될 때까지 대기 - 연결 유지
                    try:
                        while True:
                            await asyncio.sleep(1)
                            # 세션이 여전히 활성 상태인지 확인
                            if server_name not in self.sessions:
                                break
                    except asyncio.CancelledError:
                        logger.debug(f"MCP 서버 '{server_name}' 태스크 취소됨")

        except Exception as e:
            logger.error(f"MCP 서버 '{server_name}' 실행 오류: {e}")
            # 오류 상태로 표시
            if server_name in self.sessions:
                self.sessions[server_name]['ready'] = False
        finally:
            # 정리
            if server_name in self.sessions:
                del self.sessions[server_name]
            if server_name in self.tools:
                del self.tools[server_name]
            if server_name in self._background_tasks:
                del self._background_tasks[server_name]
            logger.debug(f"MCP 서버 '{server_name}' 정리 완료")

    async def _wait_for_server_ready(self, server_name: str) -> List[Tool]:
        """서버가 준비될 때까지 대기"""
        for _ in range(100):  # 10초 대기 (0.1초씩)
            if server_name in self.sessions and self.sessions[server_name].get('ready'):
                return self.sessions[server_name]['tools']
            await asyncio.sleep(0.1)
        raise TimeoutError(f"서버 '{server_name}' 준비 시간 초과")

    async def _cleanup_server_task(self, server_name: str):
        """서버 태스크 정리"""
        if server_name in self._background_tasks:
            task = self._background_tasks[server_name]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self._background_tasks[server_name]

        # 세션 정보 정리
        if server_name in self.sessions:
            del self.sessions[server_name]
        if server_name in self.tools:
            del self.tools[server_name]

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """특정 서버의 도구를 실행"""
        if server_name not in self.sessions:
            raise ValueError(f"서버 '{server_name}'이 초기화되지 않음")

        session_info = self.sessions[server_name]

        # 서버가 준비되지 않은 경우
        if not session_info.get('ready', False):
            raise ValueError(f"서버 '{server_name}'이 준비되지 않음")

        session = session_info['session']

        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"도구 실행 실패 '{server_name}.{tool_name}': {e}")
            raise

    def get_tool_for_execution(self, server_name: str, tool_name: str) -> Optional[Tool]:
        """실행용 Tool 객체 반환"""
        if server_name in self.tools:
            for tool in self.tools[server_name]:
                if tool.name == tool_name:
                    return tool
        return None

    async def get_available_tools_from_config(self) -> Dict[str, List[Dict[str, Any]]]:
        """기존 인터페이스 호환성을 위한 메서드 - 도구 메타데이터만 반환"""
        if not self._initialized:
            await self.initialize_from_config()

        tools_metadata = {}
        for server_name, tools in self.tools.items():
            tools_metadata[server_name] = [
                {
                    "name": tool.name,
                    "description": getattr(tool, "description", ""),
                    "inputSchema": getattr(tool, "inputSchema", {}),
                    "server": server_name
                }
                for tool in tools
            ]

        return tools_metadata

    async def get_executable_tools(self) -> Dict[str, List[Tool]]:
        """실행 가능한 도구들을 반환 - 새로운 인터페이스"""
        if not self._initialized:
            await self.initialize_from_config()

        return self.tools

    async def cleanup(self):
        """모든 연결과 세션 정리"""
        # 백그라운드 태스크들을 먼저 정리
        cleanup_tasks = []
        for server_name in list(self._background_tasks.keys()):
            cleanup_tasks.append(self._cleanup_server_task(server_name))

        if cleanup_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*cleanup_tasks, return_exceptions=True), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("일부 서버 태스크 정리 시간 초과")

        # 남은 세션과 도구 정보 정리
        self.sessions.clear()
        self.tools.clear()
        self._background_tasks.clear()
        self._initialized = False
        
        logger.info("PersistentMCPClient 정리 완료")
    
    def __del__(self):
        """소멸자에서 정리 작업 예약"""
        if self.sessions or self._background_tasks:
            # 이미 실행 중인 이벤트 루프가 있으면 cleanup 태스크 생성
            try:
                loop = asyncio.get_running_loop()
                # 간단한 정리만 수행 - 백그라운드 태스크 취소
                for task in self._background_tasks.values():
                    if not task.done():
                        task.cancel()
            except RuntimeError:
                # 이벤트 루프가 없으면 무시
                pass
            except Exception as e:
                logger.debug(f"소멸자 정리 중 오류 (무시됨): {e}")


class MCPToolExecutor:
    """특정 MCP Tool과 Session을 바인딩하는 실행기"""
    
    def __init__(self, tool: Tool, server_name: str, client: PersistentMCPClient):
        self.tool = tool
        self.server_name = server_name
        self.client = client
    
    async def __call__(self, **kwargs) -> Any:
        """Tool 실행"""
        return await self.client.call_tool(self.server_name, self.tool.name, kwargs)
    
    @property
    def name(self) -> str:
        return self.tool.name
    
    @property
    def description(self) -> str:
        return getattr(self.tool, "description", "")
    
    @property
    def inputSchema(self) -> Dict[str, Any]:
        return getattr(self.tool, "inputSchema", {})


# 기존 호환성을 위한 별칭
SimpleMCPClient = PersistentMCPClient