from __future__ import annotations

import re
from collections.abc import Sequence


RetrievedContext = str | Sequence[dict[str, str]] | None


def normalize_markdown(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def join_sections(sections: dict[str, str]) -> str:
    parts: list[str] = []
    for title, content in sections.items():
        parts.append(f"## {title}\n\n{normalize_markdown(content)}")
    return "\n\n".join(parts)


def format_retrieved_context(context: RetrievedContext, max_chars: int = 6000) -> str:
    if not context:
        return "未检索到相关知识库资料。"

    if isinstance(context, str):
        return normalize_markdown(context[:max_chars]) or "未检索到相关知识库资料。"

    parts: list[str] = []
    used_chars = 0
    for index, item in enumerate(context, start=1):
        title = item.get("title", f"doc_{index}")
        source = item.get("source") or item.get("path") or title
        content = normalize_markdown(item.get("content", ""))
        if not content:
            continue

        remaining = max_chars - used_chars
        if remaining <= 0:
            break

        content = content[:remaining]
        used_chars += len(content)
        parts.append(f"来源：{source}\n内容：\n{content}")

    return "\n\n".join(parts) if parts else "未检索到相关知识库资料。"


def format_upstream_outputs(outputs: dict[str, str] | None, max_chars: int = 7000) -> str:
    if not outputs:
        return "暂无上游 Agent 输出。"

    parts: list[str] = []
    used_chars = 0
    for key, value in outputs.items():
        content = normalize_markdown(value)
        if not content:
            continue

        remaining = max_chars - used_chars
        if remaining <= 0:
            break

        content = content[:remaining]
        used_chars += len(content)
        parts.append(f"## {key}\n{content}")

    return "\n\n".join(parts) if parts else "暂无上游 Agent 输出。"


def extract_markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return normalize_markdown(match.group("body"))
