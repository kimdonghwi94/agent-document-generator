"""개선된 응답 형식 테스트."""

import asyncio
import json
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


async def test_improved_response():
    """개선된 응답 형식 테스트."""
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        
        # 한국어 문서 생성 요청
        payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': 'Python 초보자를 위한 간단한 가이드를 만들어주세요.'}],
                'messageId': uuid4().hex,
            },
        }
        
        request = SendMessageRequest(
            id=str(uuid4()), 
            params=MessageSendParams(**payload)
        )
        
        print("📝 문서 생성 요청 중...")
        response = await client.send_message(request)
        
        # 개선된 응답 형식 출력
        if hasattr(response, 'response') and response.response and response.response.parts:
            response_text = response.response.parts[0].text
            print("\n" + "="*60)
            print("📋 에이전트 응답:")
            print("="*60)
            print(response_text)
            print("="*60)
        else:
            print("❌ 응답을 받지 못했습니다.")


if __name__ == "__main__":
    asyncio.run(test_improved_response())