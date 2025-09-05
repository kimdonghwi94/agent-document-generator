import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
import json
import uuid
import os
from src.config import Config
import logging

logger = logging.getLogger(__name__)


class MCPRunnerClient:
    """MCP Runner 서버를 통해 MCP 도구들을 관리하고 실행하는 클라이언트 (sub_agent_1.py 방식)"""
    
    def __init__(self, agent_id: str = None, mcp_runner_url: str = None):
        self.agent_id = agent_id or f"dh_agent_{uuid.uuid4().hex[:8]}"
        
        # MCP Runner URL 설정
        config = Config()
        self.mcp_runner_url = mcp_runner_url or getattr(config, 'MCP_RUNNER_URL', 'http://localhost:10000')
        
        self.active_sessions = {}  # session_key -> session_id 매핑
        self.mcp_configs = {}      # MCP 서버 설정들
        self.available_tools = {}  # MCP별 사용 가능한 도구 목록
        self._initialized = False
        
    async def initialize_from_config(self) -> Dict[str, List[Dict]]:
        """mcpserver.json 파일을 로드하고 MCP Runner를 통해 도구 목록을 가져오기 (sub_agent_1.py 방식)"""
        try:
            # mcpserver.json 파일 로드
            await self.load_mcp_configs()
            
            # 각 MCP 서버의 도구 목록 가져오기
            for mcp_name in self.mcp_configs.keys():
                await self.discover_mcp_tools(mcp_name)
            
            self._initialized = True
            logger.info(f"MCP Runner Client 초기화 완료: {len(self.mcp_configs)}개 서버, {sum(len(tools) for tools in self.available_tools.values())}개 도구")
            
            # 기존 인터페이스와 호환되도록 MCPToolExecutor 형태로 직접 반환
            tool_objects = {}
            for mcp_name, tools in self.available_tools.items():
                tool_objects[mcp_name] = [
                    MCPToolExecutor(tool['name'], tool.get('description', ''), tool.get('inputSchema', {}), mcp_name, self)
                    for tool in tools
                ]
            
            return tool_objects
            
        except Exception as e:
            logger.error(f"MCP Runner Client 초기화 실패: {e}")
            self._initialized = False
            return {}
    
    async def load_mcp_configs(self):
        """mcpserver.json 파일 로드 (sub_agent_1.py 방식)"""
        try:
            # 프로젝트 루트에서 mcpserver.json 찾기
            config_paths = [
                'mcpserver.json',
                '../mcpserver.json',
                os.path.join(os.path.dirname(__file__), '..', '..', 'mcpserver.json')
            ]
            
            config_data = None
            for config_path in config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    logger.info(f"MCP 설정 파일 로드: {config_path}")
                    break
            
            if not config_data:
                logger.warning("mcpserver.json 파일을 찾을 수 없습니다. 빈 설정으로 진행합니다.")
                return
                
            configs = config_data.get('mcpServers', config_data)
            
            for name, config in configs.items():
                command = config.get('command', '')
                args = config.get('args', [])
                
                self.mcp_configs[name] = {
                    'name': name,
                    'command': command,
                    'args': args,
                    'env': self.resolve_env_variables(config.get('env', {})),
                }
                
            logger.info(f"MCP 설정 로드 완료: {len(self.mcp_configs)}개 서버")
            
        except Exception as e:
            logger.error(f"MCP 설정 로드 실패: {e}")
            
    def resolve_env_variables(self, env_config: Dict) -> Dict:
        """환경 변수 치환 (sub_agent_1.py 방식)"""
        resolved = {}
        for key, value in env_config.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                resolved[key] = os.getenv(env_var, '')
            else:
                resolved[key] = value
        return resolved
        
    async def discover_mcp_tools(self, mcp_name: str):
        """MCP 서버의 도구 목록만 가져오기 (sub_agent_1.py 방식)"""
        if mcp_name not in self.mcp_configs:
            logger.warning(f"MCP 설정을 찾을 수 없습니다: {mcp_name}")
            return
            
        session_id = f"{self.agent_id}_{mcp_name}_discovery"
        
        try:
            async with aiohttp.ClientSession() as session:
                # MCP Runner에 도구 탐색 요청
                async with session.post(
                    f"{self.mcp_runner_url}/mcp/discover",
                    json={
                        'session_id': session_id,
                        'agent_id': self.agent_id,
                        'mcp_config': self.mcp_configs[mcp_name]
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result['status'] == 'success':
                            # 도구 목록 저장
                            self.available_tools[mcp_name] = result['tools']
                            logger.info(f"MCP '{mcp_name}' 도구 발견: {len(result['tools'])}개")
                            for tool in result['tools']:
                                logger.info(f"  - {tool['name']}: {tool.get('description', 'No description')}")
                        else:
                            logger.error(f"MCP '{mcp_name}' 도구 탐색 실패: {result.get('error')}")
                            self.available_tools[mcp_name] = []
                    else:
                        logger.error(f"MCP Runner 서버 응답 오류: {response.status}")
                        self.available_tools[mcp_name] = []
                        
        except Exception as e:
            logger.error(f"MCP '{mcp_name}' 도구 탐색 중 오류: {e}")
            self.available_tools[mcp_name] = []
            
    def get_all_tools(self) -> Dict[str, List[Dict]]:
        """모든 MCP 서버의 도구 목록 반환 (sub_agent_1.py 방식)"""
        return self.available_tools
        
    def get_tools_by_mcp(self, mcp_name: str) -> List[Dict]:
        """특정 MCP 서버의 도구 목록 반환 (sub_agent_1.py 방식)"""
        return self.available_tools.get(mcp_name, [])
        
    async def execute_mcp_tool(self, mcp_name: str, tool_name: str, arguments: Dict):
        """MCP 도구 실행 (sub_agent_1.py 방식)"""
        # 도구가 존재하는지 확인
        tools = self.available_tools.get(mcp_name, [])
        tool_exists = any(tool['name'] == tool_name for tool in tools)
        
        if not tool_exists:
            raise ValueError(f"Tool '{tool_name}' not found in MCP '{mcp_name}'")
            
        # 세션 ID 생성 (재사용 가능)
        session_key = f"{mcp_name}_{tool_name}"
        if session_key not in self.active_sessions:
            self.active_sessions[session_key] = f"{self.agent_id}_{mcp_name}_{uuid.uuid4().hex[:8]}"
            
        session_id = self.active_sessions[session_key]
        
        try:
            async with aiohttp.ClientSession() as http_session:
                # MCP Runner에 도구 실행 요청
                async with http_session.post(
                    f"{self.mcp_runner_url}/mcp/execute",
                    json={
                        'session_id': session_id,
                        'mcp_config': self.mcp_configs[mcp_name],
                        'tool_name': tool_name,
                        'arguments': arguments
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        raise Exception(f"MCP Runner 서버 오류 ({response.status}): {error_text}")
                        
        except Exception as e:
            logger.error(f"도구 실행 실패 '{mcp_name}.{tool_name}': {e}")
            raise
            
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """기존 인터페이스와의 호환성을 위한 메서드"""
        try:
            result = await self.execute_mcp_tool(server_name, tool_name, arguments)
            
            # CallToolResult 형태로 변환 (기존 코드와의 호환성)
            if result['status'] == 'success':
                return MCPRunnerResult(result.get('result', ''), True)
            else:
                return MCPRunnerResult(f"오류: {result.get('error', 'Unknown error')}", False)
                
        except Exception as e:
            return MCPRunnerResult(f"실행 실패: {str(e)}", False)
            
    async def cleanup_session(self, mcp_name: str = None):
        """MCP 세션 정리 (sub_agent_1.py 방식)"""
        if mcp_name:
            # 특정 MCP 관련 세션만 정리
            keys_to_remove = [k for k in self.active_sessions.keys() if k.startswith(f"{mcp_name}_")]
            for key in keys_to_remove:
                session_id = self.active_sessions[key]
                try:
                    async with aiohttp.ClientSession() as http_session:
                        await http_session.post(
                            f"{self.mcp_runner_url}/mcp/stop",
                            json={'session_id': session_id}
                        )
                except Exception as e:
                    logger.error(f"세션 정리 실패: {session_id} - {e}")
                del self.active_sessions[key]
        else:
            # 모든 세션 정리
            for session_id in list(self.active_sessions.values()):
                try:
                    async with aiohttp.ClientSession() as http_session:
                        await http_session.post(
                            f"{self.mcp_runner_url}/mcp/stop",
                            json={'session_id': session_id}
                        )
                except Exception as e:
                    logger.error(f"세션 정리 실패: {session_id} - {e}")
            self.active_sessions.clear()
            
    async def cleanup(self):
        """모든 리소스 정리"""
        try:
            await self.cleanup_session()  # 모든 세션 정리
            self._initialized = False
            logger.info("MCP Runner Client 정리 완료")
        except Exception as e:
            logger.error(f"MCP Runner Client 정리 중 오류: {e}")
            
    @property
    def sessions(self) -> Dict:
        """기존 코드와의 호환성을 위한 속성"""
        # 세션 정보를 기존 형태로 변환
        session_info = {}
        for session_key, session_id in self.active_sessions.items():
            mcp_name = session_key.split('_')[0]
            session_info[mcp_name] = {
                'ready': True,
                'session_id': session_id,
                'tools': self.available_tools.get(mcp_name, [])
            }
        return session_info




class MCPRunnerResult:
    """MCP Runner 실행 결과를 기존 CallToolResult과 호환되게 만드는 클래스"""
    
    def __init__(self, content: Any, success: bool = True):
        if success:
            self.content = [MCPRunnerTextContent(str(content))]
        else:
            self.content = [MCPRunnerTextContent(str(content))]
    

class MCPRunnerTextContent:
    """텍스트 콘텐츠 래퍼"""
    
    def __init__(self, text: str):
        self.text = text


class MCPToolExecutor:
    """MCP Runner를 통한 도구 실행기 - 간단한 구조"""
    
    def __init__(self, name: str, description: str, input_schema: Dict, server_name: str, client: MCPRunnerClient):
        self.name = name
        self.description = description
        self.inputSchema = input_schema
        self.server_name = server_name
        self.client = client
        
    async def __call__(self, **kwargs):
        """도구 실행"""
        return await self.client.call_tool(self.server_name, self.name, kwargs)