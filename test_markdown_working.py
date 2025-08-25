"""Test markdown generation without printing problematic unicode."""

import asyncio
import json
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


async def test_markdown_simple():
    """Test markdown generation."""
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient(timeout=90.0) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        
        # Test markdown request
        query = {
            "question": "Create a simple markdown guide about Python variables",
            "format": "markdown"
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
        
        print("Sending markdown request...")
        response = await client.send_message(request)
        print("Markdown document generation completed!")
        
        # Just check if we got a response without printing unicode content
        if hasattr(response, 'response') and response.response:
            print("✅ Markdown generation successful")
        else:
            print("❌ No response received")


if __name__ == "__main__":
    asyncio.run(test_markdown_simple())