"""Test client for the Document Generator Agent using A2A SDK."""

import asyncio
import json
import logging
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH


async def test_agent():
    """Test the document generator agent using A2A SDK."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient() as httpx_client:
        try:
            # Initialize A2A Card Resolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=base_url,
            )
            
            # Fetch Agent Card
            logger.info(f'Fetching agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}')
            agent_card = await resolver.get_agent_card()
            logger.info('Successfully fetched agent card:')
            print(f"Agent Name: {agent_card.name}")
            print(f"Description: {agent_card.description}")
            print(f"Skills: {[skill.name for skill in agent_card.skills]}")
            print("-" * 50)
            
            # Initialize A2A Client
            client = A2AClient(
                httpx_client=httpx_client, 
                agent_card=agent_card
            )
            logger.info('A2AClient initialized.')
            
            # Test 1: HTML Generation
            print("=== Testing HTML Generation ===")
            html_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {
                            'kind': 'text', 
                            'text': json.dumps({
                                "question": "Explain quantum computing in simple terms",
                                "format": "html"
                            })
                        }
                    ],
                    'messageId': uuid4().hex,
                },
            }
            
            html_request = SendMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**html_payload)
            )
            
            html_response = await client.send_message(html_request)
            print("HTML Response received:")
            print(html_response.model_dump(mode='json', exclude_none=True))
            print("-" * 50)
            
            # Test 2: Markdown Generation
            print("=== Testing Markdown Generation ===")
            md_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {
                            'kind': 'text', 
                            'text': json.dumps({
                                "question": "Create a beginner's guide to Python programming",
                                "format": "markdown"
                            })
                        }
                    ],
                    'messageId': uuid4().hex,
                },
            }
            
            md_request = SendMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**md_payload)
            )
            
            md_response = await client.send_message(md_request)
            print("Markdown Response received:")
            print(md_response.model_dump(mode='json', exclude_none=True))
            print("-" * 50)
            
            # Test 3: Plain Text Input
            print("=== Testing Plain Text Input ===")
            text_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {
                            'kind': 'text',
                            'text': 'What is machine learning?'
                        }
                    ],
                    'messageId': uuid4().hex,
                },
            }
            
            text_request = SendMessageRequest(
                id=str(uuid4()), 
                params=MessageSendParams(**text_payload)
            )
            
            text_response = await client.send_message(text_request)
            print("Plain Text Response received:")
            print(text_response.model_dump(mode='json', exclude_none=True))
            
        except Exception as e:
            logger.error(f"Error during testing: {e}", exc_info=True)


if __name__ == "__main__":
    print("Testing Document Generator Agent...")
    print("Make sure the agent is running on http://localhost:8005")
    print("")
    asyncio.run(test_agent())