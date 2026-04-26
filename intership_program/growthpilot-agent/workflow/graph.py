from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict

from agents.critic_agent import critique_plan
from agents.experiment_agent import design_experiments
from agents.funnel_agent import build_funnel
from agents.mvp_agent import build_mvp_features
from agents.prd_agent import build_prd_bundle
from agents.requirement_agent import build_requirement_pool
from agents.router import route_business
from rag.retriever import retrieve_context_with_debug

try:
    from langgraph.graph import END, StateGraph

    HAS_LANGGRAPH = True
except Exception:
    END = "__end__"
    StateGraph = None
    HAS_LANGGRAPH = False


ProgressCallback = Callable[[str, str], None]


class GrowthState(TypedDict, total=False):
    idea: str
    context: str
    rag_debug: list[dict[str, Any]]
    outputs: dict[str, str]
    statuses: list[dict[str, str]]


def _finalize_result(state: GrowthState) -> GrowthState:
    outputs = state.get("outputs", {})
    statuses = state.get("statuses", [])
    finalized: GrowthState = dict(state)
    finalized["router_output"] = {
        "business_type": outputs.get("business_type", ""),
        "target_user": outputs.get("target_user", ""),
    }
    finalized["funnel_output"] = outputs.get("funnel", "")
    finalized["experiment_output"] = {
        "experiments": outputs.get("experiments", ""),
        "ab_test": outputs.get("ab_test", ""),
    }
    finalized["requirement_output"] = outputs.get("requirement_pool", "")
    finalized["prd_output"] = outputs.get("prd", "")
    finalized["mvp_output"] = {
        "mvp_features": outputs.get("mvp_features", ""),
        "event_tracking": outputs.get("event_tracking", ""),
        "metrics": outputs.get("metrics", ""),
        "landing_page": outputs.get("landing_page", ""),
    }
    finalized["critic_output"] = outputs.get("critic", "")
    finalized["steps_status"] = statuses
    return finalized


def _with_update(
    state: GrowthState,
    step_key: str,
    step: str,
    message: str,
    new_outputs: dict[str, str],
    progress_callback: ProgressCallback | None = None,
    rag_debug: list[dict[str, Any]] | None = None,
) -> GrowthState:
    outputs = dict(state.get("outputs", {}))
    outputs.update(new_outputs)

    statuses = list(state.get("statuses", []))
    statuses.append({"step_key": step_key, "step": step, "message": message})

    if progress_callback is not None:
        progress_callback(step_key, message)

    return {
        "idea": state["idea"],
        "context": state.get("context", ""),
        "rag_debug": rag_debug if rag_debug is not None else state.get("rag_debug", []),
        "outputs": outputs,
        "statuses": statuses,
    }


def _progress_message(base_message: str, used_fallback: bool) -> str:
    if used_fallback:
        return f"{base_message}（已使用 fallback）"
    return base_message


