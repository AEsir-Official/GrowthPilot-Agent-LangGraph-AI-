from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any


# Disable python-dotenv auto-loading inside the MCP process. The server should
# only rely on environment variables already provided by the MCP host/client.
os.environ.setdefault("PYTHON_DOTENV_DISABLED", "1")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - optional dependency
    FastMCP = None
    MCP_IMPORT_ERROR = exc
else:
    MCP_IMPORT_ERROR = None

from rag.retriever import retrieve_context
from utils.exporter import export_growthpilot_report
from workflow.graph import run_growthpilot_workflow


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("growthpilot.mcp")


def _to_json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


if FastMCP is not None:
    mcp = FastMCP("GrowthPilot Agent MCP Server")

    @mcp.tool()
    def retrieve_growth_templates(idea: str) -> str:
        """Retrieve GrowthPilot knowledge-base templates for a business idea.

        The tool only reads from GrowthPilot's built-in local markdown knowledge
        base through the project's retriever. It does not access arbitrary file
        paths, shell commands, git, or databases.
        """
        return retrieve_context(idea)


    @mcp.tool()
    def generate_growth_report(idea: str) -> str:
        """Generate a full GrowthPilot structured report as JSON text.

        This tool reuses the existing LangGraph workflow entrypoint. If no API
        key is available, the underlying project fallback remains active and the
        tool still returns a valid report payload.
        """
        result = run_growthpilot_workflow(idea)
        return _to_json_text(result)


    @mcp.tool()
    def export_growth_report(idea: str) -> str:
        """Generate and export a GrowthPilot markdown report.

        This tool runs the existing workflow and then converts the result into a
        markdown report using the project's exporter utility.
        """
        result = run_growthpilot_workflow(idea)
        return export_growthpilot_report(result, idea)


def main() -> None:
    if FastMCP is None:  # pragma: no cover - runtime guard
        raise SystemExit(
            "The optional MCP SDK is not installed. "
            "Run `pip install -r requirements-mcp.txt` first."
        ) from MCP_IMPORT_ERROR

    LOGGER.info("Starting GrowthPilot MCP server over stdio transport")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
