"""Individual skill handlers for the 5 agent skills."""

import logging
import json
import re
import base64
from typing import Dict, Any, Optional, Union
import openai
from urllib.parse import urlparse

from a2a.types import Part, FilePart, FileWithBytes, TextPart

from .config import Config
from .models import UserQuery, DocumentGenerationResponse, DocumentFormat
from .document_generator import DocumentGenerator
from .mcp_manager import MCPManager
from .rag_manager import RAGManager
from .prompts import AgentPrompts

logger = logging.getLogger(__name__)


class SkillHandlers:
    """Handles execution of the 5 agent skills."""

    def __init__(self, config: Config, mcp_manager: MCPManager, document_generator: DocumentGenerator, rag_manager: RAGManager):
        self.config = config
        self.mcp_manager = mcp_manager
        self.document_generator = document_generator
        self.rag_manager = rag_manager

    async def handle_html_generation(self, query: str, context: Optional[Dict[str, Any]] = None) -> Union[str, Dict[str, Any]]:
        """Handle HTML document generation skill."""
        logger.info("Handling HTML generation request")
        
        try:
            # Create UserQuery object
            user_query = UserQuery(
                question=query,
                format=DocumentFormat.HTML,
                context=context
            )
            
            # Generate HTML document
            response = await self.document_generator.generate_document(user_query)
            
            # Create A2A FilePart from document response
            file_part = self._create_file_part(response)
            
            # Create user-friendly message
            user_message = f"""[HTML 문서 생성 완료]

제목: {response.title}
저장 위치: {response.file_path}
생성 시간: {response.metadata.get('generated_at', 'N/A')}

HTML 문서가 성공적으로 생성되어 A2A 프로토콜로 전송됩니다!"""

            # Return complete data with A2A part
            return {
                "text": user_message,
                "part": file_part,
                "response": response  # Include full response data
            }

        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            return f"HTML 문서 생성 중 오류가 발생했습니다: {str(e)}"

    async def handle_markdown_generation(self, query: str, context: Optional[Dict[str, Any]] = None) -> Union[str, Dict[str, Any]]:
        """Handle Markdown document generation skill."""
        logger.info("Handling Markdown generation request")
        
        try:
            # Create UserQuery object
            user_query = UserQuery(
                question=query,
                format=DocumentFormat.MARKDOWN,
                context=context
            )
            
            # Generate Markdown document
            response = await self.document_generator.generate_document(user_query)
            
            # Create A2A FilePart from document response
            file_part = self._create_file_part(response)
            
            # Create user-friendly message
            user_message = f"""[Markdown 문서 생성 완료]

제목: {response.title}
저장 위치: {response.file_path}
생성 시간: {response.metadata.get('generated_at', 'N/A')}

Markdown 문서가 성공적으로 생성되어 A2A 프로토콜로 전송됩니다!"""

            # Return complete data with A2A part
            return {
                "text": user_message,
                "part": file_part,
                "response": response  # Include full response data
            }

        except Exception as e:
            logger.error(f"Markdown generation failed: {e}")
            return f"Markdown 문서 생성 중 오류가 발생했습니다: {str(e)}"

    async def handle_url_qa(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Handle URL-based question answering skill."""
        logger.info("Handling URL QA request")
        
        try:
            # Extract URL from query
            url = self._extract_url(query)
            if not url:
                return "URL을 찾을 수 없습니다. 유효한 URL을 포함해서 다시 질문해 주세요."
            
            # Extract question from query (remove URL)
            question = self._extract_question_from_url_query(query, url)
            
            # Use content-summarizer MCP server
            content_summarizer = self.mcp_manager.get_server("content-summarizer")
            if not content_summarizer:
                return "URL 분석 서비스가 현재 이용할 수 없습니다. 잠시 후 다시 시도해 주세요."
            
            # Use standardized prompt for content summarization
            summarizer_prompt = AgentPrompts.get_mcp_content_summarizer_prompt(url, question)
            
            # Request content summarization
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "summarize-content",
                    "arguments": {
                        "url": url,
                        "query": summarizer_prompt
                    }
                }
            }
            
            mcp_response = await content_summarizer.send_request(mcp_request)
            
            if mcp_response and "result" in mcp_response:
                content_summary = mcp_response["result"]["content"]
                
                # Generate final answer using LLM
                return await self._generate_url_qa_response(url, content_summary, question)
            else:
                return f"URL '{url}' 분석 중 오류가 발생했습니다. URL이 유효한지 확인해 주세요."

        except Exception as e:
            logger.error(f"URL QA failed: {e}")
            return f"URL 기반 질의응답 중 오류가 발생했습니다: {str(e)}"

    async def handle_rag_qa(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Handle RAG-based question answering about the agent."""
        logger.info("Handling RAG QA request")
        
        try:
            # Use RAG manager to generate response
            response = await self.rag_manager.generate_rag_response(query)
            return response

        except Exception as e:
            logger.error(f"RAG QA failed: {e}")
            return f"에이전트 정보 질의응답 중 오류가 발생했습니다: {str(e)}"

    async def handle_web_search(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Handle web search skill."""
        logger.info("Handling web search request")
        
        try:
            # Use webresearch MCP server
            webresearch = self.mcp_manager.get_server("webresearch")
            if not webresearch:
                return "웹 검색 서비스가 현재 이용할 수 없습니다. 잠시 후 다시 시도해 주세요."
            
            # Extract search terms from query
            search_terms = self._extract_search_terms(query)
            
            # Use standardized prompt for web research
            research_prompt = AgentPrompts.get_mcp_web_research_prompt(search_terms)
            
            # Request web search
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "web-search",
                    "arguments": {
                        "query": research_prompt,
                        "max_results": 5
                    }
                }
            }
            
            mcp_response = await webresearch.send_request(mcp_request)
            
            if mcp_response and "result" in mcp_response:
                search_results = mcp_response["result"]["results"]
                
                # Use standardized prompt to format search results
                return await self._format_search_results_with_llm(search_terms, search_results)
            else:
                return f"'{search_terms}' 검색 중 오류가 발생했습니다. 다시 시도해 주세요."

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"웹 검색 중 오류가 발생했습니다: {str(e)}"

    async def handle_general_qa(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Handle general question answering skill."""
        logger.info("Handling general QA request")
        
        try:
            client = openai.AsyncOpenAI(
                api_key=self.config.OPENAI_API_KEY,
                timeout=15.0  # 15 second timeout for general QA
            )
            
            # Use standardized prompts from AgentPrompts
            prompts = AgentPrompts.get_general_qa_prompt(query)

            response = await client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                max_tokens=300,  # Reduced for faster response
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"General QA failed: {e}")
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"

    def _extract_url(self, query: str) -> Optional[str]:
        """Extract URL from query string."""
        url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, query)
            if match:
                url = match.group(0)
                # Ensure URL has protocol
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                return url
        return None

    def _extract_question_from_url_query(self, query: str, url: str) -> str:
        """Extract question part from URL query."""
        # Remove URL from query
        question = query.replace(url, "").strip()
        
        # Simple cleanup - remove leading/trailing whitespace and common particles
        question = question.strip()
        if not question:
            return "이 웹페이지의 내용에 대해 설명해 주세요."
            
        return question

    def _extract_search_terms(self, query: str) -> str:
        """Extract search terms from query."""
        # Simple cleanup - return the query with basic trimming
        search_terms = query.strip()
        return search_terms if search_terms else query

    async def _generate_url_qa_response(self, url: str, content_summary: str, question: str) -> str:
        """Generate final response for URL QA using LLM."""
        try:
            client = openai.AsyncOpenAI(
                api_key=self.config.OPENAI_API_KEY,
                timeout=20.0  # 20 second timeout for URL QA
            )
            
            # Use standardized prompts
            prompts = AgentPrompts.get_url_qa_prompt(url, content_summary, question)

            response = await client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                max_tokens=500,  # Reduced for faster response
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            
            return f"""[URL 기반 질의응답 결과]

📍 분석한 웹페이지: {url}

💡 답변:
{answer}

---
※ 이 답변은 해당 웹페이지의 내용을 분석하여 생성되었습니다."""

        except Exception as e:
            logger.error(f"URL QA response generation failed: {e}")
            return f"URL: {url}\n내용 요약: {content_summary}\n질문: {question}\n\n답변 생성 중 오류가 발생했습니다."

    async def _format_search_results_with_llm(self, search_terms: str, results: list) -> str:
        """Format web search results using LLM with standardized prompts."""
        try:
            if not results:
                return f"'{search_terms}'에 대한 검색 결과를 찾을 수 없습니다."
            
            # Prepare search results for LLM
            results_text = ""
            for i, result in enumerate(results[:5], 1):
                title = result.get("title", "제목 없음")
                url = result.get("url", "")
                snippet = result.get("snippet", result.get("description", "설명 없음"))
                
                results_text += f"[{i}] {title}\nURL: {url}\n설명: {snippet}\n\n"
            
            # Use standardized prompts for formatting
            client = openai.AsyncOpenAI(
                api_key=self.config.OPENAI_API_KEY,
                timeout=15.0  # 15 second timeout for search formatting
            )
            prompts = AgentPrompts.get_web_search_prompt(search_terms, results_text)

            response = await client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                max_tokens=600,  # Reduced for faster response
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"LLM search results formatting failed: {e}")
            # Fallback to simple formatting
            return self._format_search_results_fallback(search_terms, results)

    def _format_search_results_fallback(self, search_terms: str, results: list) -> str:
        """Fallback method for formatting search results without LLM."""
        try:
            if not results:
                return f"'{search_terms}'에 대한 검색 결과를 찾을 수 없습니다."
            
            formatted_results = f"""[웹 검색 결과]

🔍 검색어: {search_terms}
📊 검색 결과: {len(results)}개

"""
            
            for i, result in enumerate(results[:5], 1):
                title = result.get("title", "제목 없음")
                url = result.get("url", "")
                snippet = result.get("snippet", result.get("description", "설명 없음"))
                
                formatted_results += f"""[{i}] {title}
🔗 {url}
📝 {snippet}

"""
            
            formatted_results += "---\n※ 최신 웹 검색 결과입니다. 더 자세한 정보는 해당 링크를 참조하세요."
            
            return formatted_results

        except Exception as e:
            logger.error(f"Fallback search results formatting failed: {e}")
            return f"'{search_terms}' 검색 결과 형식화 중 오류가 발생했습니다."

    def _create_file_part(self, response) -> Part:
        """Create A2A FilePart from document response."""
        # Encode file content as base64
        file_bytes = response.content.encode('utf-8')
        file_b64 = base64.b64encode(file_bytes).decode('utf-8')
        
        # Determine MIME type based on format
        mime_type = "text/html" if response.format.value == "html" else "text/markdown"
        
        # Create filename from title and format
        extension = "html" if response.format.value == "html" else "md"
        filename = f"{response.title.replace(' ', '_')}.{extension}"
        
        # Create FileWithBytes object
        file_with_bytes = FileWithBytes(
            bytes=file_b64,
            mime_type=mime_type,
            name=filename
        )
        
        # Create FilePart
        return Part(root=FilePart(
            file=file_with_bytes,
            metadata={
                "original_title": response.title,
                "generated_at": response.metadata.get('generated_at'),
                "format": response.format.value
            }
        ))