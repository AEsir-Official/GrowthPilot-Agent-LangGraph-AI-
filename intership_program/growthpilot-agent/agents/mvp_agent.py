from __future__ import annotations

from utils.llm import call_llm
from utils.parser import extract_markdown_section, format_retrieved_context, format_upstream_outputs


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 MVP Agent，擅长把 PRD 转成第一版 MVP 功能、埋点方案、指标体系和 Landing Page 文案。
输出必须能用于本地 MVP 演示和面试讲解。
"""


def _mock_mvp_bundle() -> dict[str, str]:
    mvp_md = """
| 功能 | 说明 | 对应漏斗环节 | 验证指标 | 是否第一版必须 |
| --- | --- | --- | --- | --- |
| 商业想法输入 | 用户输入一句或一段商业想法 | 输入 | 输出完成率 | 是 |
| 工作流状态展示 | 展示 Router、Funnel、Experiment、PRD、Critic 等节点状态 | 全流程 | 生成成功率 | 是 |
| 结构化结果输出 | 按模块展示漏斗、实验、需求池、PRD、埋点和指标 | 全流程 | 用户可读性 | 是 |
| 本地知识库读取 | 从 markdown 模板中检索相关上下文 | 生成前 | context 命中率 | 是 |
| Critic 评分 | 对方案完整度、可执行性和风险进行评分 | 迭代 | badcase 覆盖率 | 是 |
| Markdown 导出 | 将结果导出为 markdown 文件 | 交付 | 导出使用率 | 否，第三轮可做 |
"""

    event_tracking_md = """
| event_name | trigger | properties | purpose | related_metric |
| --- | --- | --- | --- | --- |
| page_view | 用户访问 Landing Page | source, campaign, device, variant | 计算访问量和流量来源 | UV、渠道访问量 |
| hero_cta_click | 点击首屏 CTA | variant, cta_text | 衡量首屏价值主张吸引力 | 首屏 CTA 点击率 |
| benefit_view | 曝光新人权益模块 | benefit_type, variant | 判断权益是否被看到 | 权益曝光率 |
| signup_submit | 提交表单或注册 | form_fields, variant | 衡量留资转化 | 留资转化率 |
| order_complete | 完成下单或核心转化 | price, coupon, variant | 衡量最终转化 | 首单 / 关键行动转化率 |
| share_click | 点击分享或推荐 | channel, variant | 衡量推荐意愿 | 分享点击率 |
"""

    metrics_md = """
**北极星指标：** 新用户关键行动转化数

| 指标层级 | 指标 | 说明 | 绑定漏斗环节 |
| --- | --- | --- | --- |
| 流量指标 | UV、渠道访问量 | 判断流量质量和来源 | 访问 |
| 激活指标 | 首屏 CTA 点击率 | 判断价值主张是否有效 | 访问 -> 兴趣 |
| 转化指标 | 留资率 / 首单转化率 | 判断商业路径是否跑通 | 加购 / 留资 -> 转化 |
| 收入指标 | 客单价、GMV 或付费金额 | 判断增长是否带来收入 | 转化 |
| 留存指标 | 复购率、7 日回访率 | 判断是否有长期价值 | 复购 / 推荐 |
| 实验指标 | A/B 版本转化率差异 | 判断实验是否值得保留 | 全漏斗 |
"""

    landing_page_md = """
**首屏标题：** 为你的第一次选择，找到更省心的方案

**副标题：** 基于真实场景、用户反馈和新人权益，帮你快速判断是否值得尝试。

**核心卖点：**
- 适合明确需求但不想踩坑的新用户
- 提供新人专属权益，降低首次尝试成本
- 展示真实案例和评价，减少决策不确定性

**CTA：** 领取新人权益

**信任文案：** 已帮助多位新用户完成首次尝试，下一步将持续优化转化链路。
"""

    return {
        "mvp_features": mvp_md.strip(),
        "event_tracking": event_tracking_md.strip(),
        "metrics": metrics_md.strip(),
        "landing_page": landing_page_md.strip(),
    }


def build_mvp_features(
    idea: str,
    outputs: dict[str, str],
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_mvp_bundle()
    retrieved_context = format_retrieved_context(context)
    upstream_outputs = format_upstream_outputs(outputs)

    prompt = f"""
商业想法：
{idea}

以下是从本地知识库检索到的业务模板和参考资料：
{retrieved_context}

上游 Agent 输出：
{upstream_outputs}

请输出 Markdown，并严格使用以下二级标题：

## MVP 功能
输出第一版必须做和暂缓做的功能，每个功能绑定漏斗环节、验证指标和验收方式。

## 埋点方案
埋点必须包含：
- event_name
- trigger
- properties
- purpose
- related_metric

## 指标体系
必须包含北极星指标、一级指标、过程指标和实验判断指标。

## Landing Page 文案
必须包含首屏标题、副标题、核心卖点、CTA、信任文案和可验证指标。

要求：
- 禁止输出空泛建议。
- 每条建议必须绑定漏斗环节、具体动作、核心指标和可验证方式。
- 优先输出表格，便于本地演示。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    if not llm_output:
        if return_meta:
            return fallback, True
        return fallback

    result = {
        "mvp_features": extract_markdown_section(llm_output, "MVP 功能") or llm_output,
        "event_tracking": extract_markdown_section(llm_output, "埋点方案") or llm_output,
        "metrics": extract_markdown_section(llm_output, "指标体系") or llm_output,
        "landing_page": extract_markdown_section(llm_output, "Landing Page 文案") or llm_output,
    }
    if return_meta:
        return result, False
    return result
