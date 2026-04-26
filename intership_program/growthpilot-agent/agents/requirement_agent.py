from __future__ import annotations

from utils.llm import call_llm
from utils.parser import format_retrieved_context, format_upstream_outputs


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 Requirement Agent，擅长把增长实验转成需求池。
你的输出必须能被产品经理用于排期和验收。
"""


def _mock_requirement_pool() -> dict[str, str]:
    requirement_pool_md = """
| 需求名称 | 用户痛点 | 对应漏斗环节 | 影响指标 | 优先级 | 迭代阶段 | 验收标准 |
| --- | --- | --- | --- | --- | --- | --- |
| 首屏价值主张模块 | 用户无法快速判断产品是否适合自己 | 访问 -> 兴趣 | 首屏 CTA 点击率、跳出率 | P0 | MVP | 首屏包含人群、场景、收益和 CTA |
| 新人权益模块 | 首次尝试成本高，用户犹豫 | 兴趣 -> 加购 / 留资 | 首单 / 留资转化率 | P0 | MVP | 可配置权益名称、说明、有效期和 CTA |
| 用户证据模块 | 缺少信任证明，不敢行动 | 兴趣 -> 加购 / 留资 | 加购率、表单开始率 | P1 | V1.1 | 支持展示评价、案例或交易记录 |
| 简化转化表单 | 流程太长导致中途放弃 | 加购 / 留资 -> 转化 | 表单完成率、支付完成率 | P1 | V1.1 | 关键字段不超过 3 个，提交失败有提示 |
| 实验数据看板 | 业务方不知道实验是否有效 | 全漏斗 | 访问、点击、转化和转化率 | P2 | V2.0 | 展示分版本漏斗指标和转化率 |
"""

    return {"requirement_pool": requirement_pool_md.strip()}


def build_requirement_pool(
    idea: str,
    outputs: dict[str, str],
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_requirement_pool()
    retrieved_context = format_retrieved_context(context)
    upstream_outputs = format_upstream_outputs(outputs)

    prompt = f"""
商业想法：
{idea}

以下是从本地知识库检索到的业务模板和参考资料：
{retrieved_context}

上游 Agent 输出：
{upstream_outputs}

请输出 Markdown 需求池。每条需求必须包含：
- 需求名称
- 用户痛点
- 对应漏斗环节
- 影响指标
- 优先级 P0/P1/P2
- 迭代阶段 MVP/V1.1/V2.0
- 验收标准

要求：
- 禁止输出空泛建议。
- 每条需求必须能对应上游实验或漏斗问题。
- 每条需求必须绑定核心指标和可验证方式。
- 优先使用表格表达。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    result = {"requirement_pool": llm_output or fallback["requirement_pool"]}
    used_fallback = not bool(llm_output)
    if return_meta:
        return result, used_fallback
    return result
