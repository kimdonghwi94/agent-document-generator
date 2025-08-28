# api/index.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from agent_document_generator.__main__ import create_app
app = create_app()

# 라우트 하나 추가 (테스트용)
try:
    @app.get("/")
    def root():
        return {"status": "ok"}
except Exception:
    pass
