"""Simple test without emojis."""

import asyncio
import json
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


async def test_simple():
    """Simple test."""
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        
        payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': 'Create a simple test document'}],
                'messageId': uuid4().hex,
            },
        }
        
        request = SendMessageRequest(
            id=str(uuid4()), 
            params=MessageSendParams(**payload)
        )
        
        print("Sending request...")
        response = await client.send_message(request)
        print("Response received!")
        
        # Save response to file to avoid console encoding issues
        try:
            # Check response structure
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                result = response.root.result
                if hasattr(result, 'parts') and result.parts:
                    response_text = result.parts[0].root.text
                    with open('response_output.txt', 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    print("Response saved to response_output.txt")
                else:
                    print("No parts in result")
            else:
                print("No result found in response")
        except Exception as e:
            print(f"Error saving response: {e}")
            # Try to extract text from the printed response
            response_str = str(response)
            if 'text=' in response_str:
                start = response_str.find("text='") + 6
                end = response_str.find("'))]", start)
                if start > 5 and end > start:
                    response_text = response_str[start:end]
                    with open('response_output.txt', 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    print("Response extracted and saved to response_output.txt")


if __name__ == "__main__":
    asyncio.run(test_simple())