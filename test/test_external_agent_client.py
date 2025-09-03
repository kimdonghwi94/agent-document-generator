#!/usr/bin/env python3
"""
External agent client test - simulates how another agent would use this agent
"""

import asyncio
import aiohttp
import json


class ExternalAgentClient:
    """외부 agent가 현재 agent를 사용하는 클라이언트"""
    
    def __init__(self, agent_url: str = "http://localhost:8004"):
        self.agent_url = agent_url
    
    async def get_agent_card(self) -> dict:
        """Agent card 정보 조회"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/.well-known/agent-card.json") as resp:
                return await resp.json()
    
    async def send_streaming_message(self, content: str, context_id: str = "test_context"):
        """A2A protocol 스트리밍 메시지 전송"""
        import uuid
        
        payload = {
            "jsonrpc": "2.0",
            "method": "message/stream",
            "params": {
                "message": {
                    "messageId": str(uuid.uuid4()),
                    "role": "user", 
                    "parts": [{"type": "text", "text": content}],
                    "context": {"id": context_id}
                }
            },
            "id": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.agent_url}/",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                async for line in resp.content:
                    line_str = line.decode().strip()
                    if line_str.startswith("data: "):
                        data = line_str[6:]
                        if data and data != "[DONE]":
                            try:
                                yield json.loads(data)
                            except json.JSONDecodeError:
                                continue


async def test_external_agent_usage():
    """외부 agent가 현재 agent를 사용하는 테스트"""
    
    client = ExternalAgentClient()
    
    test_questions = [
        "소크라테스는 어떤 사람인가요?",
        "https://www.dctestlab.or.kr/u/main/main.do 이 웹사이트를 md 파일로 추출해주세요",
        "https://www.dctestlab.or.kr/u/platform/exhibits.do 여기에서 문의하려면 어디로 연락해야 하나요?"
    ]
    
    try:
        # Agent card 조회
        agent_card = await client.get_agent_card()
        
        for i, question in enumerate(test_questions, 1):
            # 스트리밍 메시지 전송 및 응답 수집
            full_response = ""
            async for event in client.send_streaming_message(question, f"context_{i}"):
                # JSON-RPC 응답 처리
                print(event)
                if event.get("result"):
                    result = event["result"]
                    
                    # artifact-update 처리
                    if result.get("kind") == "artifact-update":
                        artifact = result.get("artifact", {})
                        parts = artifact.get("parts", [])
                        for part in parts:
                            if part.get("kind") == "text":
                                full_response += part.get("text", "")
                    
                    # status-update 처리 - completed 확인
                    elif result.get("kind") == "status-update" and result.get("final"):
                        status = result.get("status", {})
                        if status.get("state") == "completed":
                            break
            
            # 결과 출력
            if full_response.strip():
                if question.startswith("https://") and "md 파일로 추출" in question:
                    # MD 파일로 저장
                    with open(f"./output_question_{i}.md", "w", encoding="utf-8") as f:
                        f.write(full_response)
                else:
                    # 텍스트 답변 저장
                    with open(f"./output_question_{i}.txt", "w", encoding="utf-8") as f:
                        f.write(full_response)
    
    except Exception as e:
        with open("./error_log.txt", "w") as f:
            f.write(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_external_agent_usage())