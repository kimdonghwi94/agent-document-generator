"""Tests for skill classifier functionality."""

import pytest
import asyncio
from unittest.mock import Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent_document_generator.skill_classifier import SkillClassifier, SkillType


class TestSkillClassifier:
    """Test cases for SkillClassifier."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SkillClassifier()

    def test_html_generation_classification(self):
        """Test HTML generation skill classification."""
        test_cases = [
            "HTML 페이지 만들어줘",
            "html 문서 생성해줘",
            "Create an HTML document about Python",
            "웹페이지 생성해줘",
            "generate html file"
        ]
        
        for query in test_cases:
            result = asyncio.run(self.classifier.classify_query(query))
            assert result == SkillType.HTML_GENERATION, f"Failed for query: {query}"

    def test_markdown_generation_classification(self):
        """Test Markdown generation skill classification."""
        test_cases = [
            "마크다운 문서 만들어줘",
            "markdown 파일 생성해줘", 
            "Create a markdown guide",
            "md 문서 작성해줘",
            "generate markdown documentation"
        ]
        
        for query in test_cases:
            result = self.classifier.classify_query(query)
            assert result == SkillType.MARKDOWN_GENERATION, f"Failed for query: {query}"

    def test_url_qa_classification(self):
        """Test URL-based QA skill classification."""
        test_cases = [
            "https://example.com 이 사이트에 대해 설명해줘",
            "www.google.com 분석해줘",
            "다음 URL의 내용은? https://python.org",
            "github.com/user/repo 에 대해 질문있어",
            "이 웹사이트 내용 요약해줘 http://test.com"
        ]
        
        for query in test_cases:
            result = self.classifier.classify_query(query)
            assert result == SkillType.URL_QA, f"Failed for query: {query}"

    def test_rag_qa_classification(self):
        """Test RAG-based QA skill classification."""
        test_cases = [
            "너는 무엇을 할 수 있니?",
            "당신의 기능은 무엇인가요?",
            "에이전트 소개해줘",
            "What can you do?",
            "Tell me about yourself",
            "자기소개해줘"
        ]
        
        for query in test_cases:
            result = self.classifier.classify_query(query)
            assert result == SkillType.RAG_QA, f"Failed for query: {query}"

    def test_web_search_classification(self):
        """Test web search skill classification."""
        test_cases = [
            "Python 최신 버전 검색해줘",
            "AI 트렌드 찾아봐",
            "최근 기술 뉴스 알아봐",
            "Search for latest Python updates",
            "Find information about quantum computing",
            "조사해줘 머신러닝"
        ]
        
        for query in test_cases:
            result = self.classifier.classify_query(query)
            assert result == SkillType.WEB_SEARCH, f"Failed for query: {query}"

    def test_context_based_classification(self):
        """Test classification with context information."""
        # Test HTML format context
        query = "문서 만들어줘"
        context = {"format": "html"}
        result = self.classifier.classify_query(query, context)
        assert result == SkillType.HTML_GENERATION

        # Test Markdown format context
        context = {"format": "markdown"}
        result = self.classifier.classify_query(query, context)
        assert result == SkillType.MARKDOWN_GENERATION

        # Test MD format context
        context = {"format": "md"}
        result = self.classifier.classify_query(query, context)
        assert result == SkillType.MARKDOWN_GENERATION

    def test_url_extraction(self):
        """Test URL extraction functionality."""
        test_cases = [
            ("Visit https://example.com for more info", True),
            ("Check www.google.com", True),
            ("Go to github.com/user/repo", True),
            ("No URL here", False),
            ("Just some text", False)
        ]
        
        for query, expected in test_cases:
            result = self.classifier._contains_url(query)
            assert result == expected, f"Failed for query: {query}"

    def test_document_generation_detection(self):
        """Test document generation request detection."""
        test_cases = [
            ("문서 생성해줘", True),
            ("파일 만들어줘", True),
            ("Create a document", True),
            ("Generate report", True),
            ("Just asking a question", False),
            ("How are you?", False)
        ]
        
        for query, expected in test_cases:
            result = self.classifier._is_document_generation_request(query.lower())
            assert result == expected, f"Failed for query: {query}"

    def test_search_request_detection(self):
        """Test search request detection."""
        test_cases = [
            ("검색해줘", True),
            ("찾아봐", True),
            ("Search for something", True),
            ("Find information", True),
            ("최신 정보 알려줘", True),
            ("문서 만들어줘", False),
            ("How are you?", False)
        ]
        
        for query, expected in test_cases:
            result = self.classifier._is_search_request(query.lower())
            assert result == expected, f"Failed for query: {query}"

    def test_skill_description(self):
        """Test skill description retrieval."""
        descriptions = {
            SkillType.HTML_GENERATION: "HTML 문서 생성",
            SkillType.MARKDOWN_GENERATION: "Markdown 문서 생성",
            SkillType.URL_QA: "URL 기반 질의응답",
            SkillType.RAG_QA: "에이전트 정보 질의응답",
            SkillType.WEB_SEARCH: "웹 검색"
        }
        
        for skill_type, expected_desc in descriptions.items():
            result = self.classifier.get_skill_description(skill_type)
            assert result == expected_desc

    def test_default_classification(self):
        """Test default classification behavior."""
        # General questions should default to RAG QA
        general_questions = [
            "안녕하세요",
            "Hello",
            "질문이 있어요",
            "Can you help me?"
        ]
        
        for query in general_questions:
            result = self.classifier.classify_query(query)
            assert result == SkillType.RAG_QA, f"Failed for query: {query}"

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty query
        result = self.classifier.classify_query("")
        assert result == SkillType.RAG_QA

        # Very long query
        long_query = "이것은 매우 긴 질문입니다. " * 100 + "HTML 문서 만들어줘"
        result = self.classifier.classify_query(long_query)
        assert result == SkillType.HTML_GENERATION

        # Mixed language query
        mixed_query = "Create HTML 문서 about Python programming"
        result = self.classifier.classify_query(mixed_query)
        assert result == SkillType.HTML_GENERATION


if __name__ == "__main__":
    pytest.main([__file__])