"""DH 에이전트 - 문서 생성 및 MCP 도구 활용"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, AsyncGenerator, Optional

from google import genai
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

from src.prompts.prompts import AgentPrompts
from src.config import Config
from src.mcp_client.simple_mcp_client import PersistentMCPClient, MCPToolExecutor

logger = logging.getLogger(__name__)


class DhAgent:
    """DH 에이전트 - 실제 LLM + MCP 도구를 활용하는 지능형 에이전트"""
    
    def __init__(self):
        self.agent_name = "DH Document Generator Agent"
        self.mcp_client = PersistentMCPClient()
        self.mcp_tools: Dict[str, List[MCPToolExecutor]] = {}
        self.genai_client = None
        self._initialized = False
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}  # context_id -> list of messages
    
    async def initialize(self):
        """에이전트 초기화 - 실제 LLM + MCP 방식"""
        if self._initialized:
            return
        
        try:
            # Google API 키 설정
            config = Config()
            if config.GOOGLE_API_KEY:
                os.environ['GOOGLE_API_KEY'] = config.GOOGLE_API_KEY
                logger.info("Google API key 설정 완료")
            else:
                logger.warning("Google API key가 설정되지 않음")
            
            # Gemini 클라이언트 초기화
            self.genai_client = genai.Client()
            
            # MCP 도구들 로드
            mcp_tools = await self.mcp_client.initialize_from_config()
            
            # 실행 가능한 도구로 변환
            for server_name, tools in mcp_tools.items():
                self.mcp_tools[server_name] = [
                    MCPToolExecutor(tool, server_name, self.mcp_client) 
                    for tool in tools
                ]
            
            # MCP 서버들이 모두 준비될 때까지 추가 대기
            await self._wait_for_all_mcp_servers_ready()
            
            total_tools = sum(len(tools) for tools in self.mcp_tools.values())
            logger.info(f"MCP 도구 로드 완료: {len(self.mcp_tools)}개 서버, {total_tools}개 도구")
            
            self._initialized = True
            logger.info("DhAgent 초기화 완료")
            
        except Exception as e:
            logger.error(f"DhAgent 초기화 실패: {e}")
            self._initialized = False
            raise
    
    async def stream(self, query: str, context_id: str, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """사용자 요청을 실제 LLM + MCP로 처리하여 스트리밍 응답"""
        
        if not self._initialized:
            yield {
                'content': '에이전트가 초기화되지 않음',
                'is_task_complete': True,
                'response_type': 'text'
            }
            return
        
        try:
            # 대화 기록 초기화 (context_id가 없으면 생성)
            if context_id not in self.conversation_history:
                self.conversation_history[context_id] = []
            
            # 사용자 메시지를 대화 기록에 추가
            self.conversation_history[context_id].append({
                'role': 'user',
                'content': query
            })
            
            # 작업 시작 알림
            yield {
                'content': f'요청 처리를 시작합니다: {query}',
                'is_task_complete': False,
                'response_type': 'text'
            }
            
            # URL이 포함된 경우 MCP 도구 먼저 사용
            if query.startswith("http") and self.mcp_tools:
                async for result in self._process_with_mcp_tools(query, context_id):
                    yield result
            else:
                # 일반 질의응답은 LLM 직접 사용 (컨텍스트 포함)
                async for result in self._process_with_llm(query, context_id):
                    yield result
        
        except Exception as e:
            logger.error(f"DhAgent stream 오류: {e}")
            yield {
                'content': f'처리 중 오류가 발생했습니다: {str(e)}',
                'is_task_complete': True,
                'response_type': 'text'
            }
    
    async def _process_with_mcp_tools(self, query: str, context_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """MCP 도구를 활용한 처리"""
        
        # AI를 사용해 적절한 도구 선택
        tool_to_use = await self._select_best_tool(query)
        
        if tool_to_use:
            yield {
                'content': '웹 페이지를 분석하고 있습니다...',
                'is_task_complete': False,
                'response_type': 'text'
            }
            
            try:
                # MCP 서버 준비 상태 확인
                server_ready = await self._check_mcp_server_ready(tool_to_use.server_name)
                if not server_ready:
                    raise Exception(f"서버가 준비되지 않았습니다")
                
                # URL 추출
                url = self._extract_url_from_query(query)
                
                # MCP 도구 실행
                if "qna" in tool_to_use.name.lower():
                    # QnA 도구는 URL과 질문 필요
                    question = self._extract_question_from_query(query)
                    result = await tool_to_use(url=url, question=question)
                else:
                    # Markdown 도구는 URL만 필요
                    result = await tool_to_use(url=url)

                # MCP 결과 처리
                if hasattr(result, 'content') and result.content:
                    content = result.content[0].text if result.content else str(result)
                else:
                    content = str(result)
                
                # 자연스러운 응답으로 변환
                final_response = await self._format_natural_response(content, query)
                
                # 어시스턴트 응답을 대화 기록에 추가
                self.conversation_history[context_id].append({
                    'role': 'assistant',
                    'content': final_response
                })
                
                yield {
                    'content': final_response,
                    'is_task_complete': True,
                    'response_type': 'text'
                }
                
            except Exception as e:
                logger.error(f"MCP 도구 실행 오류: {e}")
                # MCP 실패시 LLM으로 fallback
                async for result in self._process_with_llm(f"다음 URL에 대한 질문: {query}", context_id):
                    yield result
        else:
            # 적절한 도구가 없으면 LLM으로 처리
            async for result in self._process_with_llm(query, context_id):
                yield result

    async def _select_best_tool(self, query: str) -> Any:
        """AI를 사용해 쿼리에 가장 적합한 도구 선택"""
        if not self.mcp_tools:
            return None
            
        # 사용 가능한 도구들의 설명 수집
        available_tools = []
        for srv_name, tools in self.mcp_tools.items():
            for tool in tools:
                available_tools.append({
                    'name': tool.name,
                    'description': getattr(tool, 'description', ''),
                    'tool': tool
                })
        
        if not available_tools:
            return None
            
        # AI를 사용해 도구 선택
        try:
            tools_info = "\n".join([f"- {t['name']}: {t['description']}" for t in available_tools])
            selection_prompt = f"""
