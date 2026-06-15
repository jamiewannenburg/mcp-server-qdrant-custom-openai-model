import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.client import Client

from mcp_server_qdrant.embeddings.fastembed import FastEmbedProvider
from mcp_server_qdrant.mcp_server import QdrantMCPServer
from mcp_server_qdrant.settings import QdrantSettings, ServerSettings, ToolSettings


@pytest.fixture
def embedding_provider():
    return FastEmbedProvider(model_name="sentence-transformers/all-MiniLM-L6-v2")


def _make_server(
    monkeypatch: pytest.MonkeyPatch,
    *,
    namespace: str = "qdrant",
    search_limit: int = 10,
    read_only: bool = False,
    embedding_provider: FastEmbedProvider,
) -> QdrantMCPServer:
    collection_name = f"test_{uuid.uuid4().hex}"
    monkeypatch.setenv("NAMESPACE", namespace)
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    monkeypatch.setenv("COLLECTION_NAME", collection_name)
    monkeypatch.setenv("QDRANT_SEARCH_LIMIT", str(search_limit))
    monkeypatch.setenv("QDRANT_READ_ONLY", "1" if read_only else "0")

    return QdrantMCPServer(
        tool_settings=ToolSettings(),
        qdrant_settings=QdrantSettings(),
        server_settings=ServerSettings(),
        embedding_provider=embedding_provider,
    )


@pytest.mark.asyncio
async def test_default_namespace_tool_names(
    monkeypatch: pytest.MonkeyPatch, embedding_provider: FastEmbedProvider
) -> None:
    server = _make_server(monkeypatch, embedding_provider=embedding_provider)
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == {"qdrant-find", "qdrant-store"}


@pytest.mark.asyncio
async def test_custom_namespace_tool_names(
    monkeypatch: pytest.MonkeyPatch, embedding_provider: FastEmbedProvider
) -> None:
    server = _make_server(
        monkeypatch, namespace="memory", embedding_provider=embedding_provider
    )
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == {"memory-find", "memory-store"}


@pytest.mark.asyncio
async def test_read_only_omits_store_tool(
    monkeypatch: pytest.MonkeyPatch, embedding_provider: FastEmbedProvider
) -> None:
    server = _make_server(
        monkeypatch, read_only=True, embedding_provider=embedding_provider
    )
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == {"qdrant-find"}


@pytest.mark.asyncio
async def test_find_tool_exposes_limit_parameter(
    monkeypatch: pytest.MonkeyPatch, embedding_provider: FastEmbedProvider
) -> None:
    server = _make_server(monkeypatch, embedding_provider=embedding_provider)
    tools = await server.list_tools()
    find_tool = next(tool for tool in tools if tool.name == "qdrant-find")
    assert "limit" in find_tool.to_mcp_tool().inputSchema["properties"]


@pytest.mark.asyncio
async def test_find_uses_default_search_limit(
    monkeypatch: pytest.MonkeyPatch, embedding_provider: FastEmbedProvider
) -> None:
    server = _make_server(
        monkeypatch, search_limit=7, embedding_provider=embedding_provider
    )
    collection_name = server.qdrant_settings.collection_name
    assert collection_name is not None

    with patch.object(
        server.qdrant_connector,
        "search",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_search:
        async with Client(server) as client:
            await client.call_tool("qdrant-find", {"query": "test query"})

    mock_search.assert_awaited_once_with(
        "test query",
        collection_name=collection_name,
        limit=7,
        query_filter=None,
    )


@pytest.mark.asyncio
async def test_find_uses_explicit_limit(
    monkeypatch: pytest.MonkeyPatch, embedding_provider: FastEmbedProvider
) -> None:
    server = _make_server(
        monkeypatch, search_limit=7, embedding_provider=embedding_provider
    )
    collection_name = server.qdrant_settings.collection_name
    assert collection_name is not None

    with patch.object(
        server.qdrant_connector,
        "search",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_search:
        async with Client(server) as client:
            await client.call_tool(
                "qdrant-find", {"query": "test query", "limit": 3}
            )

    mock_search.assert_awaited_once_with(
        "test query",
        collection_name=collection_name,
        limit=3,
        query_filter=None,
    )
