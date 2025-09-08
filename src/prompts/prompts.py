"""Prompt templates for the agent system."""

from typing import Dict, List, Any, Optional
import os
from pathlib import Path


class AgentPrompts:
    """Agent prompt templates manager - loads all prompts from files."""
    
    _prompts_cache: Dict[str, str] = {}
    _prompts_dir = Path(__file__).parent
    
    @classmethod
    def _load_prompt_from_file(cls, prompt_name: str) -> str:
        """Load prompt from file, with caching."""
        if prompt_name in cls._prompts_cache:
            return cls._prompts_cache[prompt_name]
        
        prompt_file = cls._prompts_dir / f"{prompt_name}.txt"
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    cls._prompts_cache[prompt_name] = content
                    return content
            except Exception:
                pass
        
        # Fallback to empty string if file not found
        return ""
    
    @classmethod
    def get_task_planner_prompt(cls, available_tools: str) -> str:
        """Get task planner agent prompt."""
        template = cls._load_prompt_from_file("task_planner")
        return template.format(available_tools=available_tools)
    
    @classmethod
    def get_document_generator_prompt(cls, available_tools: str) -> str:
        """Get document generator agent prompt."""
        template = cls._load_prompt_from_file("document_generator")
        return template.format(available_tools=available_tools)
    
    @classmethod
    def get_general_assistant_prompt(cls, available_tools: str) -> str:
        """Get general assistant agent prompt."""
        template = cls._load_prompt_from_file("general_assistant")
        return template.format(available_tools=available_tools)
    
    @classmethod
    def get_mcp_decision_and_execution_prompt(cls, query: str, available_tools: Dict[str, List]) -> str:
        """MCP 도구 사용 여부 결정 및 실행 계획을 한 번에 생성하는 프롬프트"""
        
        # 도구 정보를 상세하게 포맷팅
        tools_info = []
        
        for server_name, tools in available_tools.items():
            tools_info.append(f"\n=== 서버: {server_name} ===")
            for tool in tools:
                tools_info.append(f"도구명: {tool.name}")
                tools_info.append(f"설명: {tool.description}")
                
                # 입력 스키마 정리
                if tool.inputSchema and isinstance(tool.inputSchema, dict):
                    properties = tool.inputSchema.get('properties', {})
                    required = tool.inputSchema.get('required', [])
                    schema_info = []
                    for prop_name, prop_info in properties.items():
                        req_mark = " (필수)" if prop_name in required else " (선택)"
                        schema_info.append(f"  - {prop_name}: {prop_info.get('description', 'No description')}{req_mark}")
                    if schema_info:
                        tools_info.append(f"입력 파라미터:")
                        tools_info.extend(schema_info)
                
                tools_info.append("")
        
        tools_description = "\n".join(tools_info)
        
        return f"""
다음 사용자 요청을 분석해서, 적절한 처리 방법을 결정해주세요:

사용자 요청: {query}

사용 가능한 MCP 도구들:
{tools_description}

판단 기준:
1. 사용자 요청이 위에 나열된 도구의 기능과 일치하는 경우 → 해당 MCP 도구 사용
2. 일반적인 질문이나 대화인 경우 → LLM 직접 사용

응답 형식 (정확히 이 JSON 형태로만 응답, 다른 텍스트 포함 금지):
{{
  "use_mcp": true/false,
  "tool_name": "도구명",
  "server_name": "서버명",
  "arguments": {{"파라미터명": "값"}}
}}

주의사항:
- 반드시 위에 나열된 정확한 서버명과 도구명을 사용하세요
- JSON만 반환하고 추가 설명은 하지 마세요
"""

    @classmethod
    def get_mcp_response_format_prompt(cls, original_query: str, actual_content: str) -> str:
        """MCP 결과를 자연스러운 응답으로 변환하는 프롬프트"""
        return f"""
다음은 웹 페이지 분석 결과입니다. 사용자의 질문에 맞게 자연스럽고 유용한 한국어 답변으로 정리해주세요:

사용자 질문: {original_query}

분석 결과:
{actual_content}

요구사항:
- 사용자가 이해하기 쉽게 설명
- 핵심 정보만 간결하게 정리
- 도구 이름이나 기술적인 용어는 사용하지 말 것
- 한국어로 자연스럽게 답변
- 만약 관련 정보가 없다면 정중하게 안내
- 모든 분석 결과를 활용하여 완전한 답변 제공
"""

    @classmethod
    def reload_prompts(cls):
        """Clear cache and reload all prompts."""
        cls._prompts_cache.clear()


class LegacyAgentPrompts:
    """Legacy prompt methods for backward compatibility."""

    @staticmethod
    def get_rag_qa_prompt(context: str, query: str) -> dict:
        """Generate RAG Q&A prompt with context and query (legacy method)."""
        return {
            "system": (
                "당신은 AI 문서 생성 에이전트에 대한 질문에 답변하는 전문 어시스턴트입니다. "
                "제공된 컨텍스트를 바탕으로 정확하고 도움이 되는 답변을 제공하세요. "
                "한국어로 친근하고 명확하게 답변하세요."
            ),
            "user": (
                f"다음 정보를 참고하여 질문에 답변해주세요:\n\n"
                f"참고 정보:\n{context}\n\n"
                f"질문: {query}\n\n"
                f"위 정보를 바탕으로 질문에 대해 구체적이고 유용한 답변을 제공해주세요."
            ),
        }

    @staticmethod
    def build_rag_messages(
        context: str,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """Build properly formatted message array for RAG Q&A with context management."""

        # System message with RAG knowledge context
        system_message = {
            "role": "system",
            "content": (
                f"당신은 AI 문서 생성 에이전트에 대한 질문에 답변하는 전문 어시스턴트입니다. "
                f"제공된 지식베이스 정보를 바탕으로 정확하고 도움이 되는 답변을 제공하세요. "
                f"한국어로 친근하고 명확하게 답변하세요.\n\n"
                f"=== 지식베이스 정보 ===\n{context}\n"
                f"=== 지식베이스 정보 끝 ==="
            ),
        }

        messages = [system_message]

        # Add conversation history if provided
        if conversation_history:
            # Limit history to last 10 exchanges to prevent token overflow
            recent_history = conversation_history[
                -20:
            ]  # 10 user + 10 assistant messages
            for msg in recent_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user query
        messages.append({"role": "user", "content": query})

        return messages
