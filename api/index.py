# api/index.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from agent_document_generator.__main__ import create_app
app = create_app()

# Starlette or FastAPI 상관없이 무조건 루트 라우트 추가
try:
    # FastAPI 스타일
    @app.get("/")
    def healthcheck():
        return {"status": "ok"}
except Exception:
    # Starlette 앱일 경우
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.applications import Starlette

    async def root(request):
        return JSONResponse({"status": "ok"})

    # 앱에 routes가 없으면 fallback으로 교체
    if not hasattr(app, "routes") or not app.routes:
        app = Starlette(routes=[Route("/", root)])
