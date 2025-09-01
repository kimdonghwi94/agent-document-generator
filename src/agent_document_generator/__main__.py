"""Main entry point for the Document Generator Agent."""

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
import httpx
from starlette.responses import RedirectResponse
from src.agent_document_generator.agent_executor import DocumentGeneratorAgentExecutor
from src.agent_document_generator.config import Config


def create_agent_skills():
    """Create the 6 main agent skills."""
    skills = []
    
    # Skill 1: HTML Document Generation
    html_skill = AgentSkill(
        id='html_generation',
        name='HTML 문서 생성',
        description='사용자 요청에 따라 구조화된 HTML 문서를 생성합니다',
        tags=['html', 'document', 'generation'],
        examples=[
            'HTML 페이지 만들어줘',
            '양자 컴퓨팅에 대한 HTML 문서 생성',
            'Python 함수 설명서를 HTML로 작성'
        ],
    )
    
    # Skill 2: Markdown Document Generation
    markdown_skill = AgentSkill(
        id='markdown_generation',
        name='Markdown 문서 생성',
        description='깔끔하고 읽기 쉬운 마크다운 문서를 생성합니다',
        tags=['markdown', 'document', 'generation'],
        examples=[
            '마크다운 문서 만들어줘',
            'Python 초보자 가이드를 마크다운으로 작성',
            'API 문서를 마크다운 형식으로 생성'
        ],
    )
    
    # Skill 3: URL-based Q&A
    url_qa_skill = AgentSkill(
        id='url_qa',
        name='URL 기반 질의응답',
        description='제공된 URL의 내용을 분석하여 관련 질문에 답변합니다',
        tags=['url', 'qa', 'analysis', 'mcp'],
        examples=[
            'https://example.com 이 사이트에 대해 설명해줘',
            '다음 URL의 주요 내용은 무엇인가요?',
            '이 웹페이지에서 중요한 정보를 요약해줘'
        ],
    )
    
    # Skill 4: Agent Self Q&A (RAG)
    rag_qa_skill = AgentSkill(
        id='rag_qa',
        name='에이전트 정보 질의응답',
        description='에이전트의 기능과 능력에 대한 질문에 RAG를 활용하여 답변합니다',
        tags=['rag', 'self-knowledge', 'qa'],
        examples=[
            '너는 무엇을 할 수 있니?',
            '당신의 주요 기능은 무엇인가요?',
            '에이전트 소개해줘'
        ],
    )
    
    # Skill 5: Web Search
    web_search_skill = AgentSkill(
        id='web_search',
        name='웹 검색',
        description='최신 정보를 웹에서 검색하여 사용자에게 제공합니다',
        tags=['search', 'web', 'information', 'mcp'],
        examples=[
            'Python 최신 버전 정보 검색해줘',
            '2024년 AI 트렌드 찾아봐',
            '최근 기술 뉴스 알아봐'
        ],
    )
    
    # Skill 6: General Q&A
    general_qa_skill = AgentSkill(
        id='general_qa',
        name='일반 질의응답',
        description='일반적인 질문이나 대화에 자연스럽고 친근하게 응답합니다',
        tags=['general', 'qa', 'conversation'],
        examples=[
            '안녕하세요',
            '오늘 날씨 어때?',
            '간단한 질문이 있어요'
        ],
    )
    
    skills.extend([html_skill, markdown_skill, url_qa_skill, rag_qa_skill, web_search_skill, general_qa_skill])
    
    return skills


def create_app():
    """Creates and configures the A2AStarletteApplication instance."""
    config = Config()

    # Create the 6 main agent skills
    all_skills = create_agent_skills()

    # Create agent card
    agent_card = AgentCard(
        name='Document Generator Agent',
        description='6가지 주요 기능을 제공하는 AI 에이전트: HTML/Markdown 문서 생성, URL 기반 질의응답, 에이전트 정보 질의응답(RAG), 웹 검색, 일반 질의응답',
        url=f'https://agent-document-generator.vercel.app/',
        version='2.0.0',
        default_input_modes=['text', 'text/plain'],
        default_output_modes=['text', 'application/json'],
        capabilities=AgentCapabilities(
            streaming=True,
        ),
        skills=all_skills,
    )

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=DocumentGeneratorAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    app = server.build()

    @app.route("/health")
    async def health(request):
        return JSONResponse({"status": "healthy"})

    @app.route("/", methods=["GET"])
    async def root(request):
        return RedirectResponse(url="https://kimdonghwi94.github.io/dhkim", status_code=302)

    return app


def main():
    """Main entry point for the Document Generator Agent."""
    import uvicorn
    config = Config()
    app = create_app()

    # Run server
    print(f"Starting Document Generator Agent on {config.HOST}:{config.PORT}")
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )


if __name__ == '__main__':
    main()
