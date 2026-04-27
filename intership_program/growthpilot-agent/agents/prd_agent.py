from __future__ import annotations

import re

from utils.llm import call_llm
from utils.parser import format_retrieved_context, format_upstream_outputs


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 PRD Agent，擅长把增长实验和需求池整理成产品需求文档初稿。
输出要清晰、完整、可进入 MVP 开发讨论。
不要输出日期字段、审阅时间字段或任何固定历史日期。
"""


def _mock_prd(idea: str) -> dict[str, str]:
    prd_md = f"""
# PRD 初稿：Growth Experiment MVP

## 项目背景
用户输入的商业想法是：{idea}

当前目标不是一次性做完整产品，而是验证关键转化路径和首个增长实验。

## 目标用户
有明确需求、正在比较方案、但首次转化前仍缺少信任和行动理由的新用户。

## 用户痛点
- 不知道产品是否适合自己。
- 首次尝试成本高。
- 缺少评价、案例或保障信息。
- 转化流程可能过长。

## 产品目标
- 明确目标用户和转化漏斗。
- 设计至少 1 个可执行增长实验。
- 支持 A/B 测试方案沉淀。
- 输出可进入开发讨论的 MVP 功能列表和埋点方案。

## 核心用户路径
访问 Landing Page -> 理解价值主张 -> 查看权益和信任证明 -> 点击 CTA -> 完成留资 / 下单 / 发布等关键行动。

## 功能需求
| 功能 | 说明 | 验证指标 |
| --- | --- | --- |
| 首屏价值主张 | 展示人群、场景、收益和 CTA | 首屏 CTA 点击率 |
| 新人权益 | 展示低成本尝试理由 | 新用户转化率 |
| 用户证据 | 展示评价、案例或成交记录 | 加购 / 留资率 |
| 简化转化流程 | 控制关键行动步骤 | 表单完成率 / 支付完成率 |

## 非功能需求
- 页面加载速度稳定，核心内容优先展示。
- 文案和权益信息可配置。
- 埋点事件命名清晰，便于后续分析。

## 验收标准
- 用户能在首屏理解产品面向谁、解决什么问题、下一步做什么。
- 至少一个 A/B 测试能被配置并追踪。
- 关键漏斗事件能被记录。

## 数据指标
- 首屏 CTA 点击率
- 加购 / 留资率
- 首单 / 关键行动转化率
- A/B 版本转化率差异

## 风险与边界
- 第一版不做复杂推荐算法、支付风控、会员体系或自动投放平台。
- 如果输入过于宽泛，需要在下一轮增加追问逻辑。
"""

    return {"prd": prd_md.strip()}


def _sanitize_prd_output(text: str) -> str:
    create_date_label = "\u521b\u5efa\u65e5\u671f"
    create_time_label = "\u521b\u5efa\u65f6\u95f4"
    review_time_label = "\u5ba1\u67e5\u65f6\u95f4"
    cleaned_lines: list[str] = []
    for line in text.splitlines():
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
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def build_prd_bundle(
    idea: str,
    outputs: dict[str, str],
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_prd(idea)
    retrieved_context = format_retrieved_context(context)
    upstream_outputs = format_upstream_outputs(outputs)

    prompt = f"""
商业想法：
{idea}

以下是从本地知识库检索到的业务模板和参考资料：
{retrieved_context}

上游 Agent 输出：
{upstream_outputs}

请输出 Markdown PRD 初稿，必须包含以下章节：
- 项目背景
- 目标用户
- 用户痛点
- 产品目标
- 核心用户路径
- 功能需求
- 非功能需求
- 验收标准
- 数据指标
- 风险与边界

要求：
- 不要输出日期字段、审阅时间字段或任何固定历史日期。
- 禁止输出空泛建议。
- 功能需求必须绑定漏斗环节、具体动作、核心指标和可验证方式。
- 数据指标必须能支持 A/B 测试和后续迭代判断。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    result = {"prd": _sanitize_prd_output(llm_output) if llm_output else fallback["prd"]}
    used_fallback = not bool(llm_output)
    if return_meta:
        return result, used_fallback
    return result
