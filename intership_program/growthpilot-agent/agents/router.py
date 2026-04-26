from __future__ import annotations

from utils.llm import call_llm
from utils.parser import extract_markdown_section, format_retrieved_context


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 Router Agent，擅长判断消费 / 电商商业想法的业务类型、目标用户、增长目标和核心指标。
你的输出必须结构化、具体、可用于后续增长实验设计。
"""


def _mock_route_business(idea: str) -> dict[str, str]:
    lower_idea = idea.lower()

    if any(word in lower_idea for word in ["护肤", "美妆", "skincare", "beauty"]):
        business_type = "美妆护肤电商"
        scenario = "高信任门槛、强内容种草、复购潜力高"
        primary_user = "18-30 岁关注功效、成分和口碑的女性用户"
        north_star = "新用户首单转化数"
    elif any(word in lower_idea for word in ["课程", "学习", "教育", "course"]):
        business_type = "在线课程 / 知识付费"
        scenario = "决策周期较长，需要证明结果和降低试错成本"
        primary_user = "有明确技能提升目标、但缺少学习路径的学生或职场新人"
        north_star = "试听课预约后付费转化数"
    elif any(word in lower_idea for word in ["二手", "闲置", "校园", "secondhand"]):
        business_type = "校园二手交易平台"
        scenario = "供需匹配、信任和交易安全是关键阻力"
        primary_user = "有闲置物品出售或低价购买需求的大学生"
        north_star = "首次发布或首次交易用户数"
    else:
        business_type = "消费 / 电商增长场景"
        scenario = "需要验证用户需求、转化路径和首单动机"
        primary_user = "对该品类有明确需求但仍在比较方案的潜在消费者"
        north_star = "新用户关键行动转化数"

    business_type_md = f"""
**业务类型：** {business_type}

**核心业务目标：** 验证用户是否愿意完成第一次关键行动，并找到影响转化的主要阻力。

**北极星指标：** {north_star}

**一级指标：**
- 访问到 CTA 点击率
- CTA 点击到关键行动转化率
- 新用户转化率
- 关键行动完成成本

**为什么适合增长实验验证：**
- 该场景的增长重点是：{scenario}。
- 用户从认知到转化之间存在清晰漏斗，可以针对每个环节设计实验。
- 首屏文案、权益、信任证明和流程长度都能通过 A/B 测试验证。
"""

    target_user_md = f"""
**核心用户画像：** {primary_user}

**用户目标：**
- 快速判断产品 / 服务是否值得尝试。
- 降低首次下单、留资、预约或发布的心理成本。
- 获得可信的案例、评价、价格或结果证明。

**主要痛点：**
- 不确定方案是否适合自己。
- 信息过载，难以比较。
- 首次转化前缺少信任触发点。

**关键触发点：**
- 明确利益点
- 社会证明
- 限时权益
- 低风险试用
"""

    return {
        "business_type": business_type_md.strip(),
        "target_user": target_user_md.strip(),
    }


def route_business(
    idea: str,
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_route_business(idea)
    retrieved_context = format_retrieved_context(context)

    prompt = f"""
商业想法：
{idea}

以下是从本地知识库检索到的业务模板和参考资料：
{retrieved_context}

请基于商业想法和本地知识库，输出 Markdown，并严格使用以下二级标题：

## 业务类型判断
- 业务类型
- 核心业务目标
- 北极星指标
- 一级指标
- 为什么适合增长实验验证

## 目标用户画像
- 核心用户画像
- 用户目标
- 主要痛点
- 关键触发点

要求：
- 禁止输出空泛建议。
- 每条判断都要尽量绑定漏斗环节、具体动作、核心指标和可验证方式。
- 输出要适合后续 Funnel Agent、Experiment Agent 和 PRD Agent 继续使用。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    if not llm_output:
        if return_meta:
            return fallback, True
        return fallback

    business_type = extract_markdown_section(llm_output, "业务类型判断") or llm_output
    target_user = extract_markdown_section(llm_output, "目标用户画像") or llm_output
    result = {
        "business_type": business_type,
        "target_user": target_user,
    }
    if return_meta:
        return result, False
    return result
