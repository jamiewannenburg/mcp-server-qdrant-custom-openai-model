FROM python:3.11-slim

WORKDIR /app

# Install uv for package management
RUN pip install --no-cache-dir uv

# Install the local mcp-server-qdrant package
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system --no-cache-dir .

# Expose the default port for SSE transport
EXPOSE 8000

# Set environment variables with defaults that can be overridden at runtime
ENV FASTMCP_HOST="0.0.0.0"
ENV QDRANT_URL=""
ENV QDRANT_API_KEY=""
ENV COLLECTION_NAME="default-collection"
ENV EMBEDDING_PROVIDER="fastembed"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
ENV EMBEDDING_BASE_URL=""
ENV EMBEDDING_API_KEY=""
ENV EMBEDDING_EXPECTED_RESPONSE_MODEL=""
ENV EMBEDDING_VECTOR_NAME=""

# Run the server with streamable HTTP transport
CMD ["sh", "-c", "exec uvicorn mcp_server_qdrant.server:app --host \"$FASTMCP_HOST\" --port \"$FASTMCP_PORT\""]
