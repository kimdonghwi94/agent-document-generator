"""Main entry point for the Document Generator Agent."""

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_document_generator.agent_executor import DocumentGeneratorAgentExecutor
from agent_document_generator.config import Config


def create_skills_from_mcp():
    """Create skills dynamically from MCP server configuration."""
    config = Config()
    mcp_config = config.load_mcp_config()
    skills = []
    
    # Base document generation skills
    html_skill = AgentSkill(
        id='generate_html',
        name='HTML Document Generation',
        description='Generate comprehensive HTML documents from user queries using LLM',
        tags=['html', 'document', 'generation', 'llm'],
        examples=[
            'Create an HTML page about quantum computing',
            'Generate HTML documentation for Python functions',
            'Make an HTML guide for beginners'
        ],
    )
    
    markdown_skill = AgentSkill(
        id='generate_markdown',
        name='Markdown Document Generation', 
        description='Generate well-structured Markdown documents from user queries using LLM',
        tags=['markdown', 'document', 'generation', 'llm'],
        examples=[
            'Create a markdown guide for Python beginners',
            'Generate markdown documentation for APIs',
            'Make a markdown tutorial about machine learning'
        ],
    )
    
    skills.extend([html_skill, markdown_skill])
    
    # Add MCP server skills
    for name, server_config in mcp_config.get("mcpServers", {}).items():
        description = server_config.get("description", f"Use {name} MCP server for enhanced functionality")
        
        if name == "mcp-pandoc":
            skill = AgentSkill(
                id=f'mcp_{name.replace("-", "_")}',
                name='Document Format Conversion',
                description='Convert documents between different formats (HTML, Markdown, PDF, etc.) using Pandoc',
                tags=['pandoc', 'conversion', 'format', 'mcp'],
                examples=[
                    'Convert this HTML to Markdown',
                    'Generate a PDF version of this document',
                    'Convert Markdown to HTML with better formatting'
                ],
            )
        elif name == "mcp-filesystem":
            skill = AgentSkill(
                id=f'mcp_{name.replace("-", "_")}',
                name='File System Operations',
                description='Save, read, and manage generated documents in the file system',
                tags=['filesystem', 'files', 'storage', 'mcp'],
                examples=[
                    'Save this document to a specific location',
                    'Read an existing document for reference',
                    'Organize generated files by category'
                ],
            )
        elif name == "markdownify":
            skill = AgentSkill(
                id=f'mcp_{name}',
                name='HTML to Markdown Conversion',
                description='Convert HTML content to clean, well-formatted Markdown',
                tags=['html', 'markdown', 'conversion', 'mcp'],
                examples=[
                    'Convert this HTML page to Markdown',
                    'Clean up HTML and make it Markdown',
                    'Extract content from HTML as Markdown'
                ],
            )
        elif name == "playwright":
            skill = AgentSkill(
                id=f'mcp_{name}',
                name='Web Content Extraction',
                description='Extract content from web pages and integrate into generated documents',
                tags=['web', 'scraping', 'extraction', 'playwright', 'mcp'],
                examples=[
                    'Extract content from this URL and create a document',
                    'Get the latest information from a website',
                    'Take screenshots and include in documentation'
                ],
            )
        else:
            # Generic MCP server skill
            skill = AgentSkill(
                id=f'mcp_{name.replace("-", "_")}',
                name=f'{name.title()} Integration',
                description=description,
                tags=[name, 'mcp', 'integration'],
                examples=[
                    f'Use {name} to enhance my document',
                    f'Apply {name} functionality to this task'
                ],
            )
        
        skills.append(skill)
    
    return skills


def create_app():
    """Creates and configures the A2AStarletteApplication instance."""
    config = Config()

    # Create skills dynamically from MCP configuration
    all_skills = create_skills_from_mcp()

    # Create agent card
    agent_card = AgentCard(
        name='Document Generator Agent',
        description='Generates HTML and Markdown documents from user queries using LLM and MCP servers',
        url=f'http://localhost:{config.PORT}/',
        version='1.0.0',
        default_input_modes=['text', 'text/plain'],
        default_output_modes=['text', 'application/json'],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
            state_transition_history=False
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

    @app.route("/")
    async def root(request):
        return {"status": "ok"}

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
