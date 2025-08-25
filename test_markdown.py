"""Test markdown document generation."""

import asyncio
import json
import logging
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


async def test_markdown_generation():
    """Test markdown document generation."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        try:
            # Get agent card
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()
            
            print(f"Agent: {agent_card.name}")
            
            # Create client
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
            
            # Test with JSON request for markdown format
            query = {
                "question": "Create a comprehensive guide about Python decorators",
                "format": "markdown",
                "context": "Include practical examples and best practices"
            }
            
            payload = {
                'message': {
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': json.dumps(query)}],
                    'messageId': uuid4().hex,
                },
            }
            
            request = SendMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**payload)
            )
            
            print("Requesting markdown document generation...")
            response = await client.send_message(request)
            print("Response received:")
            print(response.model_dump(mode='json', exclude_none=True))
            
            # Parse the response
            response_text = response.response.parts[0].text
            response_data = json.loads(response_text)
            
            print(f"Status: {response_data['status']}")
            print(f"Format: {response_data['format']}")
            print(f"Title: {response_data['title']}")
            print(f"File: {response_data.get('file_path', 'Not saved')}")
            print(f"Content length: {len(response_data['content'])} characters")
            
            # Show first few lines of generated markdown
            content_lines = response_data['content'].split('\n')[:10]
            print("\nFirst 10 lines of generated content:")
            for line in content_lines:
                print(f"  {line}")
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_markdown_generation())