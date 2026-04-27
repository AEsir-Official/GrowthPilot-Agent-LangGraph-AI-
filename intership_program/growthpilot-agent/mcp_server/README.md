# GrowthPilot MCP Server

This directory contains an optional experimental MCP server layer for GrowthPilot Agent.

Its purpose is not to improve generation quality. It standardizes access to existing project capabilities so MCP-compatible clients can call them as tools.

The MCP layer wraps three internal capabilities:

- `retrieve_growth_templates`
- `generate_growth_report`
- `export_growth_report`

## What MCP Does Here

GrowthPilot already provides:

- local markdown + TF-IDF RAG retrieval
- a LangGraph workflow entrypoint
- markdown report export

The MCP server exposes those capabilities as reusable MCP tools. This makes them easier to integrate into MCP-compatible clients, inspectors, and agent hosts.

## Tool List

### `retrieve_growth_templates`

Input:

- `idea: str`

Calls:

- `rag.retriever.retrieve_context(idea)`

Returns:

- local business templates and reference context from the GrowthPilot knowledge base

### `generate_growth_report`

Input:

- `idea: str`

Calls:

- `workflow.graph.run_growthpilot_workflow(idea)`

Returns:

- the full structured GrowthPilot report as JSON text

### `export_growth_report`

Input:

- `idea: str`

Calls:

- `workflow.graph.run_growthpilot_workflow(idea)`
- `utils.exporter.export_growthpilot_report(result, idea)`

Returns:

- markdown report text

## Why It Is Optional

This feature is experimental and not required for the main Streamlit demo.

The main application still runs normally with:

```bash
streamlit run app.py
```

No part of the Streamlit UI depends on MCP.

## Installation

Install the main project dependencies first:

```bash
pip install -r requirements.txt
```

Then install the optional MCP dependency:

```bash
pip install -r requirements-mcp.txt
```

This project uses the official Model Context Protocol Python SDK.

## Start the MCP Server

Run from the GrowthPilot project root:

```bash
python mcp_server/server.py
```

The server runs over `stdio`, which is the simplest transport for local MCP clients.

## MCP Smoke Test

You can run a local MCP smoke test with:

```bash
python scripts/test_mcp_tools.py
```

Expected output:

```text
MCP server startup: OK
Tools discovered: ['export_growth_report', 'generate_growth_report', 'retrieve_growth_templates']
retrieve_growth_templates: OK
generate_growth_report fallback: OK
```

This script verifies that the optional MCP server can start, `tools/list` can discover all three tools, `retrieve_growth_templates` can return template content, and `generate_growth_report` can still succeed through fallback when no API key is provided.

## Example MCP Client Configuration

Example configuration for a local MCP-compatible client:

```json
{
  "mcpServers": {
    "growthpilot-agent": {
      "command": "python",
      "args": [
        "D:/MYGO/intership_program/growthpilot-agent/mcp_server/server.py"
      ],
      "cwd": "D:/MYGO/intership_program/growthpilot-agent"
    }
  }
}
```

If you use a project virtual environment, point `command` to the venv Python executable instead.

## Safety Boundary

This MCP server is intentionally narrow in scope:

- it does not expose shell execution
- it does not expose git operations
- it does not expose arbitrary filesystem reads or writes
- it does not expose database access
- it does not read `.env` inside the MCP process
- it does not print or return API keys
- it only calls safe internal GrowthPilot functions

When no API key is available, the project fallback remains active and the server still returns usable outputs.

## License / Attribution

This implementation was written specifically for GrowthPilot Agent.

It references the official MCP Python SDK documentation and quickstart examples for API shape and transport usage, but it does not copy large third-party code into this project.

See [LICENSE_NOTES.md](./LICENSE_NOTES.md) for details.
