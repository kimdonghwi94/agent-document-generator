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
