"""Skill classification system for routing user queries to appropriate skills."""

import logging
import asyncio
import re
from typing import Dict, Any, Optional
from enum import Enum
import openai

from .config import Config
from .prompts import AgentPrompts

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """Available skill types."""
    HTML_GENERATION = "html_generation"
    MARKDOWN_GENERATION = "markdown_generation"
    URL_QA = "url_qa"
    RAG_QA = "rag_qa"
    WEB_SEARCH = "web_search"
    GENERAL_QA = "general_qa"


class SkillClassifier:
    """Classifies user queries and routes them to appropriate skills using LLM."""

    def __init__(self):
        self.config = Config()
        
        # Cache for classification results to avoid repeated LLM calls
        self._classification_cache = {}
        self._cache_max_size = 100

    async def classify_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> SkillType:
        """
        Classify user query and determine which skill should handle it using LLM.
        
        Args:
            query: User query string
            context: Additional context information
            
        Returns:
            SkillType: The appropriate skill to handle the query
        """
        logger.info(f"Classifying query: {query}")
        
        # Quick URL check first (highest priority)
        if self._contains_url(query):
            logger.info("URL detected - routing to URL_QA skill")
            return SkillType.URL_QA
        
        # Use LLM for classification
        try:
            skill_type = await self._classify_with_llm(query)
            logger.info(f"LLM classified query as: {skill_type.value}")
            
            # Check for format override for LLM results
            if context and context.get("format") and self._is_document_generation_request(query.lower()):
                format_type = context["format"].lower()
                if "html" in format_type and skill_type not in [SkillType.GENERAL_QA, SkillType.RAG_QA]:
                    logger.info("HTML format requested for document generation - routing to HTML_GENERATION skill")
                    return SkillType.HTML_GENERATION
                elif ("markdown" in format_type or "md" in format_type) and skill_type not in [SkillType.GENERAL_QA, SkillType.RAG_QA]:
                    logger.info("Markdown format requested for document generation - routing to MARKDOWN_GENERATION skill") 
                    return SkillType.MARKDOWN_GENERATION
            
            return skill_type
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Fallback to general QA for simple questions
            logger.info("Falling back to GENERAL_QA skill due to classification error")
            return SkillType.GENERAL_QA


    async def _classify_with_llm(self, query: str) -> SkillType:
        """Use LLM to classify the query with caching."""
        # Create cache key from normalized query
        cache_key = query.lower().strip()
        
        # Check cache first
        if cache_key in self._classification_cache:
            logger.debug(f"Cache hit for query: {query}")
            return self._classification_cache[cache_key]
        
        try:
            client = openai.AsyncOpenAI(
                api_key=self.config.OPENAI_API_KEY,
                timeout=10.0  # 10 second timeout
            )
            
            # Get classification prompts
            prompts = AgentPrompts.get_skill_classification_prompt(query)
            
            response = await client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                max_tokens=20,  # Reduced tokens for faster response
                temperature=0.0  # Deterministic for classification
            )
            
            classification_result = response.choices[0].message.content.strip().upper()
            logger.info(f"LLM classification result: {classification_result}")
            
            # Map LLM response to SkillType
            skill_mapping = {
                "HTML_GENERATION": SkillType.HTML_GENERATION,
                "MARKDOWN_GENERATION": SkillType.MARKDOWN_GENERATION,
                "URL_QA": SkillType.URL_QA,
                "RAG_QA": SkillType.RAG_QA,
                "WEB_SEARCH": SkillType.WEB_SEARCH,
                "GENERAL_QA": SkillType.GENERAL_QA
            }
            
            result = skill_mapping.get(classification_result, SkillType.RAG_QA)
            
            # Store in cache
            self._store_in_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            return SkillType.RAG_QA

    def _store_in_cache(self, cache_key: str, result: SkillType):
        """Store classification result in cache with size management."""
        # If cache is full, remove oldest entry (simple FIFO)
        if len(self._classification_cache) >= self._cache_max_size:
            # Remove first (oldest) entry
            oldest_key = next(iter(self._classification_cache))
            del self._classification_cache[oldest_key]
            logger.debug(f"Cache full, removed oldest entry: {oldest_key}")
        
        self._classification_cache[cache_key] = result
        logger.debug(f"Stored in cache: {cache_key} -> {result.value}")

    def _contains_url(self, query: str) -> bool:
        """Check if query contains a valid URL."""
        url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*'
        ]
        
        for pattern in url_patterns:
            if re.search(pattern, query):
                return True
        return False

    def _is_document_generation_request(self, query: str) -> bool:
        """Check if query is requesting document generation."""
        generation_keywords = [
            "생성", "만들", "작성", "create", "generate", "make", "write",
            "문서", "document", "파일", "file", "페이지", "page"
        ]
        
        return any(keyword in query for keyword in generation_keywords)

    def _is_search_request(self, query: str) -> bool:
        """Check if query is requesting web search."""
        search_keywords = [
            "검색", "찾", "조사", "search", "find", "research", "look up",
            "최신", "recent", "latest", "news", "정보", "information"
        ]
        
        return any(keyword in query for keyword in search_keywords)

    def get_skill_description(self, skill_type: SkillType) -> str:
        """Get human-readable description of the skill."""
        descriptions = {
            SkillType.HTML_GENERATION: "HTML 문서 생성",
            SkillType.MARKDOWN_GENERATION: "Markdown 문서 생성", 
            SkillType.URL_QA: "URL 기반 질의응답",
            SkillType.RAG_QA: "에이전트 정보 질의응답",
            SkillType.WEB_SEARCH: "웹 검색",
            SkillType.GENERAL_QA: "일반 질의응답"
        }
        return descriptions.get(skill_type, "Unknown skill")