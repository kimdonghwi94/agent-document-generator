#!/usr/bin/env python3
"""
MCP 서버 단독 테스트 - MCP 서버 연결 및 도구 실행만 테스트
"""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server_direct():
    """MCP 서버에 직접 연결하여 테스트"""
    
    # mcpserver.json 설정 읽기
    config_path = project_root / "mcpserver.json"
    
    if not config_path.exists():
        print(f"[ERROR] MCP 설정 파일을 찾을 수 없음: {config_path}")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] MCP 설정 파일 읽기 실패: {e}")
        return
    
    servers = config.get("mcpServers", {})
    
    if not servers:
        print("[ERROR] MCP 서버 설정이 없습니다")
        return
    
    print(f"[INFO] 발견된 MCP 서버: {list(servers.keys())}")
    
    # 각 서버별로 테스트
    for server_name, server_config in servers.items():
        print(f"\n[TEST] 서버 '{server_name}' 테스트 시작...")
        await test_single_mcp_server(server_name, server_config)


async def test_single_mcp_server(server_name: str, server_config: dict):
    """단일 MCP 서버 테스트"""
    
    command = server_config.get("command")
    args = server_config.get("args", [])
    env = server_config.get("env", {})
    
    if not command:
        print(f"   [ERROR] 서버 '{server_name}'에 명령어가 없음")
        return
    
    print(f"   [INFO] 명령어: {command}")
    print(f"   [INFO] 인수: {args}")
    print(f"   [INFO] 환경변수: {env}")
    
    try:
        # StdioServerParameters 생성
        params = StdioServerParameters(
            command=command,
            args=args,
            env=env if env else None
        )
        
        print(f"   [INFO] 서버 연결 중...")
        
        # MCP 서버에 연결
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                print(f"   [SUCCESS] 연결 성공!")
                
                # 초기화
                print(f"   [INFO] 초기화 중...")
                await session.initialize()
                print(f"   [SUCCESS] 초기화 완료!")
                
                # 도구 목록 가져오기
                print(f"   [INFO] 도구 목록 조회 중...")
                tool_list = await session.list_tools()
                tools = list(tool_list.tools)
                
                print(f"   [SUCCESS] 도구 {len(tools)}개 발견:")
                for i, tool in enumerate(tools, 1):
                    print(f"      {i}. {tool.name} - {getattr(tool, 'description', '설명 없음')}")
                
                # 첫 번째 도구로 테스트 실행 (있다면)
                if tools:
                    await test_tool_execution(session, tools[0], server_name)
                else:
                    print(f"   [WARNING] 사용 가능한 도구가 없습니다")
                
    except Exception as e:
        print(f"   [ERROR] 서버 '{server_name}' 테스트 실패: {e}")
        import traceback
        print(f"   [DEBUG] 상세 오류:")
        traceback.print_exc()


async def test_tool_execution(session: ClientSession, tool, server_name: str):
    """도구 실행 테스트"""
    
    print(f"\n   [TEST] 도구 '{tool.name}' 실행 테스트...")
    
    try:
        # 도구별 테스트 매개변수 설정
        test_args = {}
        
        if "url_to_markdown" in tool.name:
            test_args = {"url": "https://www.dctestlab.or.kr/u/main/main.dom"}
            print(f"      [INFO] 테스트 URL: https://www.google.com")
            
        elif "web_content_qna" in tool.name:
            test_args = {
                "url": "https://www.dctestlab.or.kr/u/main/main.do",
                "question": "이 사이트는 무엇인가요?"
            }
            print(f"      [INFO] 테스트 URL: https://www.google.com")
            print(f"      [INFO] 테스트 질문: 이 사이트는 무엇인가요?")
            
        else:
            print(f"      [WARNING] 알 수 없는 도구 타입 - 기본 인수로 테스트")
            # 기본 테스트는 건너뛰기
            return
        
        # 실제 도구 실행
        print(f"      [INFO] 도구 실행 중...")
        result = await asyncio.wait_for(
            session.call_tool(tool.name, test_args),
            timeout=30.0
        )
        
        print(f"      [SUCCESS] 도구 실행 성공!")
        
        # 결과 출력 (처음 500자만)
        if hasattr(result, 'content') and result.content:
            content = result.content[0].text if result.content else str(result)
            preview = content[:500] + "..." if len(content) > 500 else content
            print(f"      [RESULT] 결과 미리보기:")
            print(f"         {preview}")
        else:
            print(f"      [RESULT] 결과: {str(result)[:200]}...")
            
    except asyncio.TimeoutError:
        print(f"      [TIMEOUT] 도구 실행 시간 초과 (30초)")
    except Exception as e:
        print(f"      [ERROR] 도구 실행 실패: {e}")


async def main():
    """메인 테스트 함수"""
    print("[START] MCP 서버 단독 테스트 시작\n")
    print("=" * 60)
    
    await test_mcp_server_direct()
    
    print("\n" + "=" * 60)
    print("[END] MCP 서버 테스트 완료")


if __name__ == "__main__":
    asyncio.run(main())