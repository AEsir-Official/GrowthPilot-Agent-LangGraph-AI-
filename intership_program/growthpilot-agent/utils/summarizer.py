from __future__ import annotations

import re

from utils.parser import extract_markdown_section


def _clean_text(text: str) -> str:
    return " ".join(text.strip().split())


def _extract_bold_value(text: str, label: str) -> str:
    patterns = [
        rf"\*\*{re.escape(label)}：\*\*\s*(.+)",
        rf"\*\*{re.escape(label)}\*\*：\s*(.+)",
        rf"{re.escape(label)}：\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return _clean_text(match.group(1))
    return "暂无内容"


def _extract_markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").strip()) <= {"-", " "}:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if rows:
            rows.append(cells)
            continue
        if "漏斗阶段" in cells[0] or "实验名称" in cells[0] or "需求名称" in cells[0] or "badcase 风险" in cells[0]:
            rows.append(cells)
    return rows


def _extract_table_column(text: str, index: int = 0, limit: int = 3) -> list[str]:
    rows = _extract_markdown_table_rows(text)
    if len(rows) <= 1:
        return []
    values: list[str] = []
    for row in rows[1:]:
        if index >= len(row):
            continue
        value = _clean_text(row[index])
        if value and value not in {"---", ""}:
            values.append(value)
        if len(values) >= limit:
            break
    return values


def _extract_p0_requirements(text: str, limit: int = 3) -> list[str]:
    rows = _extract_markdown_table_rows(text)
    if len(rows) <= 1:
        return []

    results: list[str] = []
    for row in rows[1:]:
        joined = " | ".join(row)
        if "P0" not in joined:
            continue
        results.append(_clean_text(row[0]))
        if len(results) >= limit:
            break
    return results


def _extract_numbered_items(text: str, limit: int = 3) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^\d+\.\s+", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped))
        elif stripped.startswith("- "):
            items.append(stripped[2:].strip())
        if len(items) >= limit:
            break
    return items


def _extract_core_funnel(text: str) -> str:
    stages = _extract_table_column(text, index=0, limit=5)
    if stages:
        return " -> ".join(stages)

    match = re.search(r"访问.*?复购\s*/\s*推荐", _clean_text(text))
    if match:
        return match.group(0)
    return "暂无内容"


def build_solution_summary(outputs: dict[str, str]) -> dict[str, str | list[str]]:
    business_text = outputs.get("business_type", "")
    funnel_text = outputs.get("funnel", "")
    experiments_text = outputs.get("experiments", "")
    requirements_text = outputs.get("requirement_pool", "")
    metrics_text = outputs.get("metrics", "")
    critic_text = outputs.get("critic", "")

    north_star = _extract_bold_value(business_text, "北极星指标")
    if north_star == "暂无内容":
        north_star = _extract_bold_value(metrics_text, "北极星指标")

    critic_main_issues = extract_markdown_section(critic_text, "主要问题") or "暂无内容"
    critic_iteration = extract_markdown_section(critic_text, "下一轮迭代建议") or "暂无内容"
    badcase_section = extract_markdown_section(critic_text, "Badcase 风险") or critic_text

    badcases = _extract_table_column(badcase_section, index=0, limit=1)
    experiments = _extract_table_column(experiments_text, index=0, limit=3)
    p0_requirements = _extract_p0_requirements(requirements_text, limit=3)
    next_iteration = _extract_numbered_items(critic_iteration, limit=3)

    return {
        "business_type": _extract_bold_value(business_text, "业务类型"),
        "north_star_metric": north_star,
        "core_funnel": _extract_core_funnel(funnel_text),
        "key_experiments": experiments or ["暂无内容"],
        "p0_requirements": p0_requirements or ["暂无内容"],
        "main_badcase": badcases[0] if badcases else _clean_text(critic_main_issues) or "暂无内容",
        "next_iteration": next_iteration or ["暂无内容"],
    }
