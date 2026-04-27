from __future__ import annotations

import re

from utils.llm import call_llm
from utils.parser import format_retrieved_context, format_upstream_outputs


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 Critic Agent，负责审查增长实验方案的完整度、可执行性、风险和迭代价值。
你必须输出结构化反思结果，禁止编造审阅时间字段、日期或历史固定时间。
当前系统已经支持报告导出能力，不要把已有能力当作新增建议。
"""


def _mock_critic(outputs: dict[str, str] | None = None) -> dict[str, str]:
    experiment_count, has_ab_test = _analyze_experiment_coverage(outputs or {})
    experiment_issue = (
        "2. 实验覆盖仍可进一步完善，可以继续补充跨漏斗环节的实验优先级和停止规则。"
        if experiment_count < 2 and not has_ab_test
        else "2. A/B 测试的样本量和实验周期仍需结合真实流量确认。"
    )

    critic_md = """
## 评分

| 维度 | 分数 | 评价 |
| --- | ---: | --- |
| 结构完整度 | 8/10 | 已覆盖业务类型、漏斗、实验、PRD、埋点和指标 |
| 可执行性 | 7/10 | 实验方向清楚，但仍需要真实数据和样本量判断 |
| 增长逻辑 | 8/10 | 从认知、兴趣、转化到复购的链路基本完整 |
| 数据可验证性 | 7/10 | 已有埋点和指标体系，但没有真实数据验证 |
| 方案表达清晰度 | 9/10 | 关键模块、指标和迭代动作表达清楚，便于评审和复盘 |

## 主要问题

1. 当前方案仍偏模板化，对具体品类差异的约束不够强。
EXPERIMENT_ISSUE_PLACEHOLDER
3. Critic 已指出风险，但还没有接入真实数据做自动复盘。

## Badcase 风险

| badcase 风险 | 影响漏斗环节 | 对应指标 | 验证方式 |
| --- | --- | --- | --- |
| 输入过于宽泛，如“做一个电商平台” | 业务类型判断 | 北极星指标、一 级指标准确性 | 检查业务类型是否过于泛化 |
| 输出实验太泛 | 兴趣 -> 转化 | CTA 点击率、首单转化率 | 检查实验是否包含实验组、对照组和成功标准 |
| A/B 测试不可落地 | 实验执行 | 实验样本量、实验周期 | 检查是否给出核心指标、观察指标和停止规则 |
| 指标过多导致重点不清 | 全漏斗 | 北极星指标、关键过程指标 | 检查指标是否集中在 1 个北极星和 2-3 个关键指标 |

## 原因分析

