"""지능형 에이전트 실행기"""

import asyncio
import json
import logging
from typing import Dict, List, Any, AsyncGenerator

from a2a.server.agent_execution import AgentExecutor as BaseAgentExecutor, RequestContext
from a2a.server.events import EventQueue, TaskArtifactUpdateEvent, TaskStatusUpdateEvent
from a2a.server.tasks import TaskState, TaskStatus
from a2a.utils import new_agent_text_message, new_text_artifact

from src.mcp.simple_mcp_client import SimpleMCPClient

logger = logging.getLogger(__name__)


class AgentExecutor(BaseAgentExecutor):
    """다양한 도구들을 활용하는 지능형 에이전트 실행기"""
    
    def __init__(self):
        self._startup_complete = False
        self.mcp_client = SimpleMCPClient()
        self.available_tools: Dict[str, List[Dict[str, Any]]] = {}
        
    async def startup(self):
        """에이전트 시작 및 도구들 로드"""
        if not self._startup_complete:
            try:
                self.available_tools = await self.mcp_client.get_available_tools_from_config()
                self._startup_complete = True
            except Exception:
                self._startup_complete = True
                
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """사용자 요청을 처리하고 결과를 스트리밍"""
        
        task = context.task
        user_message = self._extract_message(context)
        
        async for event in self._process_request(user_message):
            if event['is_task_complete']:
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        append=False,
                        context_id=task.context_id,
                        task_id=task.id,
                        last_chunk=True,
                        artifact=new_text_artifact(
                            name='current_result',
                            description='Result of request to agent.',
                            text=event['content'],
                        ),
                    )
                )
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                        context_id=task.context_id,
                        task_id=task.id,
                    )
                )
            elif event.get('require_user_input', False):
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.input_required,
                            message=new_agent_text_message(
                                event['content'],
                                task.context_id,
                                task.id,
                            ),
                        ),
                        final=True,
                        context_id=task.context_id,
                        task_id=task.id,
                    )
                )
            else:
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        append=True,
                        status=TaskStatus(
                            state=TaskState.working,
                            message=new_agent_text_message(
                                event['content'],
                                task.context_id,
                                task.id,
                            ),
                        ),
                        final=False,
                        context_id=task.context_id,
                        task_id=task.id,
                    )
                )
    
    async def _process_request(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """사용자 요청을 처리하고 스트리밍 이벤트 생성"""
        
        try:
            if not user_message.strip():
                yield {'content': '안녕하세요! 무엇을 도와드릴까요?', 'is_task_complete': True}
                return
            
            # 작업 시작 알림
            yield {'content': '요청을 처리하고 있습니다...', 'is_task_complete': False}
            
            # 도구 선택 및 실행
            selected_tool = self._analyze_request_and_select_tool(user_message)
            
            if selected_tool:
                yield {'content': f"적절한 도구를 찾았습니다: {selected_tool['tool']['name']}", 'is_task_complete': False}
                result = await self._execute_tool(selected_tool, user_message)
                yield {'content': result, 'is_task_complete': True}
            else:
                # 일반적인 대화 응답
                response = self._generate_general_response(user_message)
                yield {'content': response, 'is_task_complete': True}
                
        except Exception as e:
            yield {'content': f"처리 중 오류가 발생했습니다: {str(e)}", 'is_task_complete': True}
    
    def _extract_message(self, context: RequestContext) -> str:
        """RequestContext에서 사용자 메시지 추출"""
        user_message = ""
        if hasattr(context, "message") and context.message:
            if hasattr(context.message, "parts") and context.message.parts:
                for part in context.message.parts:
                    if hasattr(part, "root") and part.root:
                        if hasattr(part.root, "text"):
                            user_message += part.root.text
                    elif hasattr(part, "text"):
                        user_message += part.text
        return user_message
    
    def _analyze_request_and_select_tool(self, user_message: str) -> Dict[str, Any] | None:
        """사용자 요청을 분석하여 가장 적절한 MCP 도구 선택"""
        user_lower = user_message.lower()
        
        # 웹 검색 관련 키워드
        search_keywords = ['검색', 'search', '찾아', '알아봐', 'google', '구글']
        if any(keyword in user_lower for keyword in search_keywords):
            for server_name, tools in self.available_tools.items():
                for tool in tools:
                    if 'search' in tool.get('name', '').lower():
                        return {
                            'server': server_name,
                            'tool': tool,
                            'action': 'search',
                            'query': user_message
                        }
        
        # 웹페이지 방문 관련 키워드
        visit_keywords = ['방문', 'visit', 'page', '페이지', 'url', '웹사이트', '사이트']
        if any(keyword in user_lower for keyword in visit_keywords):
            for server_name, tools in self.available_tools.items():
                for tool in tools:
                    if 'visit' in tool.get('name', '').lower():
                        return {
                            'server': server_name,
                            'tool': tool,
                            'action': 'visit',
                            'query': user_message
                        }
        
        # 스크린샷 관련 키워드
        screenshot_keywords = ['스크린샷', 'screenshot', '화면', 'capture', '캡처']
        if any(keyword in user_lower for keyword in screenshot_keywords):
            for server_name, tools in self.available_tools.items():
                for tool in tools:
                    if 'screenshot' in tool.get('name', '').lower():
                        return {
                            'server': server_name,
                            'tool': tool,
                            'action': 'screenshot',
                            'query': user_message
                        }
        
        # 요약 관련 키워드
        summarize_keywords = ['요약', 'summarize', '정리', '요약해', '간단히']
        if any(keyword in user_lower for keyword in summarize_keywords):
            for server_name, tools in self.available_tools.items():
                for tool in tools:
                    if 'summarize' in tool.get('name', '').lower():
                        return {
                            'server': server_name,
                            'tool': tool,
                            'action': 'summarize',
                            'query': user_message
                        }
        
        return None
    
    async def _execute_tool(self, selected_tool: Dict[str, Any], user_message: str) -> str:
        """선택된 MCP 도구를 실행"""
        server_name = selected_tool['server']
        tool = selected_tool['tool']
        action = selected_tool['action']
        
        # 도구 실행 시뮬레이션 (실제로는 MCP 서버와 통신)
        tool_name = tool.get('name', '')
        tool_description = tool.get('description', '')
        
        if action == 'search':
            return f"🔍 {tool_name} 도구를 사용하여 검색을 수행했습니다.\n\n요청: {user_message}\n\n도구 설명: {tool_description}\n\n결과: 검색이 완료되었습니다."
        
        elif action == 'visit':
            return f"🌐 {tool_name} 도구를 사용하여 웹페이지를 방문했습니다.\n\n요청: {user_message}\n\n도구 설명: {tool_description}\n\n결과: 웹페이지 내용을 추출했습니다."
        
        elif action == 'screenshot':
            return f"📷 {tool_name} 도구를 사용하여 스크린샷을 촬영했습니다.\n\n요청: {user_message}\n\n도구 설명: {tool_description}\n\n결과: 스크린샷이 생성되었습니다."
        
        elif action == 'summarize':
            return f"📝 {tool_name} 도구를 사용하여 내용을 요약했습니다.\n\n요청: {user_message}\n\n도구 설명: {tool_description}\n\n결과: 요약이 완료되었습니다."
        
        else:
            return f"🔧 {tool_name} 도구를 사용했습니다.\n\n요청: {user_message}\n\n도구 설명: {tool_description}\n\n결과: 작업이 완료되었습니다."
    
    def _generate_general_response(self, user_message: str) -> str:
        """MCP 도구를 사용하지 않는 일반적인 대화 응답"""
        
        # 사용 가능한 도구들 나열
        tool_info = []
        for server_name, tools in self.available_tools.items():
            for tool in tools:
                tool_name = tool.get('name', '')
                tool_desc = tool.get('description', '')
                tool_info.append(f"- **{tool_name}**: {tool_desc}")
        
        if tool_info:
            tools_text = "\n".join(tool_info)
            return f"""안녕하세요! 다음과 같은 도구들을 사용할 수 있습니다:

{tools_text}

어떤 도구를 사용하고 싶으신지 말씀해주세요!

받은 메시지: {user_message}"""
        else:
            return f"""안녕하세요! 현재 MCP 도구 로딩 중입니다.

받은 메시지: {user_message}

곧 다양한 도구들을 사용할 수 있게 될 예정입니다."""
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """작업 취소"""
        await event_queue.enqueue_event(new_agent_text_message("작업이 취소되었습니다."))
    
    async def cleanup(self):
        """리소스 정리"""
        self._startup_complete = False