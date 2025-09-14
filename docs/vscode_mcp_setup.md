# Using Maverick MCP in VS Code (Continue)

This guide shows how to use the Maverick MCP server from VS Code via the Continue extension. Two connection methods are supported:

- STDIO (local, recommended for VS Code/Continue)
- SSE via mcp-remote bridge (alternative)

## Prerequisites

- Python environment with project dependencies installed
- API keys (at least `TIINGO_API_KEY`)

Install dependencies:

```bash
uv sync
# or
pip install -e .
```

Create `.env` (optional but recommended):

```bash
cp .env.example .env
# set TIINGO_API_KEY=... and optional OPENROUTER_API_KEY, EXA_API_KEY, etc.
```

## Option A: STDIO (Recommended)

Server descriptor `server.json` now includes a `stdio` remote with the exact command VS Code/Continue can run.

Continue config example (`.continue/config.json`):

```json
{
  "mcpServers": {
    "maverick-mcp": {
      "command": "uv",
      "args": [
        "run", "python", "-m", "maverick_mcp.api.server", "--transport", "stdio"
      ],
      "env": {
        "TIINGO_API_KEY": "${env:TIINGO_API_KEY}",
        "OPENROUTER_API_KEY": "${env:OPENROUTER_API_KEY}",
        "EXA_API_KEY": "${env:EXA_API_KEY}"
      }
    }
  }
}
```

Alternatively, in Continue UI: Settings → MCP Servers → Add server (STDIO) and paste the same command/args.

Test locally:

```bash
uv run python -m maverick_mcp.api.server --transport stdio
```

## Option B: SSE via mcp-remote

Start the SSE server:

```bash
make dev
# or
uv run python -m maverick_mcp.api.server --transport sse --port 8003
```

Bridge with `mcp-remote` (if needed by your client):

```bash
npx mcp-remote http://localhost:8003/sse/
```

Then connect your client to the local bridge.

## Notes

- Some clients prefer STDERR for logs when using STDIO; the server auto-switches when `--transport stdio` is used.
- If you see deprecation warnings from dependencies, we filter common ones to keep logs clean.
- For Claude Desktop, prefer STDIO or HTTP via `mcp-remote`; SSE has specific requirements (trailing slash `/sse/`).

## Troubleshooting

- Ensure API keys are present in your environment or `.env`.
- If the IDE cannot find `uv`, use Python directly: `python -m maverick_mcp.api.server --transport stdio`.
- See `CLAUDE.md` for more client compatibility details.
