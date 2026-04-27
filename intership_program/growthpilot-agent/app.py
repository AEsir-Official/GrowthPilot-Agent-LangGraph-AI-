from __future__ import annotations

import re
from typing import Any

import streamlit as st

from utils.exporter import export_growthpilot_report
from utils.summarizer import build_solution_summary
from workflow.graph import run_growthpilot_workflow


DEFAULT_IDEA = "我想做一个面向大学生的平价护肤电商平台"

EXAMPLE_IDEAS = {
    "平价护肤电商平台": "我想做一个面向大学生的平价护肤电商平台",
    "校园二手交易平台": "我想做一个校园二手交易平台",
    "在线考证课程平台": "我想做一个面向大学生的在线考证课程平台",
}

PROGRESS_ORDER = [
    "retrieve_context",
    "route_scenario",
    "generate_funnel",
    "generate_experiments",
    "generate_requirements",
    "generate_prd",
    "generate_mvp",
    "critique_result",
]


def get_output(outputs: dict[str, str], key: str) -> str:
    content = outputs.get(key, "")
    return content.strip() if content and content.strip() else "暂无内容"


def count_chinese_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def render_sidebar() -> None:
    with st.sidebar:
        st.header("项目定位")
        st.markdown("面向消费 / 电商场景的 AI Growth Experiment Workflow，支持商业想法到增长实验方案的结构化生成。")

        st.header("技术栈")
        st.markdown(
            """
- Python
- Streamlit
- LangGraph
- OpenAI-compatible API
- TF-IDF RAG
- Markdown Knowledge Base
"""
        )

        st.header("核心亮点")
        st.markdown(
            """
- 多 Agent 工作流
- Critic Rewrite 闭环
- RAG Debug Panel
- A/B 测试方案
- 需求池、PRD、埋点与指标
- Markdown 报告导出
"""
        )

        st.header("技术关键词")
        st.markdown(
            """
- Agent Workflow
- LangGraph
- RAG
- A/B Testing
- Requirement Pool
- PRD
- Event Tracking
- Metrics System
- Badcase Analysis
- Iteration Logic
"""
        )


def render_status(statuses: list[dict[str, str]]) -> None:
    with st.expander("工作流状态", expanded=True):
        if not statuses:
            st.info("等待输入商业想法后启动工作流。")
            return

        for item in statuses:
            step = item.get("step", "workflow")
            message = item.get("message", "done")
            st.success(f"{step}: {message}")


def render_solution_summary(outputs: dict[str, str]) -> None:
    summary = build_solution_summary(outputs)
    with st.expander("方案摘要", expanded=True):
        st.markdown(f"**业务类型：** {summary['business_type']}")
        st.markdown(f"**北极星指标：** {summary['north_star_metric']}")
        st.markdown(f"**核心漏斗：** {summary['core_funnel']}")
        st.markdown("**3 个关键增长实验：**")
        for item in summary["key_experiments"]:
            st.markdown(f"- {item}")
        st.markdown("**3 个 P0 需求：**")
        for item in summary["p0_requirements"]:
            st.markdown(f"- {item}")
        st.markdown(f"**主要 badcase：** {summary['main_badcase']}")
        st.markdown("**下一轮迭代方向：**")
        for item in summary["next_iteration"]:
            st.markdown(f"- {item}")


def render_rag_debug_panel(rag_debug: list[dict[str, Any]]) -> None:
    with st.expander("RAG 检索调试信息 / RAG Debug Panel"):
        if not rag_debug:
            st.info("暂无 RAG 调试信息")
            return

        for item in rag_debug:
            source_file = item.get("source_file", "unknown")
            score = item.get("score")
            retrieval_method = item.get("retrieval_method", "unknown")
            preview = item.get("matched_preview", "暂无内容")
            score_text = str(score) if score is not None else "暂无分数"

            st.markdown(f"### {source_file}")
            st.markdown(f"- 检索方式：{retrieval_method}")
            st.markdown(f"- 分数：{score_text}")
            st.markdown(f"- 片段预览：{preview}")


