import hmac
import os
from typing import Any

from fastmcp import settings as fastmcp_settings
from load_dotenv import load_dotenv
load_dotenv()

from mcp_server_qdrant.mcp_server import QdrantMCPServer
from mcp_server_qdrant.settings import (
    EmbeddingProviderSettings,
    QdrantSettings,
    ServerSettings,
    ToolSettings,
)

AUTH_BEARER_TOKEN = os.environ.get("AUTH_BEARER_TOKEN", "").strip() or None

mcp = QdrantMCPServer(
    tool_settings=ToolSettings(),
    qdrant_settings=QdrantSettings(),
    server_settings=ServerSettings(),
    embedding_provider_settings=EmbeddingProviderSettings()
)


async def _send_plain_response(
    send: Any,
    status: int,
    body: bytes,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"text/plain; charset=utf-8"),
                *(headers or []),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class BearerAuthMiddleware:
    """ASGI middleware that requires a static Authorization bearer token."""

    def __init__(self, app: Any, token: str) -> None:
        self.app = app
        self._expected = f"Bearer {token}".encode("utf-8")

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        auth_header = b""
        for name, value in scope.get("headers", []):
            if name.lower() == b"authorization":
                auth_header = value
                break

        if not hmac.compare_digest(auth_header, self._expected):
            await _send_plain_response(
                send,
                401,
                b"Unauthorized",
                [(b"www-authenticate", b"Bearer")],
            )
            return

        await self.app(scope, receive, send)


def build_http_app(transport: str | None = None) -> Any:
    """Build the ASGI app for HTTP transports, optionally wrapped with bearer auth."""
    _transport = transport or fastmcp_settings.transport
    if _transport not in ("http", "streamable-http", "sse"):
        _transport = "streamable-http"

    mcp_app = mcp.http_app(transport=_transport)
    if AUTH_BEARER_TOKEN:
        return BearerAuthMiddleware(mcp_app, AUTH_BEARER_TOKEN)
    return mcp_app


app = build_http_app()