다음 사용자 질문에 가장 적합한 도구를 선택하세요:

사용자 질문: {query}

사용 가능한 도구들:
{tools_info}

응답 형식: 도구명만 반환 (예: web_content_qna)
"""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=selection_prompt,
                config={'temperature': 0.1}
            )
            
            selected_tool_name = response.text.strip() if response.text else ""
            
            # 선택된 도구 반환
            for tool_info in available_tools:
                if tool_info['name'] in selected_tool_name:
                    return tool_info['tool']
                    
        except Exception as e:
            logger.error(f"도구 선택 오류: {e}")
            
        # AI 선택 실패시 첫 번째 도구 사용
        return available_tools[0]['tool'] if available_tools else None
    
    def _extract_url_from_query(self, query: str) -> str:
        """쿼리에서 URL 추출"""
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, query)
        return urls[0] if urls else ""
    
    def _extract_question_from_query(self, query: str) -> str:
        """쿼리에서 URL을 제외한 질문 부분 추출"""
        import re
        # URL 제거
        url_pattern = r'https?://[^\s]+'
        question = re.sub(url_pattern, '', query).strip()
        # 기본 질문이 없으면 기본값 사용
        return question if question else "이 웹사이트에 대해 알려주세요"
    
    async def _format_natural_response(self, content: str, original_query: str) -> str:
        """MCP 도구 결과를 자연스러운 응답으로 변환"""
        try:
            # MCP 응답에서 실제 텍스트 추출
            if hasattr(content, 'content') and content.content:
                # MCP CallToolResult 객체인 경우
                actual_content = content.content[0].text if content.content else str(content)
            elif 'content=' in str(content) and 'TextContent' in str(content):
                # 문자열로 된 MCP 결과에서 텍스트 추출
                import re
                text_match = re.search(r"text='([^']+)'", str(content))
                actual_content = text_match.group(1) if text_match else str(content)
            else:
                actual_content = str(content)
            
            format_prompt = f"""
다음은 웹 페이지 분석 결과입니다. 사용자의 질문에 맞게 자연스럽고 유용한 한국어 답변으로 정리해주세요:

사용자 질문: {original_query}

분석 결과:
{actual_content[:2000]}  

