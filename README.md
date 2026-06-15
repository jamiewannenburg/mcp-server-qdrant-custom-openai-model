# mcp-server-qdrant: Custom OpenAI-Compatible Embedding Server for Qdrant MCP

[![smithery badge](https://smithery.ai/badge/mcp-server-qdrant)](https://smithery.ai/protocol/mcp-server-qdrant)

> The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that enables
> seamless integration between LLM applications and external data sources and tools. Whether you're building an
> AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to
> connect LLMs with the context they need.

This repository is a fork of [`qdrant/mcp-server-qdrant`](https://github.com/qdrant/mcp-server-qdrant) and an example of how to create a MCP server for [Qdrant](https://qdrant.tech/), a vector search engine.

## Why this fork exists

This fork keeps the official Qdrant MCP server behavior, but adds support for using an external OpenAI-compatible embeddings API instead of local FastEmbed-only inference.

The main reason for the change is to support higher-quality or centrally managed embedding models exposed through any OpenAI-compatible embeddings endpoint, including self-hosted gateways and managed providers.

That allows you to:

- keep Qdrant as the memory/search layer,
- keep the official MCP server structure and tool behavior,
- choose your own embedding model through environment variables,
- avoid local fallback embeddings when you want a single shared embedding pipeline,
- let the server detect the real embedding dimension before creating a collection.

If you do not need that, the default FastEmbed flow still works.

## Overview

An official Model Context Protocol server for keeping and retrieving memories in the Qdrant vector search engine.
It acts as a semantic memory layer on top of the Qdrant database.

## Components

### Tools

Tools are prefixed at runtime using the `NAMESPACE` environment variable (default: `qdrant`). With the default namespace, clients see `qdrant-store` and `qdrant-find`. Set `NAMESPACE=memory` to expose `memory-store` and `memory-find` instead — useful when mounting multiple instances in the same MCP client.

1. `{NAMESPACE}-store` (default: `qdrant-store`)
   - Store some information in the Qdrant database
   - Input:
     - `information` (string): Information to store
     - `metadata` (JSON): Optional metadata to store
     - `collection_name` (string): Name of the collection to store the information in. This field is required if there are no default collection name.
                                   If there is a default collection name, this field is not enabled.
   - Returns: Confirmation message
2. `{NAMESPACE}-find` (default: `qdrant-find`)
   - Retrieve relevant information from the Qdrant database
   - Input:
     - `query` (string): Query to use for searching
     - `limit` (integer, optional): Max results to return. Defaults to `QDRANT_SEARCH_LIMIT`.
     - `collection_name` (string): Name of the collection to store the information in. This field is required if there are no default collection name.
                                   If there is a default collection name, this field is not enabled.
   - Returns: Information stored in the Qdrant database as separate messages

The `qdrant-store` tool is omitted when `QDRANT_READ_ONLY=true`.

## Environment Variables

The configuration of the server is done using environment variables:

| Name                     | Description                                                         | Default Value                                                     |
|--------------------------|---------------------------------------------------------------------|-------------------------------------------------------------------|
| `QDRANT_URL`             | URL of the Qdrant server                                            | None                                                              |
| `QDRANT_API_KEY`         | API key for the Qdrant server                                       | None                                                              |
| `COLLECTION_NAME`        | Name of the default collection to use.                              | None                                                              |
| `QDRANT_LOCAL_PATH`      | Path to the local Qdrant database (alternative to `QDRANT_URL`)     | None                                                              |
| `QDRANT_SEARCH_LIMIT`    | Default max results for `find` (overridable per call via `limit`)   | `10`                                                              |
| `QDRANT_READ_ONLY`       | When `true`, omit the store tool                                    | `false`                                                           |
| `QDRANT_ALLOW_ARBITRARY_FILTER` | Expose raw `query_filter` on find                          | `false`                                                           |
| `NAMESPACE`              | Prefix for MCP tool names (`{NAMESPACE}-find`, `{NAMESPACE}-store`) | `qdrant`                                                          |
| `AUTH_BEARER_TOKEN`      | Bearer token required on HTTP requests (optional)                   | None                                                              |
| `EMBEDDING_PROVIDER`     | Embedding provider to use (`fastembed` or `openai`)                  | `fastembed`                                                       |
| `EMBEDDING_MODEL`        | Name of the embedding model to use                                  | `sentence-transformers/all-MiniLM-L6-v2`                          |
| `EMBEDDING_BASE_URL`     | Base URL for OpenAI-compatible embeddings API                        | None                                                              |
| `EMBEDDING_API_KEY`      | API key for OpenAI-compatible embeddings API                         | None                                                              |
| `EMBEDDING_EXPECTED_RESPONSE_MODEL` | Expected `model` value in embedding responses               | `EMBEDDING_MODEL`                                                 |
| `EMBEDDING_VECTOR_NAME`  | Override vector name stored in Qdrant                                | sanitized model name                                              |
| `TOOL_STORE_DESCRIPTION` | Custom description for the store tool                               | See default in [`settings.py`](src/mcp_server_qdrant/settings.py) |
| `TOOL_FIND_DESCRIPTION`  | Custom description for the find tool                                | See default in [`settings.py`](src/mcp_server_qdrant/settings.py) |

Note: You cannot provide both `QDRANT_URL` and `QDRANT_LOCAL_PATH` at the same time.

> [!IMPORTANT]
> Command-line arguments are not supported anymore! Please use environment variables for all configuration.

## Embedding backends

This fork supports two embedding modes:

### 1. `fastembed`

This is the original upstream behavior.

- embeddings are generated locally,
- FastEmbed models are used,
- the default model is `sentence-transformers/all-MiniLM-L6-v2`.

### 2. `openai`

This fork-specific mode uses any OpenAI-compatible embeddings endpoint.

In this mode the server:

- sends every embedding request to `EMBEDDING_BASE_URL + /v1/embeddings`,
- forces `model=EMBEDDING_MODEL`,
- requests `encoding_format=float`,
- validates the embedding response structure,
- optionally checks the returned response model through `EMBEDDING_EXPECTED_RESPONSE_MODEL`,
- detects the real vector size from the returned embedding before creating a collection.

This is the recommended mode if you want to use your own centralized embedding model.

### FastMCP Environment Variables

Since `mcp-server-qdrant` is based on FastMCP, it also supports all the FastMCP environment variables. The most
important ones are listed below:

| Environment Variable                  | Description                                               | Default Value |
|---------------------------------------|-----------------------------------------------------------|---------------|
| `FASTMCP_DEBUG`                       | Enable debug mode                                         | `false`       |
| `FASTMCP_LOG_LEVEL`                   | Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO`        |
| `FASTMCP_HOST`                        | Host address to bind the server to                        | `127.0.0.1`   |
| `FASTMCP_PORT`                        | Port to run the server on                                 | `8000`        |
| `FASTMCP_WARN_ON_DUPLICATE_RESOURCES` | Show warnings for duplicate resources                     | `true`        |
| `FASTMCP_WARN_ON_DUPLICATE_TOOLS`     | Show warnings for duplicate tools                         | `true`        |
| `FASTMCP_WARN_ON_DUPLICATE_PROMPTS`   | Show warnings for duplicate prompts                       | `true`        |
| `FASTMCP_DEPENDENCIES`                | List of dependencies to install in the server environment | `[]`          |

## Installation

### Using uvx

When using [`uvx`](https://docs.astral.sh/uv/guides/tools/#running-tools) no specific installation is needed to directly run *mcp-server-qdrant*.

```shell
QDRANT_URL="http://localhost:6333" \
COLLECTION_NAME="my-collection" \
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2" \
uvx mcp-server-qdrant
```

#### Transport Protocols

The server supports different transport protocols that can be specified using the `--transport` flag:

```shell
QDRANT_URL="http://localhost:6333" \
COLLECTION_NAME="my-collection" \
uvx mcp-server-qdrant --transport sse
```

Supported transport protocols:

- `stdio` (default): Standard input/output transport, might only be used by local MCP clients
- `sse`: Server-Sent Events transport, perfect for remote clients
- `streamable-http`: Streamable HTTP transport, perfect for remote clients, more recent than SSE

The default transport is `stdio` if not specified.

When SSE transport is used, the server will listen on the specified port and wait for incoming connections. The default
port is 8000, however it can be changed using the `FASTMCP_PORT` environment variable.

```shell
QDRANT_URL="http://localhost:6333" \
COLLECTION_NAME="my-collection" \
FASTMCP_PORT=1234 \
uvx mcp-server-qdrant --transport sse
```

### Using Docker

A Dockerfile is available for building and running the MCP server:

```bash
# Build the container
docker build -t mcp-server-qdrant .

# Run the container
docker run -p 8000:8000 \
  -e FASTMCP_HOST="0.0.0.0" \
  -e QDRANT_URL="http://your-qdrant-server:6333" \
  -e QDRANT_API_KEY="your-api-key" \
  -e COLLECTION_NAME="your-collection" \
  mcp-server-qdrant
```

> [!TIP]
> Please note that we set `FASTMCP_HOST="0.0.0.0"` to make the server listen on all network interfaces. This is
> necessary when running the server in a Docker container.

When using HTTP transport (`sse` or `streamable-http`), connect your MCP client to `http://localhost:8000/mcp` (no trailing slash). Set `AUTH_BEARER_TOKEN` to require `Authorization: Bearer TOKEN` on every request.

### Deploy to Google Cloud Run

Cloud Run can host this MCP server as a stateless HTTP service. Qdrant itself should run separately (see [Setting up Qdrant on Google Cloud](#setting-up-qdrant-on-google-cloud) below); point `QDRANT_URL` at that instance.

#### Prerequisites

1. Install and authenticate the Google Cloud CLI:

   ```bash
   gcloud auth login
   gcloud config set project PROJECT_ID
   ```

2. Enable required APIs:

   ```bash
   gcloud services enable run.googleapis.com secretmanager.googleapis.com
   ```

3. Create a dedicated service account (recommended):

   ```bash
   gcloud iam service-accounts create mcp-server-qdrant \
     --display-name="mcp-server-qdrant Cloud Run"

   SA_EMAIL="mcp-server-qdrant@PROJECT_ID.iam.gserviceaccount.com"
   ```

4. Optional: store secrets in Secret Manager.

   Use `printf` on Linux/macOS so secret values are written without a trailing newline. On Windows PowerShell, piping to `gcloud` adds `\r\n` to the value, which breaks HTTP headers such as `QDRANT_API_KEY`. Write the value to a temp file with `[System.IO.File]::WriteAllBytes` instead.

   **Linux / macOS (bash):**

   ```bash
   printf "%s" "your-embedding-key" | gcloud secrets create embedding-api-key \
     --replication-policy="automatic" --data-file=-

   printf "%s" "your-qdrant-key" | gcloud secrets create qdrant-api-key \
     --replication-policy="automatic" --data-file=-

   AUTH_TOKEN="$(openssl rand -base64 48)"
   printf "%s" "${AUTH_TOKEN}" | gcloud secrets create mcp-server-qdrant-auth-token \
     --replication-policy="automatic" --data-file=-

   for SECRET in embedding-api-key qdrant-api-key mcp-server-qdrant-auth-token; do
     gcloud secrets add-iam-policy-binding "${SECRET}" \
       --member="serviceAccount:${SA_EMAIL}" \
       --role="roles/secretmanager.secretAccessor"
   done
   ```

   **Windows (PowerShell):**

   ```powershell
   $utf8 = New-Object System.Text.UTF8Encoding $false
   $SA_EMAIL = "mcp-server-qdrant@PROJECT_ID.iam.gserviceaccount.com"

   function Write-GcloudSecretFile {
     param([string]$Value)
     $tmp = [System.IO.Path]::GetTempFileName()
     [System.IO.File]::WriteAllBytes($tmp, $utf8.GetBytes($Value))
     return $tmp
   }

   $tmp = Write-GcloudSecretFile "your-embedding-key"
   gcloud secrets create embedding-api-key --replication-policy="automatic" --data-file=$tmp
   Remove-Item $tmp -Force

   $tmp = Write-GcloudSecretFile "your-qdrant-key"
   gcloud secrets create qdrant-api-key --replication-policy="automatic" --data-file=$tmp
   Remove-Item $tmp -Force

   $bytes = New-Object byte[] 48
   [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
   $AUTH_TOKEN = [Convert]::ToBase64String($bytes)
   $tmp = Write-GcloudSecretFile $AUTH_TOKEN
   gcloud secrets create mcp-server-qdrant-auth-token --replication-policy="automatic" --data-file=$tmp
   Remove-Item $tmp -Force

   foreach ($SECRET in @("embedding-api-key", "qdrant-api-key", "mcp-server-qdrant-auth-token")) {
     gcloud secrets add-iam-policy-binding $SECRET `
       --member="serviceAccount:$SA_EMAIL" `
       --role="roles/secretmanager.secretAccessor"
   }
   ```

   To update an existing secret (equivalent to `printf "%s" "value" | gcloud secrets versions add ...`):

   ```bash
   printf "%s" "your-qdrant-key" | gcloud secrets versions add qdrant-api-key --data-file=-
   ```

   ```powershell
   # Uses Write-GcloudSecretFile from the PowerShell block above.
   $tmp = Write-GcloudSecretFile "your-qdrant-key"
   gcloud secrets versions add qdrant-api-key --data-file=$tmp
   Remove-Item $tmp -Force
   ```

   Save `AUTH_TOKEN` in your password manager; MCP clients must send `Authorization: Bearer TOKEN` on every request when `AUTH_BEARER_TOKEN` is set.

#### Deploy from source

```bash
gcloud run deploy mcp-server-qdrant \
  --source . \
  --region REGION \
  --port 8000 \
  --service-account="${SA_EMAIL}" \
  --min-instances 0 \
  --set-env-vars "EMBEDDING_PROVIDER=openai,EMBEDDING_MODEL=text-embedding-3-large,EMBEDDING_BASE_URL=https://api.openai.com,QDRANT_URL=https://YOUR_QDRANT_URL,COLLECTION_NAME=mcp_memory,NAMESPACE=qdrant" \
  --set-secrets "EMBEDDING_API_KEY=embedding-api-key:latest,QDRANT_API_KEY=qdrant-api-key:latest,AUTH_BEARER_TOKEN=mcp-server-qdrant-auth-token:latest"
```

Omit `--set-secrets AUTH_BEARER_TOKEN=...` if you do not want application-level bearer authentication.

If your MCP client cannot mint Google Cloud Run IAM tokens and you rely on `AUTH_BEARER_TOKEN`, add `--allow-unauthenticated`. The application middleware still rejects requests without the correct bearer token.

Keep the service private (default) when clients can authenticate with Cloud Run IAM instead.

#### Deploy a pre-built image

```bash
docker build -t gcr.io/PROJECT_ID/mcp-server-qdrant:latest .
docker push gcr.io/PROJECT_ID/mcp-server-qdrant:latest
# or to dockerhub
docker build -t jamiewannenburg/mcp-server-qdrant:latest .
docker push jamiewannenburg/mcp-server-qdrant

gcloud run deploy mcp-server-qdrant \
  --image gcr.io/PROJECT_ID/mcp-server-qdrant:latest \
# or
  --image docker.io/jamiewannenburg/mcp-server-qdrant:latest
  --region REGION \
  --port 8000 \
  --service-account="${SA_EMAIL}" \
  --set-env-vars "EMBEDDING_PROVIDER=openai,EMBEDDING_MODEL=text-embedding-3-large,EMBEDDING_BASE_URL=https://api.openai.com,QDRANT_URL=https://YOUR_QDRANT_URL,NAMESPACE=qdrant" \
  --set-secrets "EMBEDDING_API_KEY=embedding-api-key:latest,QDRANT_API_KEY=qdrant-api-key:latest,AUTH_BEARER_TOKEN=mcp-server-qdrant-auth-token:latest"
```

After deployment, connect your MCP client to:

```text
https://SERVICE_URL/mcp
```

Get the service URL:

```bash
gcloud run services describe mcp-server-qdrant \
  --region REGION \
  --format='value(status.url)'
```

#### Cursor configuration (Cloud Run)

```json
{
  "mcpServers": {
    "qdrant-memory": {
      "url": "https://SERVICE_URL/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_AUTH_TOKEN"
      }
    }
  }
}
```

References:

- [Cloud Run deploy reference](https://cloud.google.com/sdk/gcloud/reference/run/deploy)
- [Cloud Run secrets](https://cloud.google.com/run/docs/configuring/services/secrets)

### Setting up Qdrant on Google Cloud

This MCP server is a **client** of Qdrant. You need a running Qdrant instance before deploying the MCP server. Choose an option based on workload size and durability requirements.

#### Option 1: Qdrant Cloud (managed, recommended for production)

[Qdrant Cloud](https://cloud.qdrant.io/) is the simplest path: fully managed clusters with backups, scaling, and a stable HTTPS endpoint.

1. Create a cluster at [cloud.qdrant.io](https://cloud.qdrant.io/).
2. Copy the cluster URL and API key.
3. Set in your MCP server environment:

   ```bash
   QDRANT_URL=https://xxxxxxxx.qdrant.io
   QDRANT_API_KEY=your-cluster-api-key
   ```

No GCP infrastructure to manage; billing is through Qdrant Cloud.

#### Option 1b: Qdrant Cloud via Google Cloud Marketplace

Google Cloud Marketplace offers a [Qdrant subscription](https://qdrant.tech/documentation/cloud-pricing-payments/) that bills Qdrant Cloud usage through your existing GCP account. Clusters are still created and managed in the [Qdrant Cloud Console](https://cloud.qdrant.io/) — Marketplace handles payment only.

To subscribe:

1. Go to **Billing Details** in the Qdrant Cloud Console.
2. Select **GCP Marketplace** as the payment method and follow the redirect to subscribe.
3. After subscribing, create clusters in the Qdrant Cloud Console as usual and use the cluster URL and API key as `QDRANT_URL` and `QDRANT_API_KEY`.

#### Option 2: Qdrant on Cloud Run (dev / small workloads)

You can run the official `qdrant/qdrant` container on Cloud Run for low-traffic or development use. Qdrant keeps indexes in memory and writes data to disk, so treat this as **single-instance only**.

Important constraints:

- Set `--min-instances 1` to avoid cold starts reloading large HNSW indexes.
- Set `--max-instances 1` — Qdrant is a single-writer store; multiple Cloud Run instances cannot safely share one collection.
- Use a **Cloud Storage volume mount** (GCS FUSE) for persistence across restarts.

See the [Qdrant configuration guide](https://qdrant.tech/documentation/guides/configuration/) and [Cloud Run volume mounts](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts).

#### Option 3: Qdrant on GKE (production / HA)

For production workloads needing persistent SSD storage, rolling updates, and optional distributed mode, deploy Qdrant on [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine). Google publishes a tutorial: [Deploy a Qdrant vector database on GKE](https://cloud.google.com/kubernetes-engine/docs/tutorials/deploy-qdrant).

Point the MCP server at the internal service URL from Cloud Run (via VPC connector) or from clients inside the same VPC.

#### Choosing an option

| Option | Best for | Persistence | Scaling |
| ------ | -------- | ----------- | ------- |
| Qdrant Cloud | Production without ops overhead | Managed | Managed |
| GCP Marketplace | Qdrant Cloud billed via GCP | Managed | Managed |
| Cloud Run | Dev / prototypes | GCS FUSE mount | Single instance only |
| GKE | Production on GCP | Regional SSD PVCs | StatefulSet / distributed |

### Installing via Smithery

To install Qdrant MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/protocol/mcp-server-qdrant):

```bash
npx @smithery/cli install mcp-server-qdrant --client claude
```

### Manual configuration of Claude Desktop

To use this server with the Claude Desktop app, add the following configuration to the "mcpServers" section of your
`claude_desktop_config.json`:

```json
{
  "qdrant": {
    "command": "uvx",
    "args": ["mcp-server-qdrant"],
    "env": {
      "QDRANT_URL": "https://xyz-example.eu-central.aws.cloud.qdrant.io:6333",
      "QDRANT_API_KEY": "your_api_key",
      "COLLECTION_NAME": "your-collection-name",
      "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
    }
  }
}
```

For local Qdrant mode:

```json
{
  "qdrant": {
    "command": "uvx",
    "args": ["mcp-server-qdrant"],
    "env": {
      "QDRANT_LOCAL_PATH": "/path/to/qdrant/database",
      "COLLECTION_NAME": "your-collection-name",
      "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
    }
  }
}
```

This MCP server will automatically create a collection with the specified name if it doesn't exist.

By default, the server will use the `sentence-transformers/all-MiniLM-L6-v2` embedding model via FastEmbed.

If you want to use an OpenAI-compatible embeddings backend, set:

```shell
EMBEDDING_PROVIDER="openai" \
EMBEDDING_BASE_URL="https://your-openai-compatible-endpoint" \
EMBEDDING_MODEL="your-embedding-model" \
EMBEDDING_API_KEY="your-api-key" \
uvx mcp-server-qdrant --transport streamable-http
```

In `openai` mode, the server:
- forces `model=EMBEDDING_MODEL` on every `/v1/embeddings` request,
- requests `encoding_format=float`,
- validates the response structure,
- probes the real embedding dimension before creating a collection.

## Support for other tools

This MCP server can be used with any MCP-compatible client. For example, you can use it with
[Cursor](https://docs.cursor.com/context/model-context-protocol) and [VS Code](https://code.visualstudio.com/docs), which provide built-in support for the Model Context
Protocol.

### Using with Cursor/Windsurf

You can configure this MCP server to work as a code search tool for Cursor or Windsurf by customizing the tool
descriptions:

```bash
QDRANT_URL="http://localhost:6333" \
COLLECTION_NAME="code-snippets" \
TOOL_STORE_DESCRIPTION="Store reusable code snippets for later retrieval. \
The 'information' parameter should contain a natural language description of what the code does, \
while the actual code should be included in the 'metadata' parameter as a 'code' property. \
The value of 'metadata' is a Python dictionary with strings as keys. \
Use this whenever you generate some code snippet." \
TOOL_FIND_DESCRIPTION="Search for relevant code snippets based on natural language descriptions. \
The 'query' parameter should describe what you're looking for, \
and the tool will return the most relevant code snippets. \
Use this when you need to find existing code snippets for reuse or reference." \
uvx mcp-server-qdrant --transport sse # Enable SSE transport
```

In Cursor/Windsurf, you can then configure the MCP server in your settings by pointing to this running server using
SSE transport protocol. The description on how to add an MCP server to Cursor can be found in the [Cursor
documentation](https://docs.cursor.com/context/model-context-protocol#adding-an-mcp-server-to-cursor). If you are
running Cursor/Windsurf locally, you can use the following URL:

```
http://localhost:8000/sse
```

> [!TIP]
> We suggest SSE transport as a preferred way to connect Cursor/Windsurf to the MCP server, as it can support remote
> connections. That makes it easy to share the server with your team or use it in a cloud environment.

This configuration transforms the Qdrant MCP server into a specialized code search tool that can:

1. Store code snippets, documentation, and implementation details
2. Retrieve relevant code examples based on semantic search
3. Help developers find specific implementations or usage patterns

You can populate the database by storing natural language descriptions of code snippets (in the `information` parameter)
along with the actual code (in the `metadata.code` property), and then search for them using natural language queries
that describe what you're looking for.

> [!NOTE]
> The tool descriptions provided above are examples and may need to be customized for your specific use case. Consider
> adjusting the descriptions to better match your team's workflow and the specific types of code snippets you want to
> store and retrieve.

**If you have successfully installed the `mcp-server-qdrant`, but still can't get it to work with Cursor, please
consider creating the [Cursor rules](https://docs.cursor.com/context/rules-for-ai) so the MCP tools are always used when
the agent produces a new code snippet.** You can restrict the rules to only work for certain file types, to avoid using
the MCP server for the documentation or other types of content.

### Using with Claude Code

You can enhance Claude Code's capabilities by connecting it to this MCP server, enabling semantic search over your
existing codebase.

#### Setting up mcp-server-qdrant

1. Add the MCP server to Claude Code:

    ```shell
    # Add mcp-server-qdrant configured for code search
    claude mcp add code-search \
    -e QDRANT_URL="http://localhost:6333" \
    -e COLLECTION_NAME="code-repository" \
    -e EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2" \
    -e TOOL_STORE_DESCRIPTION="Store code snippets with descriptions. The 'information' parameter should contain a natural language description of what the code does, while the actual code should be included in the 'metadata' parameter as a 'code' property." \
    -e TOOL_FIND_DESCRIPTION="Search for relevant code snippets using natural language. The 'query' parameter should describe the functionality you're looking for." \
    -- uvx mcp-server-qdrant
    ```

For a custom OpenAI-compatible embeddings backend:

    ```shell
    claude mcp add code-search \
    -e QDRANT_URL="http://localhost:6333" \
    -e COLLECTION_NAME="code-repository" \
    -e EMBEDDING_PROVIDER="openai" \
    -e EMBEDDING_BASE_URL="https://your-openai-compatible-endpoint" \
    -e EMBEDDING_MODEL="your-embedding-model" \
    -e EMBEDDING_API_KEY="your-api-key" \
    -- uvx mcp-server-qdrant
    ```

2. Verify the server was added:

    ```shell
    claude mcp list
    ```

#### Using Semantic Code Search in Claude Code

Tool descriptions, specified in `TOOL_STORE_DESCRIPTION` and `TOOL_FIND_DESCRIPTION`, guide Claude Code on how to use
the MCP server. The ones provided above are examples and may need to be customized for your specific use case. However,
Claude Code should be already able to:

1. Use the `qdrant-store` tool to store code snippets with descriptions.
2. Use the `qdrant-find` tool to search for relevant code snippets using natural language.

### Run MCP server in Development Mode

The MCP server can be run in development mode using the `mcp dev` command. This will start the server and open the MCP
inspector in your browser.

```shell
COLLECTION_NAME=mcp-dev fastmcp dev src/mcp_server_qdrant/server.py
```

### Using with VS Code

For one-click installation, click one of the install buttons below:

[![Install with UVX in VS Code](https://img.shields.io/badge/VS_Code-UVX-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=qdrant&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-qdrant%22%5D%2C%22env%22%3A%7B%22QDRANT_URL%22%3A%22%24%7Binput%3AqdrantUrl%7D%22%2C%22QDRANT_API_KEY%22%3A%22%24%7Binput%3AqdrantApiKey%7D%22%2C%22COLLECTION_NAME%22%3A%22%24%7Binput%3AcollectionName%7D%22%7D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantUrl%22%2C%22description%22%3A%22Qdrant+URL%22%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantApiKey%22%2C%22description%22%3A%22Qdrant+API+Key%22%2C%22password%22%3Atrue%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22collectionName%22%2C%22description%22%3A%22Collection+Name%22%7D%5D) [![Install with UVX in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-UVX-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=qdrant&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-qdrant%22%5D%2C%22env%22%3A%7B%22QDRANT_URL%22%3A%22%24%7Binput%3AqdrantUrl%7D%22%2C%22QDRANT_API_KEY%22%3A%22%24%7Binput%3AqdrantApiKey%7D%22%2C%22COLLECTION_NAME%22%3A%22%24%7Binput%3AcollectionName%7D%22%7D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantUrl%22%2C%22description%22%3A%22Qdrant+URL%22%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantApiKey%22%2C%22description%22%3A%22Qdrant+API+Key%22%2C%22password%22%3Atrue%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22collectionName%22%2C%22description%22%3A%22Collection+Name%22%7D%5D&quality=insiders)

[![Install with Docker in VS Code](https://img.shields.io/badge/VS_Code-Docker-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=qdrant&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22-p%22%2C%228000%3A8000%22%2C%22-i%22%2C%22--rm%22%2C%22-e%22%2C%22QDRANT_URL%22%2C%22-e%22%2C%22QDRANT_API_KEY%22%2C%22-e%22%2C%22COLLECTION_NAME%22%2C%22mcp-server-qdrant%22%5D%2C%22env%22%3A%7B%22QDRANT_URL%22%3A%22%24%7Binput%3AqdrantUrl%7D%22%2C%22QDRANT_API_KEY%22%3A%22%24%7Binput%3AqdrantApiKey%7D%22%2C%22COLLECTION_NAME%22%3A%22%24%7Binput%3AcollectionName%7D%22%7D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantUrl%22%2C%22description%22%3A%22Qdrant+URL%22%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantApiKey%22%2C%22description%22%3A%22Qdrant+API+Key%22%2C%22password%22%3Atrue%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22collectionName%22%2C%22description%22%3A%22Collection+Name%22%7D%5D) [![Install with Docker in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Docker-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=qdrant&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22-p%22%2C%228000%3A8000%22%2C%22-i%22%2C%22--rm%22%2C%22-e%22%2C%22QDRANT_URL%22%2C%22-e%22%2C%22QDRANT_API_KEY%22%2C%22-e%22%2C%22COLLECTION_NAME%22%2C%22mcp-server-qdrant%22%5D%2C%22env%22%3A%7B%22QDRANT_URL%22%3A%22%24%7Binput%3AqdrantUrl%7D%22%2C%22QDRANT_API_KEY%22%3A%22%24%7Binput%3AqdrantApiKey%7D%22%2C%22COLLECTION_NAME%22%3A%22%24%7Binput%3AcollectionName%7D%22%7D%7D&inputs=%5B%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantUrl%22%2C%22description%22%3A%22Qdrant+URL%22%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22qdrantApiKey%22%2C%22description%22%3A%22Qdrant+API+Key%22%2C%22password%22%3Atrue%7D%2C%7B%22type%22%3A%22promptString%22%2C%22id%22%3A%22collectionName%22%2C%22description%22%3A%22Collection+Name%22%7D%5D&quality=insiders)

#### Manual Installation

Add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)`.

```json
{
  "mcp": {
    "inputs": [
      {
        "type": "promptString",
        "id": "qdrantUrl",
        "description": "Qdrant URL"
      },
      {
        "type": "promptString",
        "id": "qdrantApiKey",
        "description": "Qdrant API Key",
        "password": true
      },
      {
        "type": "promptString",
        "id": "collectionName",
        "description": "Collection Name"
      }
    ],
    "servers": {
      "qdrant": {
        "command": "uvx",
        "args": ["mcp-server-qdrant"],
        "env": {
          "QDRANT_URL": "${input:qdrantUrl}",
          "QDRANT_API_KEY": "${input:qdrantApiKey}",
          "COLLECTION_NAME": "${input:collectionName}"
        }
      }
    }
  }
}
```

Or if you prefer using Docker, add this configuration instead:

```json
{
  "mcp": {
    "inputs": [
      {
        "type": "promptString",
        "id": "qdrantUrl",
        "description": "Qdrant URL"
      },
      {
        "type": "promptString",
        "id": "qdrantApiKey",
        "description": "Qdrant API Key",
        "password": true
      },
      {
        "type": "promptString",
        "id": "collectionName",
        "description": "Collection Name"
      }
    ],
    "servers": {
      "qdrant": {
        "command": "docker",
        "args": [
          "run",
          "-p", "8000:8000",
          "-i",
          "--rm",
          "-e", "QDRANT_URL",
          "-e", "QDRANT_API_KEY",
          "-e", "COLLECTION_NAME",
          "mcp-server-qdrant"
        ],
        "env": {
          "QDRANT_URL": "${input:qdrantUrl}",
          "QDRANT_API_KEY": "${input:qdrantApiKey}",
          "COLLECTION_NAME": "${input:collectionName}"
        }
      }
    }
  }
}
```

Alternatively, you can create a `.vscode/mcp.json` file in your workspace with the following content:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "qdrantUrl",
      "description": "Qdrant URL"
    },
    {
      "type": "promptString",
      "id": "qdrantApiKey",
      "description": "Qdrant API Key",
      "password": true
    },
    {
      "type": "promptString",
      "id": "collectionName",
      "description": "Collection Name"
    }
  ],
  "servers": {
    "qdrant": {
      "command": "uvx",
      "args": ["mcp-server-qdrant"],
      "env": {
        "QDRANT_URL": "${input:qdrantUrl}",
        "QDRANT_API_KEY": "${input:qdrantApiKey}",
        "COLLECTION_NAME": "${input:collectionName}"
      }
    }
  }
}
```

For workspace configuration with Docker, use this in `.vscode/mcp.json`:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "qdrantUrl",
      "description": "Qdrant URL"
    },
    {
      "type": "promptString",
      "id": "qdrantApiKey",
      "description": "Qdrant API Key",
      "password": true
    },
    {
      "type": "promptString",
      "id": "collectionName",
      "description": "Collection Name"
    }
  ],
  "servers": {
    "qdrant": {
      "command": "docker",
      "args": [
        "run",
        "-p", "8000:8000",
        "-i",
        "--rm",
        "-e", "QDRANT_URL",
        "-e", "QDRANT_API_KEY",
        "-e", "COLLECTION_NAME",
        "mcp-server-qdrant"
      ],
      "env": {
        "QDRANT_URL": "${input:qdrantUrl}",
        "QDRANT_API_KEY": "${input:qdrantApiKey}",
        "COLLECTION_NAME": "${input:collectionName}"
      }
    }
  }
}
```

## Contributing

If you have suggestions for how mcp-server-qdrant could be improved, or want to report a bug, open an issue!
We'd love all and any contributions.

### Testing `mcp-server-qdrant` locally

The [MCP inspector](https://github.com/modelcontextprotocol/inspector) is a developer tool for testing and debugging MCP
servers. It runs both a client UI (default port 5173) and an MCP proxy server (default port 3000). Open the client UI in
your browser to use the inspector.

```shell
QDRANT_URL=":memory:" COLLECTION_NAME="test" \
fastmcp dev src/mcp_server_qdrant/server.py
```

Once started, open your browser to http://localhost:5173 to access the inspector interface.

## License

This MCP server is licensed under the Apache License 2.0. This means you are free to use, modify, and distribute the
software, subject to the terms and conditions of the Apache License 2.0. For more details, please see the LICENSE file
in the project repository.
