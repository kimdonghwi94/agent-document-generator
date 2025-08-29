"""Document generation engine using LLM and MCP servers."""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import openai

from .models import UserQuery, DocumentGenerationResponse, DocumentFormat
from .mcp_manager import MCPManager
from .config import Config

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Generates documents from user queries using LLM and MCP servers."""
    
    def __init__(self, config: Config, mcp_manager: MCPManager):
        self.config = config
        self.mcp_manager = mcp_manager
        self.client = openai.AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=30.0  # 30 second timeout for document generation
        )
    
    async def generate_document(self, query: UserQuery) -> DocumentGenerationResponse:
        """Generate document from user query."""
        try:
            logger.info(f"Generating document with format: {query.format} ({query.format.value})")
            
            # Generate content using LLM
            content = await self._generate_content_with_llm(query)
            logger.info(f"Generated content length: {len(content)} chars, starts with: {content[:100]}...")
            
            # Convert to desired format if needed
            final_content = await self._convert_format(content, query.format)
            logger.info(f"Final content length: {len(final_content)} chars, starts with: {final_content[:100]}...")
            
            # Generate title
            title = await self._generate_title(query.question)
            logger.info(f"Generated title: {title}")
            
            # Save to file
            file_path = await self._save_document(final_content, title, query.format)
            logger.info(f"Saved to file: {file_path}")
            
            return DocumentGenerationResponse(
                content=final_content,
                format=query.format,
                title=title,
                file_path=str(file_path) if file_path else None,
                metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "model": self.config.MODEL_NAME,
                    "original_query": query.question
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate document: {e}")
            raise
    
    async def _generate_content_with_llm(self, query: UserQuery) -> str:
        """Generate content using LLM."""
        system_prompt = self._create_system_prompt(query.format)
        user_prompt = self._create_user_prompt(query)
        
        response = await self.client.chat.completions.create(
            model=self.config.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def _create_system_prompt(self, format: DocumentFormat) -> str:
        """Create system prompt based on output format."""
        base_prompt = """You are an expert document generator. Your task is to create comprehensive, well-structured documents that directly answer user questions."""
        
        if format == DocumentFormat.HTML:
            return f"""{base_prompt}
            
Generate your response as a complete HTML document with:
- Proper HTML5 structure with <!DOCTYPE html>, <html>, <head>, and <body> tags
- A descriptive <title> tag
- Semantic HTML elements (header, main, section, article, etc.)
- Proper heading hierarchy (h1, h2, h3, etc.)
- Well-formatted content with paragraphs, lists, and other appropriate elements
- Include CSS styling in a <style> tag in the head for better presentation
- Make it visually appealing and professional
- Ensure the content is comprehensive and addresses the user's question thoroughly"""

        elif format == DocumentFormat.MARKDOWN:
            return f"""{base_prompt}
            
Generate your response in Markdown format with:
- Proper heading hierarchy (# ## ### etc.)
- Well-structured content with paragraphs, lists, code blocks, and tables where appropriate
- Use markdown formatting for emphasis (*italic*, **bold**)
- Include code blocks with language specification when showing code
- Use links, images, and other markdown features when relevant
- Make the content comprehensive and well-organized
- Ensure the content thoroughly addresses the user's question"""
        
        return base_prompt
    
    def _create_user_prompt(self, query: UserQuery) -> str:
        """Create user prompt with context."""
        prompt = f"Please create a comprehensive document that answers the following question:\n\n{query.question}"
        
        if query.context:
            prompt += f"\n\nAdditional context:\n{query.context}"
        
        prompt += "\n\nPlease provide a detailed, well-structured response that thoroughly addresses the question."
        
        return prompt
    
    async def _convert_format(self, content: str, target_format: DocumentFormat) -> str:
        """Convert content to target format using MCP servers."""
        # If content is already in the right format or no conversion needed
        if target_format == DocumentFormat.HTML and content.strip().startswith('<!DOCTYPE html>'):
            return content
        elif target_format == DocumentFormat.MARKDOWN and not content.strip().startswith('<!DOCTYPE html>'):
            return content
        
        # Use pandoc for format conversion
        if target_format == DocumentFormat.HTML:
            # Convert from markdown to HTML
            converted = await self.mcp_manager.convert_with_pandoc(content, "markdown", "html5")
            if converted:
                # Wrap in complete HTML document if not already
                if not converted.strip().startswith('<!DOCTYPE html>'):
                    converted = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
{converted}
</body>
</html>"""
                return converted
        
        elif target_format == DocumentFormat.MARKDOWN:
            # Convert from HTML to markdown
            converted = await self.mcp_manager.convert_with_pandoc(content, "html", "markdown")
            if converted:
                return converted
        
        # If conversion failed, return original content
        return content
    
    async def _generate_title(self, question: str) -> str:
        """Generate a title for the document."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Generate a concise, descriptive title (maximum 10 words) for a document that answers the following question. Respond with only the title, no additional text."},
                    {"role": "user", "content": question}
                ],
                temperature=0.5,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to generate title: {e}")
            return "Generated Document"
    
    async def _save_document(self, content: str, title: str, format: DocumentFormat) -> Optional[Path]:
        """Save document to file."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            
            extension = "html" if format == DocumentFormat.HTML else "md"
            filename = f"{timestamp}_{safe_title}.{extension}"
            file_path = self.config.OUTPUT_DIR / filename
            
            # Use MCP filesystem server to save file
            success = await self.mcp_manager.save_file(str(file_path), content)
            
            if success:
                logger.info(f"Document saved to: {file_path}")
                return file_path
            else:
                # Fallback to direct file write
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Document saved to: {file_path} (fallback)")
                return file_path
                
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return None