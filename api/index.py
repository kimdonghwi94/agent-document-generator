# api/index.py  (임시 최소 버전)
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

async def root(request):
    return JSONResponse({"ok": True, "path": str(request.url.path)})

app = Starlette(routes=[
    Route("/", root),
    Route("/health", root),
])
