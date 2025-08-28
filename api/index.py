# api/index.py
import sys, logging
from pathlib import Path

logging.warning("PYTHON VERSION: %s", sys.version)

try:
    import a2a
    logging.warning("A2A IMPORT OK: %s", getattr(a2a, "__version__", "unknown"))
except Exception as e:
    logging.error("A2A IMPORT FAILED: %r", e)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from agent_document_generator.__main__ import create_app
app = create_app()