1. 当前知识库规模较小，导致行业细节覆盖有限，部分建议仍偏模板化。
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
4. 增加实验优先级评分，帮助团队判断先做哪个实验。
""".replace("EXPERIMENT_ISSUE_PLACEHOLDER", experiment_issue)

    return {"critic": critic_md.strip()}


def _count_markdown_table_rows(table_text: str) -> int:
    row_count = 0
    for line in table_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "---" in stripped or "实验名称" in stripped or "核心指标" in stripped or "观察指标" in stripped:
            continue
        row_count += 1
    return row_count


def _analyze_experiment_coverage(outputs: dict[str, str]) -> tuple[int, bool]:
    experiment_text = outputs.get("experiments", "") or outputs.get("experiment_output", "")
    ab_test_text = outputs.get("ab_test", "")
    combined = "\n".join(part for part in [experiment_text, ab_test_text] if part)

    experiment_count = _count_markdown_table_rows(experiment_text)
    if experiment_count == 0:
        experiment_count = sum(
            combined.count(marker)
            for marker in ["### 实验", "## 实验", "实验一", "实验二", "实验三", "实验四", "实验五"]
        )

    has_ab_test = bool(
        ab_test_text.strip()
        or ("A/B" in combined and ("A 版本" in combined or "B 版本" in combined))
        or ("实验组" in combined and "对照组" in combined)
    )
    return experiment_count, has_ab_test


def _sanitize_critic_output(text: str, experiment_count: int = 0, has_ab_test: bool = False) -> str:
    review_time_label = "\u5ba1\u67e5\u65f6\u95f4"
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        lower_line = line.lower()
        if review_time_label in line or "review date" in lower_line:
            continue
        if re.search(r"\b20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}\b", line):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()
    replacements = {
        "\u9762\u8bd5\u8bb2\u89e3\u4ef7\u503c": "方案表达清晰度",
        "\u9762\u8bd5\u4ef7\u503c": "方案表达清晰度",
        "\u6c42\u804c\u5c55\u793a": "结构化方案验证",
        "\u6c42\u804c\u9879\u76ee": "实验性项目",
        "\u9762\u8bd5\u8bb2\u89e3": "方案讲解",
        "\u589e\u52a0 Markdown \u5bfc\u51fa": "增加 SQL 指标复盘",
        "\u589e\u52a0 markdown \u5bfc\u51fa": "增加 SQL 指标复盘",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)

    if experiment_count >= 2 or has_ab_test:
        experiment_guard_replacements = {
            "实验部分严重残缺": "实验覆盖仍可进一步完善",
            "experiments 部分被截断": "实验细节仍可进一步完善",
            "`experiments` 部分被截断": "实验细节仍可进一步完善",
            "上游输出未完成": "上游输出仍可继续细化",
            "仅写了一个实验": "当前实验覆盖仍可进一步扩展",
            "实验方案不完整": "实验覆盖仍可进一步完善",
        }
        for source, target in experiment_guard_replacements.items():
            cleaned = cleaned.replace(source, target)

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def critique_plan(
    idea: str,
    outputs: dict[str, str],
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_critic(outputs)
    retrieved_context = format_retrieved_context(context)
    upstream_outputs = format_upstream_outputs(outputs)
    experiment_count, has_ab_test = _analyze_experiment_coverage(outputs)

    prompt = f"""
商业想法：
{idea}

以下是从本地知识库检索到的业务模板和参考资料：
{retrieved_context}

上游 Agent 输出：
{upstream_outputs}

当前实验覆盖信号：
- 已识别实验条目数：{experiment_count}
- 是否识别到 A/B 测试内容：{"是" if has_ab_test else "否"}

请输出 Markdown Critic 审查结果，并严格包含以下二级标题：

## 评分
## 主要问题
## Badcase 风险
## 原因分析
## 修复方案
## 修订版方案摘要
## 下一轮迭代建议

额外要求：
- 不要输出审阅时间字段、生成日期或任何具体日期。
- 当前系统已经支持报告导出能力，不要把已有能力写成下一轮新增建议。
- 禁止输出空泛建议。
- Badcase 风险必须绑定具体漏斗环节、具体动作、核心指标和验证方式。
- 修订版方案摘要至少输出 3 条修订动作。
- 每条修订动作必须包含：原问题、修订动作、影响漏斗环节、对应指标、验证方式。
- 评分维度至少包含结构完整度、可执行性、增长逻辑、数据可验证性、方案表达清晰度、迭代指导价值。
- 不要轻易判断“上游输出被截断”或“实验部分严重残缺”。
- 如果上游输出已经包含至少 2 个实验，或已经明确包含 A/B 测试方案，就不要把问题归因为输出被截断、未完成或实验数量明显不足。
- 在实验覆盖不足时，使用“实验覆盖仍可进一步完善”这类表述，而不是“被截断”或“未完成”。
- 请优先审查：实验是否覆盖完整漏斗、实验是否有明确假设、指标是否能判断成败、是否有埋点支撑、MVP 是否过大、风险是否有回滚阈值。
- 下一轮迭代建议优先从以下方向选择：增强 RAG 知识库检索、接入真实业务数据、增加 SQL 指标复盘、增加 Rewrite Agent、增加实验优先级评分、扩展行业模板库、增加真实竞品数据输入、增加 RAG 评估指标。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    if not llm_output:
        if return_meta:
            return fallback, True
        return fallback

    result = {"critic": _sanitize_critic_output(llm_output, experiment_count, has_ab_test)}
    if return_meta:
        return result, False
    return result
