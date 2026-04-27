from __future__ import annotations

import os
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.exporter import export_growthpilot_report
from workflow.graph import run_growthpilot_workflow


IDEA = "我想做一个校园二手交易平台"
REQUIRED_PROGRESS_STEPS = [
    "retrieve_context",
    "route_scenario",
    "generate_funnel",
    "generate_experiments",
    "generate_requirements",
    "generate_prd",
    "generate_mvp",
    "critique_result",
]


def main() -> None:
    os.environ["OPENAI_API_KEY"] = ""

    events: list[tuple[str, str]] = []
    result = run_growthpilot_workflow(
        IDEA,
        progress_callback=lambda step_key, message: events.append((step_key, message)),
    )

    required_result_keys = [
        "router_output",
        "funnel_output",
        "experiment_output",
        "requirement_output",
        "prd_output",
        "mvp_output",
        "critic_output",
        "rag_debug",
        "steps_status",
    ]
    for key in required_result_keys:
        assert key in result, f"Missing result key: {key}"

    rag_debug = result["rag_debug"]
    assert isinstance(rag_debug, list), "rag_debug must be a list"
    assert rag_debug, "rag_debug should not be empty"
    first_debug = rag_debug[0]
    for debug_key in ["source_file", "matched_preview", "retrieval_method"]:
        assert debug_key in first_debug, f"Missing rag_debug field: {debug_key}"

    assert len(events) >= 8, f"Expected at least 8 progress events, got {len(events)}"
    received_steps = [step for step, _message in events]
    for step in REQUIRED_PROGRESS_STEPS:
        assert step in received_steps, f"Missing progress step: {step}"

    report = export_growthpilot_report(result, IDEA)
    assert report, "Markdown report should not be empty"
    assert "## RAG 检索来源" in report, "Markdown report missing RAG section"
    assert "## Iteration Log / 迭代闭环说明" in report, "Markdown report missing iteration log"
    assert "修订版方案摘要" in report, "Markdown report missing revised summary"
    assert "badcase" in report.lower(), "Markdown report missing badcase content"
    assert "下一轮迭代建议" in report, "Markdown report missing next iteration suggestions"

    forbidden_patterns = [
        r"\b20\d{2}-\d{2}-\d{2}\b",
        r"\u5ba1\u67e5\u65f6\u95f4[:：]\s*20\d{2}",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, result["critic_output"]), f"Critic output contains forbidden date pattern: {pattern}"
        assert not re.search(pattern, report), f"Markdown report contains forbidden date pattern: {pattern}"

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
