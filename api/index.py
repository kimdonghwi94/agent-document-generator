import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from agent_document_generator.__main__ import create_app

app = create_app()