def render_result_expanders(outputs: dict[str, str]) -> None:
    with st.expander("业务类型判断", expanded=True):
        st.markdown(get_output(outputs, "business_type"))
        st.markdown("### 目标用户画像")
        st.markdown(get_output(outputs, "target_user"))

    with st.expander("转化漏斗"):
        st.markdown(get_output(outputs, "funnel"))

    with st.expander("增长实验与 A/B 测试"):
        st.markdown("### 增长实验方案")
        st.markdown(get_output(outputs, "experiments"))
        st.markdown("### A/B 测试方案")
        st.markdown(get_output(outputs, "ab_test"))

    with st.expander("需求池"):
        st.markdown(get_output(outputs, "requirement_pool"))

    with st.expander("PRD 初稿"):
        st.markdown(get_output(outputs, "prd"))

    with st.expander("MVP 功能"):
        st.markdown(get_output(outputs, "mvp_features"))

    with st.expander("埋点方案"):
        st.markdown(get_output(outputs, "event_tracking"))

    with st.expander("指标体系"):
        st.markdown(get_output(outputs, "metrics"))

    with st.expander("Landing Page 文案"):
        st.markdown(get_output(outputs, "landing_page"))

    with st.expander("Critic 评分、badcase 和迭代建议"):
        st.markdown(get_output(outputs, "critic"))


def render_download(result: dict, idea: str) -> None:
    with st.expander("Markdown 导出"):
        if not result or not result.get("outputs"):
            st.info("生成结果后可下载 Markdown 报告。")
            return

        report = export_growthpilot_report(result, idea)
        st.download_button(
            label="下载 Markdown 报告",
            data=report,
            file_name="growthpilot_report.md",
            mime="text/markdown",
        )


def main() -> None:
    st.set_page_config(page_title="GrowthPilot Agent", layout="wide")

    if "idea_input" not in st.session_state:
        st.session_state.idea_input = DEFAULT_IDEA
    if "last_result" not in st.session_state:
        st.session_state.last_result = {}
    if "last_idea" not in st.session_state:
        st.session_state.last_idea = ""
    if "last_progress_events" not in st.session_state:
        st.session_state.last_progress_events = []

    render_sidebar()

    st.title("GrowthPilot Agent")
    st.markdown(
        "GrowthPilot Agent 是一个面向消费 / 电商场景的 AI 增长实验设计 Agent，"
        "可以将商业想法拆解为转化漏斗、A/B 测试、需求池、PRD、埋点方案、"
        "指标体系和迭代建议。"
    )

    st.subheader("输入商业想法")
    example_cols = st.columns(3)
    for column, (label, example_idea) in zip(example_cols, EXAMPLE_IDEAS.items()):
        with column:
            if st.button(label, use_container_width=True):
                st.session_state.idea_input = example_idea

    idea = st.text_area(
        "商业想法输入框",
        key="idea_input",
        height=140,
        placeholder=DEFAULT_IDEA,
    )

    if idea.strip() and count_chinese_chars(idea) < 8:
        st.warning("建议输入更具体的商业想法，例如目标用户、产品类型或场景。")

    generate = st.button("生成增长实验方案", type="primary")
    progress_bar_placeholder = st.empty()
    progress_text_placeholder = st.empty()

    if generate:
        if not idea.strip():
            st.warning("请先输入一个商业想法。")
        else:
            live_events: list[str] = []
            progress_bar = progress_bar_placeholder.progress(0)
            progress_text_placeholder.info("正在启动 GrowthPilot Agent 工作流...")

            def progress_callback(step_key: str, message: str) -> None:
                try:
                    completed = PROGRESS_ORDER.index(step_key) + 1
                except ValueError:
                    completed = len(live_events) + 1
                completed = min(completed, len(PROGRESS_ORDER))
                live_events.append(f"{completed}/{len(PROGRESS_ORDER)} ✅ {message}")
                progress_bar.progress(completed / len(PROGRESS_ORDER))
                progress_text_placeholder.markdown("\n".join(live_events))

            st.session_state.last_result = run_growthpilot_workflow(
                idea.strip(),
                progress_callback=progress_callback,
            )
            st.session_state.last_idea = idea.strip()
            st.session_state.last_progress_events = list(live_events)
            progress_bar.progress(1.0)
            progress_text_placeholder.success("全部阶段完成，报告已生成。")

    render_status(st.session_state.last_result.get("statuses", []))
    render_solution_summary(st.session_state.last_result.get("outputs", {}))
    render_rag_debug_panel(st.session_state.last_result.get("rag_debug", []))
    render_result_expanders(st.session_state.last_result.get("outputs", {}))
    render_download(st.session_state.last_result, st.session_state.last_idea or idea)


if __name__ == "__main__":
    main()
