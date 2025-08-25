"""Simple test for send_message functionality."""

import asyncio
import json
import logging
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


async def simple_test():
    """Simple test of send_message."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient(timeout=30.0) as httpx_client:
        try:
            # Get agent card
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
            agent_card = await resolver.get_agent_card()
            
            print(f"Agent: {agent_card.name}")
            print(f"Skills: {len(agent_card.skills)}")
            
            # Create client
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
            
            # Simple test message
            payload = {
                'message': {
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': 'Hello, test message!'}],
                    'messageId': uuid4().hex,
                },
            }
            
            request = SendMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**payload)
            )
            
            print("Sending message...")
            response = await client.send_message(request)
            print("Response received:")
            print(response.model_dump(mode='json', exclude_none=True))
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(simple_test())