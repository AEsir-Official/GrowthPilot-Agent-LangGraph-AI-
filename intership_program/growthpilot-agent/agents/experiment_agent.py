from __future__ import annotations

from utils.llm import call_llm
from utils.parser import extract_markdown_section, format_retrieved_context, format_upstream_outputs


SYSTEM_PROMPT = """
你是 GrowthPilot Agent 的 Experiment Agent，擅长设计增长实验和 A/B 测试。
你的方案必须有业务假设、实验组、对照组、指标、成功标准和风险。
"""


def _mock_experiments() -> dict[str, str]:
    experiments_md = """
| 实验名称 | 漏斗环节 | 业务假设 | 实验组 | 对照组 | 核心指标 | 观察指标 | 成功标准 | 风险 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 首屏价值主张实验 | 访问 -> 兴趣 | 用户需要在 5 秒内理解产品价值 | 首屏改为「人群 + 场景 + 结果」结构 | 原始功能型标题 | 首屏 CTA 点击率 | 跳出率、停留时长 | CTA 点击率提升 15% 且跳出率不升高 | 过度承诺导致后续转化下降 |
| 新人权益实验 | 兴趣 -> 加购 / 留资 | 降低首次行动成本能提升转化 | 展示新人券、免费试用或保障承诺 | 不展示新人权益 | 首单 / 留资转化率 | 权益点击率、客单价 | 转化率提升 10% 且毛利可接受 | 用户只被优惠吸引，长期价值低 |
| 社会证明实验 | 兴趣 -> 加购 / 留资 | 真实案例能降低信任阻力 | 增加评价、案例、成交记录或成果展示 | 原页面少量介绍 | 加购 / 留资率 | 评价模块浏览率 | 加购或留资率提升 10% | 案例不真实会损害信任 |
| 流程压缩实验 | 加购 / 留资 -> 转化 | 更少步骤能减少流失 | 关键行动流程控制在 2-3 步 | 原流程 | 表单完成率 / 支付完成率 | 字段放弃率 | 完成率提升 15% | 字段过少影响后续运营 |
"""

    ab_test_md = """
**实验主题：** 首屏价值主张 A/B 测试

| 项目 | A 版本（对照组） | B 版本（实验组） |
| --- | --- | --- |
| 首屏标题 | 强调产品功能 | 强调用户场景和明确收益 |
| CTA | 立即了解 | 领取新人权益 / 开始试用 |
| 信任元素 | 无或靠后展示 | 首屏展示评价、数据或真实案例 |

**核心假设：** B 版本能让用户更快理解价值，并提升首屏 CTA 点击率。

**核心指标：** 首屏 CTA 点击率

**观察指标：**
- 访问到关键行动转化率
- 新用户转化率
- 跳出率

**成功标准：** B 版本 CTA 点击率提升 15%，且最终转化率不低于 A 版本。

**风险：** 点击提升可能来自夸张文案，如果后续转化下降，需要回看文案与真实交付是否一致。
"""

    return {
        "experiments": experiments_md.strip(),
        "ab_test": ab_test_md.strip(),
    }


def design_experiments(
    idea: str,
    outputs: dict[str, str],
    context: str | None = None,
    return_meta: bool = False,
) -> dict[str, str] | tuple[dict[str, str], bool]:
    fallback = _mock_experiments()
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

## 增长实验方案
每个实验必须包含：
- 实验名称
- 漏斗环节
- 业务假设
- 实验组
- 对照组
- 核心指标
- 观察指标
- 成功标准
- 风险

## A/B 测试方案
必须包含：
- 实验主题
- A 版本
- B 版本
- 核心假设
- 核心指标
- 观察指标
- 成功标准
- 风险

要求：
- 禁止输出空泛建议。
- 每条建议必须绑定漏斗环节、具体动作、核心指标和可验证方式。
- 优先输出可直接执行的实验，不要只给概念。
"""

    llm_output = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    if not llm_output:
        if return_meta:
            return fallback, True
        return fallback

    experiments = extract_markdown_section(llm_output, "增长实验方案") or llm_output
    ab_test = extract_markdown_section(llm_output, "A/B 测试方案") or llm_output
    result = {
        "experiments": experiments,
        "ab_test": ab_test,
    }
    if return_meta:
        return result, False
    return result