def router_node(
    state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    outputs, used_fallback = route_business(
        state["idea"],
        state.get("context", ""),
        return_meta=True,
    )
    return _with_update(
        state,
        "route_scenario",
        "Router Agent",
        _progress_message("业务类型判断完成", used_fallback),
        outputs,
        progress_callback=progress_callback,
    )


def funnel_node(
    state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    outputs, used_fallback = build_funnel(
        state["idea"],
        state.get("outputs", {}),
        state.get("context", ""),
        return_meta=True,
    )
    return _with_update(
        state,
        "generate_funnel",
        "Funnel Agent",
        _progress_message("转化漏斗生成完成", used_fallback),
        outputs,
        progress_callback=progress_callback,
    )


def experiment_node(
    state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    outputs, used_fallback = design_experiments(
        state["idea"],
        state.get("outputs", {}),
        state.get("context", ""),
        return_meta=True,
    )
    return _with_update(
        state,
        "generate_experiments",
        "Experiment Agent",
        _progress_message("增长实验与 A/B 测试生成完成", used_fallback),
        outputs,
        progress_callback=progress_callback,
    )


def requirement_node(
    state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    outputs, used_fallback = build_requirement_pool(
        state["idea"],
        state.get("outputs", {}),
        state.get("context", ""),
        return_meta=True,
    )
    return _with_update(
        state,
        "generate_requirements",
        "Requirement Agent",
        _progress_message("需求池生成完成", used_fallback),
        outputs,
        progress_callback=progress_callback,
    )


def prd_node(
    state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    outputs, used_fallback = build_prd_bundle(
        state["idea"],
        state.get("outputs", {}),
        state.get("context", ""),
        return_meta=True,
    )
    return _with_update(
        state,
        "generate_prd",
        "PRD Agent",
        _progress_message("PRD 初稿生成完成", used_fallback),
        outputs,
        progress_callback=progress_callback,
    )


def mvp_node(
    state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    outputs, used_fallback = build_mvp_features(
        state["idea"],
        state.get("outputs", {}),
        state.get("context", ""),
        return_meta=True,
    )
    return _with_update(
        state,
        "generate_mvp",
        "MVP Agent",
        _progress_message("MVP、埋点与指标体系生成完成", used_fallback),
        outputs,
        progress_callback=progress_callback,
    )


def critic_node(
    state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    outputs, used_fallback = critique_plan(
        state["idea"],
        state.get("outputs", {}),
        state.get("context", ""),
        return_meta=True,
    )
    return _with_update(
        state,
        "critique_result",
        "Critic Agent",
        _progress_message("Critic 评分与 badcase 分析完成", used_fallback),
        outputs,
        progress_callback=progress_callback,
    )


def build_graph(progress_callback: ProgressCallback | None = None) -> Any:
    """Build the LangGraph workflow when LangGraph is installed."""
    if not HAS_LANGGRAPH or StateGraph is None:
        return None

    graph = StateGraph(GrowthState)
    graph.add_node("router", lambda state: router_node(state, progress_callback))
    graph.add_node("funnel", lambda state: funnel_node(state, progress_callback))
    graph.add_node("experiment", lambda state: experiment_node(state, progress_callback))
    graph.add_node("requirement", lambda state: requirement_node(state, progress_callback))
    graph.add_node("prd", lambda state: prd_node(state, progress_callback))
    graph.add_node("mvp", lambda state: mvp_node(state, progress_callback))
    graph.add_node("critic", lambda state: critic_node(state, progress_callback))

    graph.set_entry_point("router")
    graph.add_edge("router", "funnel")
    graph.add_edge("funnel", "experiment")
    graph.add_edge("experiment", "requirement")
    graph.add_edge("requirement", "prd")
    graph.add_edge("prd", "mvp")
    graph.add_edge("mvp", "critic")
    graph.add_edge("critic", END)

    return graph.compile()


def _run_sequential(
    initial_state: GrowthState,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    state = router_node(initial_state, progress_callback)
    state = funnel_node(state, progress_callback)
    state = experiment_node(state, progress_callback)
    state = requirement_node(state, progress_callback)
    state = prd_node(state, progress_callback)
    state = mvp_node(state, progress_callback)
    state = critic_node(state, progress_callback)
    return state


def run_growthpilot_workflow(
    idea: str,
    progress_callback: ProgressCallback | None = None,
) -> GrowthState:
    """Run GrowthPilot Agent and return structured outputs for the UI."""
    context, rag_debug = retrieve_context_with_debug(idea, top_k=4)
    rag_methods = {item.get("retrieval_method", "fallback") for item in rag_debug}
    rag_message = "RAG 检索完成"
    if rag_methods == {"keyword"}:
        rag_message = "RAG 检索完成（已使用 keyword fallback）"
    elif rag_methods == {"fallback"}:
        rag_message = "RAG 检索完成（已使用默认模板 fallback）"

    initial_state: GrowthState = {
        "idea": idea,
        "context": context,
        "rag_debug": rag_debug,
        "outputs": {},
        "statuses": [],
    }
    initial_state = _with_update(
        initial_state,
        "retrieve_context",
        "RAG Retriever",
        rag_message,
        {},
        progress_callback=progress_callback,
        rag_debug=rag_debug,
    )

    compiled_graph = build_graph(progress_callback)
    if compiled_graph is None:
        return _finalize_result(_run_sequential(initial_state, progress_callback))

    return _finalize_result(compiled_graph.invoke(initial_state))


def run_growthpilot(idea: str) -> GrowthState:
    """Backward-compatible alias for older examples."""
    return run_growthpilot_workflow(idea)
