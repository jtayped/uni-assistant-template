"""
Uni Assistant MCP Server entry point.

The MCP server runs Streamable HTTP transport (compatible with Claude Code remote MCP).
API key auth is applied via a pure ASGI middleware (NOT BaseHTTPMiddleware,
which buffers responses and breaks streaming).

Start: uvicorn main:app --host 0.0.0.0 --port 8000
"""
import logging
from urllib.parse import parse_qs

from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_instance import mcp
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Register all tools (import triggers @mcp.tool() decorator registration)
import tools.time_tools      # noqa: F401
import tools.search          # noqa: F401
import tools.subjects        # noqa: F401
import tools.campaigns       # noqa: F401
import tools.logging_tools   # noqa: F401
import tools.ingest          # noqa: F401
import tools.marks           # noqa: F401
import tools.render          # noqa: F401
import tools.export          # noqa: F401
import tools.dashboard       # noqa: F401
import tools.git_sync        # noqa: F401

log.info("All tools registered.")


class APIKeyMiddleware:
    """Pure ASGI middleware — does not buffer, safe for streaming."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path != "/health" and settings.API_KEY:
                headers = {k.lower(): v for k, v in scope.get("headers", [])}
                api_key = headers.get(b"x-api-key", b"").decode()

                if not api_key:
                    qs = scope.get("query_string", b"").decode()
                    api_key = parse_qs(qs).get("api_key", [""])[0]

                if api_key != settings.API_KEY:
                    log.warning("Unauthorized: %s %s", scope.get("method"), path)
                    await send({
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [[b"content-type", b"text/plain"]],
                    })
                    await send({"type": "http.response.body", "body": b"Unauthorized"})
                    return

        await self.app(scope, receive, send)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": "uni-assistant"})


# mcp_asgi must be the effective top-level app so its lifespan runs and the
# StreamableHTTPSessionManager task group is initialized before any requests arrive.
# We inject /health directly into its router rather than wrapping in another Starlette.
mcp_asgi = mcp.streamable_http_app()
mcp_asgi.add_route("/health", health, methods=["GET"])

app = APIKeyMiddleware(mcp_asgi)

log.info(
    "Server ready — API key auth: %s",
    "enabled" if settings.API_KEY else "DISABLED (set API_KEY in .env)",
)
