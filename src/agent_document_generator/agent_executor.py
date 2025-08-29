"""Document Generator Agent Executor implementation."""

import json
import logging
from typing import Dict, Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_agent_parts_message
from a2a.types import Part, FilePart, FileWithBytes, TextPart
import base64

from .config import Config
from .document_generator import DocumentGenerator
from .mcp_manager import MCPManager
from .models import UserQuery, DocumentFormat
from .skill_classifier import SkillClassifier, SkillType
from .skill_handlers import SkillHandlers
from .rag_manager import RAGManager

logger = logging.getLogger(__name__)


class DocumentGeneratorAgentCore:
    """Core Document Generator Agent logic."""

    def __init__(self):
        self.config = Config()
        self.mcp_manager = MCPManager(self.config)
        self.document_generator = DocumentGenerator(self.config, self.mcp_manager)
        self.rag_manager = RAGManager(self.config)
        self.skill_classifier = SkillClassifier()
        self.skill_handlers = SkillHandlers(
            self.config, 
            self.mcp_manager, 
            self.document_generator, 
            self.rag_manager
        )
        self.startup_complete = False

    async def startup(self):
        """Initialize the agent and start MCP servers."""
        if self.startup_complete:
            return
            
        logger.info("Starting Document Generator Agent...")
        
        # Start MCP servers
        await self.mcp_manager.start_all()
        
        # Initialize RAG system
        await self.rag_manager.initialize()
        
        self.startup_complete = True
        logger.info("Document Generator Agent startup complete")

    async def shutdown(self):
        """Cleanup agent resources."""
        logger.info("Shutting down Document Generator Agent...")
        await self.mcp_manager.stop_all()
        await self.rag_manager.cleanup()

    async def process_message(self, content: str) -> str:
        """Process user message using skill-based routing."""
        try:
            # Ensure agent is started
            if not self.startup_complete:
                await self.startup()

            logger.info(f"Processing message: {content}")

            # Parse the user query to get context
            parsed_query = self._parse_user_query(content)
            context = {
                "format": parsed_query.format.value if parsed_query.format else None,
                "context": parsed_query.context,
                "metadata": parsed_query.metadata
            }
            
            # Classify the query to determine which skill to use
            skill_type = await self.skill_classifier.classify_query(parsed_query.question, context)
            
            logger.info(f"Query classified as: {skill_type.value}")
            print("skill type 은 ",skill_type)
            # Route to appropriate skill handler
            if skill_type == SkillType.HTML_GENERATION:
                response = await self.skill_handlers.handle_html_generation(parsed_query.question, context)
            elif skill_type == SkillType.MARKDOWN_GENERATION:
                response = await self.skill_handlers.handle_markdown_generation(parsed_query.question, context)
            elif skill_type == SkillType.URL_QA:
                response = await self.skill_handlers.handle_url_qa(parsed_query.question, context)
            elif skill_type == SkillType.RAG_QA:
                response = await self.skill_handlers.handle_rag_qa(parsed_query.question, context)
            elif skill_type == SkillType.WEB_SEARCH:
                response = await self.skill_handlers.handle_web_search(parsed_query.question, context)
            elif skill_type == SkillType.GENERAL_QA:
                response = await self.skill_handlers.handle_general_qa(parsed_query.question, context)
            else:
                # Fallback to general QA
                logger.warning(f"Unknown skill type: {skill_type}, falling back to general QA")
                response = await self.skill_handlers.handle_general_qa(parsed_query.question, context)
            print("결과 출력은 : ",response)
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"요청 처리 중 오류가 발생했습니다: {str(e)}"

    def _parse_user_query(self, content: str) -> UserQuery:
        """Parse message content into UserQuery."""
        try:
            # Try to parse as JSON first
            data = json.loads(content)
            logger.info(f"Parsed JSON data: {data}")
            if isinstance(data, dict):
                format_str = data.get("format", "html")
                logger.info(f"Format string: {format_str}")
                return UserQuery(
                    question=data.get("question", content),
                    format=DocumentFormat(format_str),
                    context=data.get("context"),
                    metadata=data.get("metadata")
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.info(f"JSON parsing failed: {e}")
            pass
        
        # Fallback: treat as plain text question
        logger.info(f"Using fallback parsing for: {content}")
        return UserQuery(
            question=content,
            format=DocumentFormat.HTML
        )

    def _format_response(self, response) -> str:
        """Format document generation response for A2A."""
        # Create a user-friendly response instead of raw JSON
        format_name = "HTML" if response.format.value == "html" else response.format.value.upper()
        
        user_message = f"""[문서 생성 완료]

제목: {response.title}
형식: {format_name}  
저장 위치: {response.file_path}
생성 시간: {response.metadata.get('generated_at', 'N/A')}

생성된 문서 미리보기:
{'='*50}
{response.content[:500]}{'...' if len(response.content) > 500 else ''}
{'='*50}

문서가 성공적으로 생성되어 host agent로 전송되었습니다!"""
        
        return user_message
    
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


class DocumentGeneratorAgentExecutor(AgentExecutor):
    """A2A Agent Executor for Document Generator."""

    def __init__(self):
        self.agent = DocumentGeneratorAgentCore()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute document generation request."""
        try:
            # Startup MCP servers if not already done
            if not self.agent.startup_complete:
                await self.agent.startup()
            
            # Get user message from context
            user_message = ""
            if hasattr(context, 'message') and context.message:
                if hasattr(context.message, 'parts') and context.message.parts:
                    for part in context.message.parts:
                        if hasattr(part, 'text'):
                            user_message += part.text
            
            # If no message found, use default
            if not user_message.strip():
                user_message = "Generate a sample document"
            
            logger.info(f"Processing user message: {user_message}")
            
            # Process the message using the agent core
            response = await self.agent.document_generator.generate_document(
                self.agent._parse_user_query(user_message)
            )
            
            # Create message parts - text message + file attachment
            text_response = self.agent._format_response(response)
            file_part = self.agent._create_file_part(response)
            
            # Send text message with file attachment
            text_part = Part(root=TextPart(text=text_response))
            message_parts = [text_part, file_part]
            
            await event_queue.enqueue_event(new_agent_parts_message(message_parts))
            
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            error_message = f"Error generating document: {str(e)}"
            await event_queue.enqueue_event(new_agent_text_message(error_message))

    async def cancel(
        self, 
        context: RequestContext, 
        event_queue: EventQueue
    ) -> None:
        """Cancel operation (not supported)."""
        raise Exception('Cancel operation not supported for document generation')