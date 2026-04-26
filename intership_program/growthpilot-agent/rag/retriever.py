from __future__ import annotations

from pathlib import Path
from typing import Any

from rag.vector_store import KeywordVectorStore

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    HAS_SKLEARN = True
except Exception:
    TfidfVectorizer = None
    cosine_similarity = None
    HAS_SKLEARN = False


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

DEFAULT_GROWTH_CONTEXT = """
来源：default_growth_analysis_template
内容：
# 默认增长分析模板

## 漏斗
访问 -> 兴趣 -> 加购 / 留资 -> 转化 -> 复购 / 推荐

## 实验设计
每个实验必须包含漏斗环节、业务假设、实验组、对照组、核心指标、观察指标、成功标准和风险。

## 需求池
每条需求必须绑定用户痛点、漏斗环节、影响指标、优先级、迭代阶段和验收标准。

## 埋点和指标
埋点必须包含 event_name、trigger、properties、purpose、related_metric。
指标体系至少包含北极星指标、一级指标、过程指标和实验判断指标。

## Critic
需要检查输出是否空泛、实验是否可执行、指标是否匹配漏斗、PRD 是否有验收标准、埋点是否有属性。
""".strip()


def load_markdown_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    if not KNOWLEDGE_BASE_DIR.exists():
        return documents

    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        documents.append(
            {
                "title": path.stem,
                "source": path.name,
                "path": str(path),
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return documents


def _default_debug_entry() -> list[dict[str, Any]]:
    return [
        {
            "source_file": "default_growth_analysis_template",
            "score": None,
            "matched_preview": DEFAULT_GROWTH_CONTEXT[:150],
            "retrieval_method": "fallback",
        }
    ]


def _format_context(documents: list[dict[str, str]]) -> str:
    if not documents:
        return DEFAULT_GROWTH_CONTEXT

    parts: list[str] = []
    for doc in documents:
        source = doc.get("source") or Path(doc.get("path", "")).name or doc.get("title", "unknown.md")
        content = doc.get("content", "").strip()
        if not content:
            continue
        parts.append(f"来源：{source}\n内容：\n{content}")

    return "\n\n---\n\n".join(parts) if parts else DEFAULT_GROWTH_CONTEXT


def _build_debug_entry(
    document: dict[str, str],
    retrieval_method: str,
    score: float | None = None,
) -> dict[str, Any]:
    preview = document.get("content", "").strip().replace("\n", " ")[:150]
    return {
        "source_file": document.get("source") or Path(document.get("path", "")).name or document.get("title", "unknown.md"),
        "score": round(score, 4) if score is not None else None,
        "matched_preview": preview or "暂无内容",
        "retrieval_method": retrieval_method,
    }


def _retrieve_with_tfidf(
    query: str,
    documents: list[dict[str, str]],
    top_k: int,
) -> list[tuple[dict[str, str], float]]:
    if not HAS_SKLEARN or TfidfVectorizer is None or cosine_similarity is None:
        return []

    corpus = [query] + [doc.get("content", "") for doc in documents]
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    selected: list[tuple[dict[str, str], float]] = []
    for index, score in ranked[:top_k]:
        if score <= 0:
            continue
        selected.append((documents[index], float(score)))
    return selected


def _retrieve_with_keywords(
    query: str,
    documents: list[dict[str, str]],
    top_k: int,
) -> list[dict[str, str]]:
    store = KeywordVectorStore(documents)
    return store.search(query, top_k=top_k)


def retrieve_context_with_debug(query: str, top_k: int = 3) -> tuple[str, list[dict[str, Any]]]:
    try:
        documents = load_markdown_documents()
        if not documents:
            return DEFAULT_GROWTH_CONTEXT, _default_debug_entry()

        tfidf_selected = _retrieve_with_tfidf(query, documents, top_k)
        if tfidf_selected:
            selected_documents = [doc for doc, _ in tfidf_selected[:top_k]]
            debug = [
                _build_debug_entry(doc, "tfidf", score)
                for doc, score in tfidf_selected[:top_k]
            ]
            return _format_context(selected_documents), debug

        keyword_selected = _retrieve_with_keywords(query, documents, top_k)
        if keyword_selected:
            debug = [
                _build_debug_entry(doc, "keyword")
                for doc in keyword_selected[:top_k]
            ]
            return _format_context(keyword_selected[:top_k]), debug

        return DEFAULT_GROWTH_CONTEXT, _default_debug_entry()
    except Exception:
        return DEFAULT_GROWTH_CONTEXT, _default_debug_entry()


def retrieve_context(query: str, top_k: int = 3) -> str:
    """Retrieve local markdown context using TF-IDF, with keyword fallback."""
    context, _debug = retrieve_context_with_debug(query, top_k=top_k)
    return context
