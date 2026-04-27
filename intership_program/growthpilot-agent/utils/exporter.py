from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from utils.parser import extract_markdown_section, normalize_markdown


REPORT_SECTIONS = [
    ("business_type", "业务类型判断"),
    ("target_user", "用户画像"),
    ("funnel", "转化漏斗"),
    ("experiments", "增长实验方案"),
    ("ab_test", "A/B 测试方案"),
    ("requirement_pool", "需求池"),
    ("prd", "PRD 初稿"),
    ("mvp_features", "MVP 功能"),
    ("event_tracking", "埋点方案"),
    ("metrics", "指标体系"),
    ("landing_page", "Landing Page 文案"),
    ("critic", "Critic 评分、badcase 分析与下一轮迭代建议"),
]


def _strip_metadata_lines(content: str) -> str:
    create_date_label = "\u521b\u5efa\u65e5\u671f"
    create_time_label = "\u521b\u5efa\u65f6\u95f4"
    review_time_label = "\u5ba1\u67e5\u65f6\u95f4"
    cleaned_lines: list[str] = []
    for line in content.splitlines():
        lower_line = line.lower()
        if create_date_label in line or create_time_label in line or review_time_label in line:
            continue
        if "review date" in lower_line or "created date" in lower_line or "created at" in lower_line:
            continue
        if re.search(r"\b20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}\b", line) and (
            "日期" in line or "时间" in line or "create" in lower_line or "review" in lower_line
        ):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def _safe_content(outputs: dict[str, str], key: str) -> str:
    content = outputs.get(key, "")
    if not content or not content.strip():
        return "暂无内容"
    return _strip_metadata_lines(normalize_markdown(content))


def _extract_iteration_content(critic_output: str, heading: str) -> str:
    content = extract_markdown_section(critic_output, heading)
    return content or "暂无内容"


def _build_iteration_log(critic_output: str) -> str:
    revision_summary = _extract_iteration_content(critic_output, "修订版方案摘要")
    return "\n".join(
        [
            "### 初版方案主要问题",
            "",
            _extract_iteration_content(critic_output, "主要问题"),
            "",
            "### Critic Agent 原因分析",
            "",
            _extract_iteration_content(critic_output, "原因分析"),
            "",
            "### 修复动作",
            "",
            _extract_iteration_content(critic_output, "修复方案"),
            "",
            "### 修订版方案摘要",
            "",
            revision_summary,
            "",
            "### 修复后预期收益",
            "",
            revision_summary,
            "",
            "### 下一轮迭代方向",
            "",
            _extract_iteration_content(critic_output, "下一轮迭代建议"),
        ]
    )


def _format_rag_debug(rag_debug: list[dict[str, Any]] | None) -> str:
    if not rag_debug:
        return "暂无 RAG 调试信息"

    lines: list[str] = []
    for item in rag_debug:
        source_file = item.get("source_file", "unknown")
        score = item.get("score")
        retrieval_method = item.get("retrieval_method", "unknown")
        preview = item.get("matched_preview", "暂无内容")
        score_text = str(score) if score is not None else "暂无分数"
        lines.extend(
            [
                f"### {source_file}",
                "",
                f"- 检索方式：{retrieval_method}",
                f"- 分数：{score_text}",
                f"- 片段预览：{preview}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def export_growthpilot_report(result: dict, idea: str) -> str:
    outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
    rag_debug = result.get("rag_debug", []) if isinstance(result, dict) else []
    if not isinstance(outputs, dict):
        outputs = {}

    critic_output = _safe_content(outputs, "critic")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [
        "# GrowthPilot Agent 增长实验设计报告",
        "",
        f"生成时间：{generated_at}",
        "",
        "## 用户输入的商业想法",
        "",
        idea.strip() or "暂无内容",
        "",
    ]

    for key, title in REPORT_SECTIONS:
        parts.extend([f"## {title}", "", _safe_content(outputs, key), ""])

    parts.extend(
        [
            "## Iteration Log / 迭代闭环说明",
            "",
            _build_iteration_log(critic_output),
            "",
            "## RAG 检索来源",
            "",
            _format_rag_debug(rag_debug),
            "",
            "## 导出说明",
            "",
            "本报告由 GrowthPilot Agent 自动生成。若未配置 API key，内容来自本地 mock fallback；若已配置 OpenAI-compatible API，则内容来自 LLM 工作流生成。",
            "",
        ]
    )
    return "\n".join(parts)
