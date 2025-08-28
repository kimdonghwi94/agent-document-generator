
from src.agent_document_generator.__main__ import create_app
app = create_app()

# 최소 헬스체크 라우트 추가 (없으면 404)
try:
    @app.get("/")
    def root():
        return {"status": "ok"}
except Exception:
    pass