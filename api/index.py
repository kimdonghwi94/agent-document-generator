# api/index.py
import sys, logging
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

# 진단용: 파이썬 버전/에러를 배포 로그에 남김
logging.warning("PYTHON START OK")

try:
    # 네가 만든 앱을 그대로 로드
    from agent_document_generator.__main__ import create_app
    app = create_app()  # Starlette/FastAPI 상관없음 (ASGI면 OK)

    # 테스트용 루트 라우트(없으면 404라서 임시로 추가)
    try:
        # FastAPI라면
        @app.get("/")
        def _root():
            return {"status": "ok"}
    except Exception:
        # Starlette라면
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        from starlette.applications import Starlette

        async def root(request):
            return JSONResponse({"status": "ok"})

        # app이 Starlette면 위가 필요 없지만, 혹시 라우트가 없다면 보강
        if not hasattr(app, "routes") or not app.routes:
            app = Starlette(routes=[Route("/", root), Route("/health", root)])

except Exception as e:
    # 네 앱 로드가 실패해도 절대 404로 안 끝나게, 최소 응답 보장
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.applications import Starlette

    logging.exception("APP_LOAD_FAILED")
    async def fallback(request):
        return JSONResponse({"status": "fallback", "error": str(e)}, status_code=500)

    app = Starlette(routes=[Route("/", fallback), Route("/health", fallback)])
