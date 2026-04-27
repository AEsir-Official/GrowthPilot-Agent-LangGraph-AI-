from __future__ import annotations

from utils.llm import call_llm
from utils.parser import format_retrieved_context, format_upstream_outputs


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 Funnel Agent，擅长把消费 / 电商商业想法拆成可验证的转化漏斗。
你的输出必须包含用户行为、业务问题、核心指标和可优化方向。
"""


def _mock_funnel(idea: str, outputs: dict[str, str]) -> dict[str, str]:
    business_type = outputs.get("business_type", "消费 / 电商增长场景")

    funnel_md = f"""
**适用业务：** {business_type.splitlines()[0].replace("**业务类型：**", "").strip()}

| 漏斗阶段 | 用户行为 | 业务问题 | 核心指标 | 可优化方向 |
| --- | --- | --- | --- | --- |
| 访问 | 看到广告、内容或朋友推荐后进入页面 | 价值点不清晰，用户不确定是否与自己相关 | 页面访问量、跳出率 | 首屏直接说明人群、场景和核心收益 |
| 兴趣 | 浏览产品、案例、评价或活动 | 信任不足，不知道是否适合自己 | 商品详情点击率、评价模块浏览率 | 增加场景化推荐和用户证据 |
| 加购 / 留资 | 点击购买、预约、收藏或提交信息 | 价格、信任、流程成本造成犹豫 | 加购率、表单开始率 | 新人权益、风险逆转、流程压缩 |
| 下单 / 转化 | 完成支付或关键行动 | 最后一公里犹豫，担心决策错误 | 支付完成率、提交完成率 | 倒计时、免运费、试用承诺 |
| 复购 / 推荐 | 二次购买、分享或评价 | 没有持续理由或分享动机 | 复购率、分享点击率 | 会员任务、复购提醒、推荐奖励 |

**北极星动作：** 让用户完成第一次高意向行为，例如首单、留资、试用申请、预约或发布商品。
"""

    return {"funnel": funnel_md.strip()}


def build_funnel(
    idea: str,
    outputs: dict[str, str],
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_funnel(idea, outputs)
    retrieved_context = format_retrieved_context(context)
    upstream_outputs = format_upstream_outputs(outputs)

    prompt = f"""
商业想法：
{idea}

以下是从本地知识库检索到的业务模板和参考资料：
{retrieved_context}

上游 Agent 输出：
{upstream_outputs}

请输出 Markdown 转化漏斗。每个漏斗环节必须包含：
- 用户行为
- 业务问题
- 核心指标
- 可优化方向

要求：
- 禁止输出空泛建议。
- 每条建议必须绑定漏斗环节、具体动作、核心指标和可验证方式。
- 优先使用表格表达，便于评审、复盘和结果对比。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    result = {"funnel": llm_output or fallback["funnel"]}
    used_fallback = not bool(llm_output)
    if return_meta:
        return result, used_fallback
    return result
