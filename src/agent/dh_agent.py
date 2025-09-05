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
from src.mcp_client.mcp_runner_client import MCPRunnerClient, MCPToolExecutor

logger = logging.getLogger(__name__)


class DhAgent:
    """DH 에이전트 - 실제 LLM + MCP 도구를 활용하는 지능형 에이전트"""
    
    def __init__(self):
        self.agent_name = "DH Document Generator Agent"
        # MCP Runner Client 사용 (sub_agent_1.py 방식)
        self.mcp_client = MCPRunnerClient()
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
            
            # MCP 도구들 로드 (이미 MCPToolExecutor 형태로 반환됨)
            self.mcp_tools = await self.mcp_client.initialize_from_config()
            
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

            # AI가 한 번에 처리 방법과 실행 계획 결정
            execution_plan = await self._decide_mcp_execution(query)

            if execution_plan.get("use_mcp", False):
                # MCP 도구를 사용한 처리
                async for result in self._execute_mcp_with_plan(execution_plan, query, context_id):
                    yield result
            else:
                # LLM 직접 사용 (컨텍스트 포함)
                async for result in self._process_with_llm(query, context_id):
                    yield result

        except Exception as e:
            logger.error(f"DhAgent stream 오류: {e}")
            yield {
                'content': f'처리 중 오류가 발생했습니다: {str(e)}',
                'is_task_complete': True,
                'response_type': 'text'
            }

    async def _decide_mcp_execution(self, query: str) -> Dict[str, Any]:
        """AI가 쿼리를 분석해서 MCP 도구 사용 여부와 실행 계획을 한 번에 결정"""
        if not self.mcp_tools or not self.genai_client:
            return {"use_mcp": False}

        try:
            # 프롬프트 매니저에서 프롬프트 가져오기
            decision_prompt = AgentPrompts.get_mcp_decision_and_execution_prompt(query, self.mcp_tools)

            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=decision_prompt,
                config={'temperature': 0.1}
            )

            if not response.text:
                return {"use_mcp": False}

            # JSON 파싱 - 코드 블록 마커 제거
            import json
            try:
                response_text = response.text.strip()

                # ```json ... ``` 형태의 코드 블록 제거
                if response_text.startswith('```json'):
                    # ```json으로 시작하는 경우
                    response_text = response_text[7:]  # '```json' 제거
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]  # 끝의 '```' 제거
                elif response_text.startswith('```'):
                    # ```으로 시작하는 경우
                    response_text = response_text[3:]  # '```' 제거
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]  # 끝의 '```' 제거

                # 앞뒤 공백 제거
                response_text = response_text.strip()

                decision_data = json.loads(response_text)
                logger.info(f"MCP 실행 결정: {decision_data}")
                return decision_data
            except json.JSONDecodeError:
                logger.error(f"JSON 파싱 실패: {response.text}")
                return {"use_mcp": False}

        except Exception as e:
            logger.error(f"MCP 실행 결정 실패: {e}")
            return {"use_mcp": False}

    async def _execute_mcp_with_plan(self, execution_plan: Dict[str, Any], query: str, context_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """실행 계획에 따라 MCP 도구 실행"""
        
        try:
            tool_name = execution_plan.get("tool_name")
            server_name = execution_plan.get("server_name")
            arguments = execution_plan.get("arguments", {})
            
            if not tool_name or not server_name:
                # 계획이 불완전한 경우 LLM으로 fallback
                async for result in self._process_with_llm(query, context_id):
                    yield result
                return
                
            yield {
                'content': f'{tool_name} 도구를 사용하여 분석하고 있습니다...',
                'is_task_complete': False,
                'response_type': 'text'
            }
            
            # MCP 도구 실행
            result = await self.mcp_client.execute_mcp_tool(server_name, tool_name, arguments)
            
            # 결과 처리
            if result['status'] == 'success':
                content = result.get('result', '')
                
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
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"MCP 도구 실행 실패: {error_msg}")
                
                # MCP 실패시 LLM으로 fallback
                fallback_query = f"다음 요청에 대해 답변해주세요: {query}"
                async for result in self._process_with_llm(fallback_query, context_id):
                    yield result
                    
        except Exception as e:
            logger.error(f"MCP 실행 계획 처리 중 오류: {e}")
            # 오류 발생시 LLM으로 fallback
            async for result in self._process_with_llm(query, context_id):
                yield result
    
    
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

            # 프롬프트 매니저에서 프롬프트 가져오기
            format_prompt = AgentPrompts.get_mcp_response_format_prompt(original_query, actual_content)

            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=format_prompt,
                config={'temperature': 0.3}
            )

            if response.text:
                # 응답 텍스트 정리
                cleaned_response = self._clean_response_text(response.text)
                return cleaned_response
            else:
                return actual_content

        except Exception as e:
            logger.error(f"응답 포맷팅 오류: {e}")
            return "죄송합니다. 웹페이지 분석 중 문제가 발생했습니다."

    def _clean_response_text(self, text: str) -> str:
        """응답 텍스트에서 불필요한 공백과 줄바꿈 정리"""
        if not text:
            return text
            
        # 여러 줄바꿈을 최대 2개로 제한
        import re
        
        # 연속된 공백을 하나로 정리
        cleaned = re.sub(r' +', ' ', text)
        
        # 연속된 줄바꿈을 최대 2개로 제한 (단락 구분용)
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        # 줄 시작과 끝의 공백 제거
        lines = cleaned.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        
        # 빈 줄이 너무 많은 경우 정리
        result_lines = []
        consecutive_empty = 0
        
        for line in cleaned_lines:
            if line == '':
                consecutive_empty += 1
                if consecutive_empty <= 1:  # 최대 1개의 빈 줄만 허용
                    result_lines.append(line)
            else:
                consecutive_empty = 0
                result_lines.append(line)
        
        # 앞뒤 빈 줄 제거
        while result_lines and result_lines[0] == '':
            result_lines.pop(0)
        while result_lines and result_lines[-1] == '':
            result_lines.pop()
            
        return '\n'.join(result_lines)
        # """MCP 도구 결과를 자연스러운 응답으로 변환"""
        # try:
        #     # MCP 응답에서 실제 텍스트 추출
        #     if hasattr(content, 'content') and content.content:
        #         # MCP CallToolResult 객체인 경우
        #         actual_content = content.content[0].text if content.content else str(content)
        #     elif 'content=' in str(content) and 'TextContent' in str(content):
        #         # 문자열로 된 MCP 결과에서 텍스트 추출
        #         import re
        #         text_match = re.search(r"text='([^']+)'", str(content))
        #         actual_content = text_match.group(1) if text_match else str(content)
        #     else:
        #         actual_content = str(content)
        #
        #     # 프롬프트 매니저에서 프롬프트 가져오기
        #     format_prompt = AgentPrompts.get_mcp_response_format_prompt(original_query, actual_content)
        #
        #     response = self.genai_client.models.generate_content(
        #         model='gemini-2.0-flash',
        #         contents=format_prompt,
        #         config={'temperature': 0.3}
        #     )
        #
        #     if response.text:
        #         # 응답 텍스트 정리
        #         cleaned_response = self._clean_response_text(response.text)
        #         return cleaned_response
        #     else:
        #         return actual_content
        #
        # except Exception as e:
        #     logger.error(f"응답 포맷팅 오류: {e}")
        #     return "죄송합니다. 웹페이지 분석 중 문제가 발생했습니다."
    
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

            # 사용자 친화적인 오류 메시지 생성
            friendly_message = self._get_friendly_error_message(str(e))

            yield {
                'content': friendly_message,
                'is_task_complete': True,
                'response_type': 'text'
            }

    def _get_friendly_error_message(self, error_str: str) -> str:
        """기술적인 오류 메시지를 사용자 친화적인 메시지로 변환"""
        
        # 503 서버 과부하 오류
        if "503" in error_str and "overloaded" in error_str.lower():
            return "현재 AI 서비스가 많은 요청으로 인해 일시적으로 사용량이 많습니다. 잠시 후 다시 시도해주세요."
        
        # 429 요청 제한 오류
        if "429" in error_str or "quota" in error_str.lower() or "limit" in error_str.lower():
            return "요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
        
        # 401 인증 오류
        if "401" in error_str or "unauthorized" in error_str.lower():
            return "인증 문제가 발생했습니다. 시스템 관리자에게 문의해주세요."
        
        # 400 잘못된 요청
        if "400" in error_str or "bad request" in error_str.lower():
            return "요청을 처리하는 중 문제가 발생했습니다. 다시 시도해주세요."
        
        # 네트워크 관련 오류
        if any(keyword in error_str.lower() for keyword in ["network", "connection", "timeout", "연결"]):
            return "네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인하고 다시 시도해주세요."
        
        # 일반적인 오류
        return "일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        """Gemini LLM을 사용한 처리"""

        # try:
        #     # 대화 기록 조회
        #     conversation = self.conversation_history.get(context_id, [])
        #
        #     # 프롬프트 생성 (대화 기록 포함)
        #     system_prompt = AgentPrompts.get_general_assistant_prompt("")
        #
        #     # 대화 기록을 프롬프트에 포함
        #     conversation_context = ""
        #     if len(conversation) > 1:  # 현재 메시지 외에 이전 대화가 있는 경우
        #         conversation_context = "\n\n=== 이전 대화 기록 ===\n"
        #         for msg in conversation[:-1]:  # 마지막 메시지(현재 질문) 제외
        #             role = "사용자" if msg['role'] == 'user' else "어시스턴트"
        #             conversation_context += f"{role}: {msg['content']}\n"
        #         conversation_context += "==================\n"
        #
        #     full_prompt = f"{system_prompt}{conversation_context}\n\n사용자 질문: {query}"
        #
        #     yield {
        #         'content': 'AI가 응답을 생성 중입니다...',
        #         'is_task_complete': False,
        #         'response_type': 'text'
        #     }
        #
        #     # Gemini 2.0 Flash로 응답 생성
        #     response = self.genai_client.models.generate_content(
        #         model='gemini-2.0-flash',
        #         contents=full_prompt,
        #         config={'temperature': 0.7}
        #     )
        #
        #     content = response.text if response.text else "응답을 생성할 수 없습니다."
        #
        #     # 어시스턴트 응답을 대화 기록에 추가
        #     self.conversation_history[context_id].append({
        #         'role': 'assistant',
        #         'content': content
        #     })
        #
        #     # 구조화된 콘텐츠인지 판단
        #     response_type = 'data' if self._is_structured_content(content) else 'text'
        #
        #     yield {
        #         'content': content,
        #         'is_task_complete': True,
        #         'response_type': response_type
        #     }
        #
        # except Exception as e:
        #     logger.error(f"LLM 처리 오류: {e}")
        #
        #     # 사용자 친화적인 오류 메시지 생성
        #     friendly_message = self._get_friendly_error_message(str(e))
        #
        #     yield {
        #         'content': friendly_message,
        #         'is_task_complete': True,
        #         'response_type': 'text'
        #     }
    
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