요구사항:
- 사용자가 이해하기 쉽게 설명
- 핵심 정보만 간결하게 정리
- 도구 이름이나 기술적인 용어는 사용하지 말 것
- 한국어로 자연스럽게 답변
- 만약 관련 정보가 없다면 정중하게 안내
"""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=format_prompt,
                config={'temperature': 0.3}
            )
            
            return response.text if response.text else actual_content
            
        except Exception as e:
            logger.error(f"응답 포맷팅 오류: {e}")
            return "죄송합니다. 웹페이지 분석 중 문제가 발생했습니다."
    
    async def _process_with_llm(self, query: str, context_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Gemini LLM을 사용한 처리"""
        
        try:
            # 대화 기록 조회
            conversation = self.conversation_history.get(context_id, [])
            
            # 프롬프트 생성 (대화 기록 포함)
            system_prompt = AgentPrompts.get_general_assistant_prompt("")
            
            # 대화 기록을 프롬프트에 포함
            conversation_context = ""
            if len(conversation) > 1:  # 현재 메시지 외에 이전 대화가 있는 경우
                conversation_context = "\n\n=== 이전 대화 기록 ===\n"
                for msg in conversation[:-1]:  # 마지막 메시지(현재 질문) 제외
                    role = "사용자" if msg['role'] == 'user' else "어시스턴트"
                    conversation_context += f"{role}: {msg['content']}\n"
                conversation_context += "==================\n"
            
            full_prompt = f"{system_prompt}{conversation_context}\n\n사용자 질문: {query}"
            
            yield {
                'content': 'AI가 응답을 생성 중입니다...',
                'is_task_complete': False,
                'response_type': 'text'
            }
            
            # Gemini 2.0 Flash로 응답 생성
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=full_prompt,
                config={'temperature': 0.7}
            )
            
            content = response.text if response.text else "응답을 생성할 수 없습니다."
            
            # 어시스턴트 응답을 대화 기록에 추가
            self.conversation_history[context_id].append({
                'role': 'assistant',
                'content': content
            })
            
            # 구조화된 콘텐츠인지 판단
            response_type = 'data' if self._is_structured_content(content) else 'text'
            
            yield {
                'content': content,
                'is_task_complete': True,
                'response_type': response_type
            }
            
        except Exception as e:
            logger.error(f"LLM 처리 오류: {e}")
            yield {
                'content': f'LLM 처리 중 오류: {str(e)}',
                'is_task_complete': True,
                'response_type': 'text'
            }
    
    def _get_tools_description(self) -> str:
        """사용 가능한 도구들의 설명을 생성"""
        if not self.mcp_tools:
            return "현재 사용 가능한 외부 도구가 없습니다."
        
        descriptions = []
        for server_name, tools in self.mcp_tools.items():
            descriptions.append(f"=== {server_name} 서버 도구들 ===")
            for tool in tools:
                descriptions.append(f"- {tool.name}: {tool.description}")
            descriptions.append("")  # 빈 줄 추가
        
        return "\n".join(descriptions) if descriptions else "사용 가능한 도구 없음"
    
    async def _wait_for_all_mcp_servers_ready(self):
        """모든 MCP 서버가 준비될 때까지 대기"""
        if not self.mcp_tools:
            return
        
        logger.info("모든 MCP 서버 준비 상태 확인 중...")
        
        for server_name in self.mcp_tools.keys():
            max_retries = 30  # 최대 30초 대기
            retry_count = 0
            
            while retry_count < max_retries:
                if await self._check_mcp_server_ready(server_name):
                    logger.info(f"MCP 서버 '{server_name}' 준비 완료")
                    break
                
                retry_count += 1
                await asyncio.sleep(1.0)
                
                if retry_count >= max_retries:
                    logger.warning(f"MCP 서버 '{server_name}' 준비 시간 초과 (30초)")
    
    async def _check_mcp_server_ready(self, server_name: str) -> bool:
        """MCP 서버가 준비되었는지 확인"""
        try:
            # 서버 세션이 존재하고 준비되었는지 확인
            sessions = getattr(self.mcp_client, 'sessions', {})
            if server_name not in sessions:
                return False
            
            session_info = sessions[server_name]
            ready = session_info.get('ready', False)
            
            return ready
            
        except Exception as e:
            logger.error(f"MCP 서버 '{server_name}' 상태 확인 실패: {e}")
            return False
    
    def _is_structured_content(self, text: str) -> bool:
        """텍스트가 구조화된 콘텐츠(HTML/MD)인지 판단"""
        if not text:
            return False
            
        text_stripped = text.strip()
        return (
            text_stripped.startswith('<html') or 
            text_stripped.startswith('<!DOCTYPE') or
            text_stripped.startswith('#') or
            '<h1>' in text_stripped or
            '<div>' in text_stripped or
            '```' in text_stripped or
            len(text_stripped.split('\n')) > 10  # 긴 구조화된 텍스트
        )
    
    async def cancel(self):
        """작업 취소"""
        logger.info("DhAgent 작업 취소")
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            # MCP 클라이언트 정리
            if self.mcp_client:
                await self.mcp_client.cleanup()
            
            self._initialized = False
            logger.info("DhAgent 정리 완료")
        except Exception as e:
            logger.error(f"DhAgent 정리 중 오류: {e}")
    
    @property
    def is_ready(self) -> bool:
        """에이전트가 준비되었는지 확인"""
        return self._initialized and self.genai_client is not None