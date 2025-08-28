# main.py
import os, sys

# Vercel 런타임에서 현재 파일 위치를 sys.path에 넣어 패키지 탐색 보장
sys.path.append(os.path.dirname(__file__))

# __main__.py 가 위치한 실제 경로로 임포트 (output 하위)
from src.agent_document_generator.__main__ import create_app

app = create_app()

# 로컬 개발용 (Vercel 서버리스에서는 실행되지 않음)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
