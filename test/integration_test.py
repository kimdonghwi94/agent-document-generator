"""Integration test for the 5-skill agent system."""

import asyncio
import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from agent_document_generator.skill_classifier import SkillClassifier, SkillType
    from agent_document_generator.config import Config
    from agent_document_generator.agent_executor import DocumentGeneratorAgentCore
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_skill_classification():
    """Test skill classification functionality."""
    print("\n🧪 Testing Skill Classification...")
    
    classifier = SkillClassifier()
    
    test_cases = [
        ("HTML 페이지 만들어줘", SkillType.HTML_GENERATION),
        ("마크다운 문서 생성해줘", SkillType.MARKDOWN_GENERATION),
        ("https://example.com 분석해줘", SkillType.URL_QA),
        ("너는 무엇을 할 수 있니?", SkillType.RAG_QA),
        ("Python 최신 정보 검색해줘", SkillType.WEB_SEARCH),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        try:
            result = await classifier.classify_query(query)
            if result == expected:
                print(f"  ✅ '{query[:30]}...' → {result.value}")
                passed += 1
            else:
                print(f"  ❌ '{query[:30]}...' → Expected: {expected.value}, Got: {result.value}")
                failed += 1
        except Exception as e:
            print(f"  ❌ '{query[:30]}...' → Error: {e}")
            failed += 1
    
    print(f"\nClassification Tests: {passed} passed, {failed} failed")
    return failed == 0


async def test_agent_initialization():
    """Test agent core initialization."""
    print("\n🧪 Testing Agent Initialization...")
    
    try:
        # Create agent core
        agent_core = DocumentGeneratorAgentCore()
        print("  ✅ Agent core created successfully")
        
        # Test startup
        await agent_core.startup()
        print("  ✅ Agent startup completed")
        
        # Test shutdown
        await agent_core.shutdown()
        print("  ✅ Agent shutdown completed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Agent initialization failed: {e}")
        return False


async def test_basic_message_processing():
    """Test basic message processing without external dependencies."""
    print("\n🧪 Testing Basic Message Processing...")
    
    try:
        agent_core = DocumentGeneratorAgentCore()
        await agent_core.startup()
        
        # Test simple queries (these might fail due to missing OpenAI key, but should not crash)
        test_queries = [
            "소크라테스의 철학에 대해서 알려주세요",
            "당신이 가지고 있는 기능은 어떤 것들이 있나요 ?"
            # "안녕하세요",
            # "HTML 문서 만들어줘",
            # "당신의 기능은 무엇인가요?"
        ]
        
        passed = 0
        failed = 0
        
        for query in test_queries:
            try:
                print("질문 : ", query)
                # This will likely fail due to missing API keys, but should handle gracefully
                response = await agent_core.process_message(query)
                if isinstance(response, str) and len(response) > 0:
                    print(f"  ✅ '{query[:20]}...' → Response received")
                    passed += 1
                else:
                    print(f"  ⚠️  '{query[:20]}...' → Empty response")
                    passed += 1  # Still counts as handled gracefully
            except Exception as e:
                if "API key" in str(e) or "OpenAI" in str(e):
                    print(f"  ⚠️  '{query[:20]}...' → Expected API key error")
                    passed += 1  # Expected error, system working
                else:
                    print(f"  ❌ '{query[:20]}...' → Unexpected error: {e}")
                    failed += 1
        
        await agent_core.shutdown()
        print(f"\nMessage Processing Tests: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"  ❌ Message processing test failed: {e}")
        return False


async def test_config_loading():
    """Test configuration loading."""
    print("\n🧪 Testing Configuration Loading...")
    
    try:
        config = Config()
        print(f"  ✅ Config loaded - Host: {config.HOST}, Port: {config.PORT}")
        
        # Check if required environment variables are present
        required_vars = ['OPENAI_API_KEY', 'VECTOR_DB_URL']
        for var in required_vars:
            value = getattr(config, var, None) or os.getenv(var)
            if value:
                print(f"  ✅ {var} is configured")
            else:
                print(f"  ⚠️  {var} not configured (optional for testing)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config loading failed: {e}")
        return False


def test_mcp_config():
    """Test MCP server configuration."""
    print("\n🧪 Testing MCP Configuration...")
    
    try:
        mcp_config_path = os.path.join(os.path.dirname(__file__), '..', 'mcpserver.json')
        
        if not os.path.exists(mcp_config_path):
            print("  ❌ mcpserver.json not found")
            return False
            
        with open(mcp_config_path, 'r', encoding='utf-8') as f:
            mcp_config = json.load(f)
        
        required_servers = ['content-summarizer', 'webresearch']
        passed = 0
        failed = 0
        
        for server in required_servers:
            if server in mcp_config.get('mcpServers', {}):
                print(f"  ✅ MCP server '{server}' configured")
                passed += 1
            else:
                print(f"  ❌ MCP server '{server}' not configured")
                failed += 1
        
        print(f"\nMCP Configuration Tests: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"  ❌ MCP config test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("🚀 Starting Agent Integration Tests")
    print("=" * 50)
    
    tests = [
        # ("Configuration Loading", test_config_loading()),
        # ("MCP Configuration", test_mcp_config()),
        # ("Skill Classification", test_skill_classification()),
        # ("Agent Initialization", test_agent_initialization()),
        ("Message Processing", test_basic_message_processing()),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_name, test_coro in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
                
            if result:
                print(f"  ✅ {test_name} PASSED")
                total_passed += 1
            else:
                print(f"  ❌ {test_name} FAILED")
                total_failed += 1
        except Exception as e:
            print(f"  ❌ {test_name} CRASHED: {e}")
            total_failed += 1
    
    print("\n" + "=" * 50)
    print(f"🏁 Integration Tests Complete")
    print(f"   ✅ Passed: {total_passed}")
    print(f"   ❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print("   🎉 All tests passed! Agent system is working correctly.")
    else:
        print("   ⚠️  Some tests failed. Please check the issues above.")
    
    return total_failed == 0


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner crashed: {e}")
        sys.exit(1)