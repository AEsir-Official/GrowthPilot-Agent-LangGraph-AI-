from __future__ import annotations

import re

from utils.llm import call_llm
from utils.parser import format_retrieved_context, format_upstream_outputs


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 Critic Agent，负责审查增长实验方案的完整度、可执行性、风险和迭代价值。
你必须输出结构化反思结果，禁止编造审查时间、日期或历史固定时间。
"""


def _mock_critic() -> dict[str, str]:
    critic_md = """
## 评分

| 维度 | 分数 | 评价 |
| --- | ---: | --- |
| 结构完整度 | 8/10 | 已覆盖业务类型、漏斗、实验、PRD、埋点和指标 |
| 可执行性 | 7/10 | 实验方向清楚，但仍需要真实数据和样本量判断 |
| 增长逻辑 | 8/10 | 从认知、兴趣、转化到复购的链路基本完整 |
| 数据可验证性 | 7/10 | 已有埋点和指标体系，但没有真实数据验证 |
| 面试讲解价值 | 9/10 | 能体现 Agent Workflow、RAG 和反思闭环 |

## 主要问题

1. 当前方案仍偏模板化，对具体品类差异的约束不够强。
2. A/B 测试的样本量和实验周期仍需结合真实流量确认。
3. Critic 已指出风险，但还没有接入真实数据做自动复盘。

## Badcase 风险

| badcase 风险 | 影响漏斗环节 | 对应指标 | 验证方式 |
| --- | --- | --- | --- |
| 输入过于宽泛，如“做一个电商平台” | 业务类型判断 | 北极星指标、一 级指标准确性 | 检查业务类型是否过于泛化 |
| 输出实验太泛 | 兴趣 -> 转化 | CTA 点击率、首单转化率 | 检查实验是否包含实验组、对照组和成功标准 |
| A/B 测试不可落地 | 实验执行 | 实验样本量、实验周期 | 检查是否给出核心指标、观察指标和停止规则 |
| 指标过多导致重点不清 | 全漏斗 | 北极星指标、关键过程指标 | 检查指标是否集中在 1 个北极星和 2-3 个关键指标 |

## 原因分析

1. 当前项目仍以求职展示为目标，知识库规模较小，导致行业细节覆盖有限。
2. 没有接入真实实验数据，因此成功标准主要依赖规则模板和经验阈值。
3. Reflection 已经生成，但还没有把修复动作映射到真实实验结果。

## 修复方案

1. 扩充不同消费场景模板，让 Router 和 Funnel 对行业差异判断更具体。
2. 在 Experiment Agent 中补充样本量、实验周期和停止规则约束。
3. 在 Future Work 中接入真实 SQL 指标分析，把 Critic 建议和真实数据闭环起来。

## 修订版方案摘要

| 原问题 | 修订动作 | 影响漏斗环节 | 对应指标 | 验证方式 |
| --- | --- | --- | --- | --- |
| 行业判断过泛 | 增加场景模板和业务分类约束 | 业务判断 -> 漏斗建模 | 北极星指标准确性 | 检查输出是否明确到品类和用户 |
| 实验定义不够严谨 | 为每个实验补充成功标准和停止规则 | 增长实验 | CTA 点击率、转化率 | 检查实验表格字段是否完整 |
| 指标与执行脱节 | 把 P0 需求和埋点指标一一绑定 | 需求池 -> 埋点 -> 指标 | 首单转化率、留资率 | 检查需求、埋点、指标是否可追踪 |

## 下一轮迭代建议

1. 增强知识库，让不同业务类型引用更细的模板。
2. 接入真实指标数据，用 SQL 自动判断 A/B 测试是否成功。
3. 让 Critic 输出的修复动作直接映射到下一轮实验优先级。
"""

    return {"critic": critic_md.strip()}


def _sanitize_critic_output(text: str) -> str:
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        lower_line = line.lower()
        if "审查时间" in line or "review date" in lower_line:
            continue
        if re.search(r"\b20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}\b", line):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def critique_plan(
    idea: str,
    outputs: dict[str, str],
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_critic()
    retrieved_context = format_retrieved_context(context)
    upstream_outputs = format_upstream_outputs(outputs)

    prompt = f"""
商业想法：
{idea}

以下是从本地知识库检索到的业务模板和参考资料：
{retrieved_context}

上游 Agent 输出：
{upstream_outputs}

请输出 Markdown Critic 审查结果，并严格包含以下二级标题：

## 评分
## 主要问题
## Badcase 风险
## 原因分析
## 修复方案
## 修订版方案摘要
## 下一轮迭代建议

额外要求：
- 不要输出审查时间、生成日期或任何具体日期。
- 禁止输出空泛建议。
- Badcase 风险必须绑定具体漏斗环节、具体动作、核心指标和验证方式。
- 修订版方案摘要至少输出 3 条修订动作。
- 每条修订动作必须包含：原问题、修订动作、影响漏斗环节、对应指标、验证方式。
- 评分维度至少包含结构完整度、可执行性、增长逻辑、数据可验证性、面试讲解价值。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    if not llm_output:
        if return_meta:
            return fallback, True
        return fallback

    result = {"critic": _sanitize_critic_output(llm_output)}
    if return_meta:
        return result, False
    return result
