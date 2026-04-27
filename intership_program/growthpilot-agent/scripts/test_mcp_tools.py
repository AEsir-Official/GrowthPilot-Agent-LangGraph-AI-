from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PROJECT_ROOT / "mcp_server" / "server.py"
TEST_IDEA = "我想做一个校园二手交易平台"
EXPECTED_TOOLS = {
    "retrieve_growth_templates",
    "generate_growth_report",
    "export_growth_report",
}


def _server_env() -> dict[str, str]:
    env = get_default_environment()
    env.update(
        {
            "PYTHON_DOTENV_DISABLED": "1",
            "OPENAI_API_KEY": "",
            "OPENAI_BASE_URL": "",
            "OPENAI_MODEL": "",
        }
    )
    return env


def _extract_text_content(tool_result: object) -> str:
    content_items = getattr(tool_result, "content", []) or []
    parts: list[str] = []
    for item in content_items:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


async def main() -> None:
    if not SERVER_PATH.exists():
        raise AssertionError(f"MCP server not found: {SERVER_PATH}")

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=_server_env(),
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = {tool.name for tool in tools_result.tools}
            missing = EXPECTED_TOOLS - tool_names
            if missing:
                raise AssertionError(f"Missing MCP tools: {sorted(missing)}")

            template_result = await session.call_tool(
                "retrieve_growth_templates",
                {"idea": TEST_IDEA},
            )
            template_text = _extract_text_content(template_result)
            if not template_text:
                raise AssertionError("retrieve_growth_templates returned empty content")
            if "来源" not in template_text and "default_growth_analysis_template" not in template_text:
                raise AssertionError("retrieve_growth_templates did not return recognizable template content")

            report_result = await session.call_tool(
                "generate_growth_report",
                {"idea": TEST_IDEA},
            )
            report_text = _extract_text_content(report_result)
            if not report_text:
                raise AssertionError("generate_growth_report returned empty content")

            try:
                report_payload = json.loads(report_text)
            except json.JSONDecodeError as exc:
                raise AssertionError("generate_growth_report did not return valid JSON text") from exc

            if not isinstance(report_payload, dict):
                raise AssertionError("generate_growth_report JSON payload is not a dict")

            statuses = report_payload.get("steps_status", [])
            if not isinstance(statuses, list) or not statuses:
                raise AssertionError("generate_growth_report missing steps_status")

            fallback_detected = any(
                "fallback" in str(item.get("message", "")).lower()
                for item in statuses
                if isinstance(item, dict)
            )
            if not fallback_detected:
                raise AssertionError("Expected fallback markers were not found in generate_growth_report output")

            print("MCP server startup: OK")
            print(f"Tools discovered: {sorted(tool_names)}")
            print("retrieve_growth_templates: OK")
            print("generate_growth_report fallback: OK")


if __name__ == "__main__":
    asyncio.run(main())
