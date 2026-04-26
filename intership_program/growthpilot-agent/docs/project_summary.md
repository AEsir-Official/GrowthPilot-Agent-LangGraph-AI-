# Project Summary

## 项目背景

很多消费 / 电商方向的商业想法一开始只有一句话，例如“做一个校园二手交易平台”。这类想法很难直接进入产品设计或实验验证，因为缺少目标用户、转化漏斗、增长实验、需求池、PRD、埋点和指标体系。

GrowthPilot Agent 的目标是把商业想法转成结构化增长实验报告，帮助用户快速理解业务该如何验证。

## 用户输入

用户输入一句或一段商业想法，例如：

```text
我想做一个面向大学生的平价护肤电商平台
```

## 系统输出

系统输出包括：

- 方案摘要
- 业务类型判断
- 目标用户画像
- 转化漏斗
- 增长实验与 A/B 测试方案
- 需求池
- PRD 初稿
- MVP 功能
- 埋点方案
- 指标体系
- Landing Page 文案
- Critic 评分
- badcase 分析
- 修订版方案摘要
- 下一轮迭代建议
- RAG Debug 信息
- Markdown 报告

## 工作流说明

```text
用户输入
-> RAG Retriever
-> Router Agent
-> Funnel Agent
-> Experiment Agent
-> Requirement Agent
-> PRD Agent
-> MVP Agent
-> Critic Agent
-> Markdown Exporter
```

每个 Agent 都有明确职责，并读取上游 Agent 输出。这样可以避免单 prompt 输出过长、结构混乱，也方便后续扩展单个模块。

## 技术栈

- Python
- Streamlit
- LangGraph
- OpenAI-compatible API
- OpenAI Python SDK
- TF-IDF RAG
- Markdown Knowledge Base

## 核心模块

| 模块 | 作用 |
| --- | --- |
| `app.py` | Streamlit UI，负责输入、展示、进度反馈、摘要和导出 |
| `workflow/graph.py` | LangGraph 主工作流入口 |
| `agents/router.py` | 业务类型、用户画像和指标判断 |
| `agents/funnel_agent.py` | 转化漏斗建模 |
| `agents/experiment_agent.py` | 增长实验和 A/B 测试 |
| `agents/requirement_agent.py` | 需求池生成 |
| `agents/prd_agent.py` | PRD 初稿生成 |
| `agents/mvp_agent.py` | MVP、埋点、指标和 Landing Page |
| `agents/critic_agent.py` | 评分、badcase、修复方案和迭代建议 |
| `rag/retriever.py` | 本地知识库 TF-IDF 检索和 RAG Debug 输出 |
| `utils/llm.py` | OpenAI-compatible API 调用封装 |
| `utils/summarizer.py` | 方案摘要提取 |
| `utils/exporter.py` | Markdown 报告导出和 Iteration Log 组织 |

## 当前限制

- 当前不是生产级系统。
- 没有接真实业务数据库。
- 没有接真实搜索 API 或复杂爬虫。
- 没有微调模型。
- 没有真正接入 MCP。
- RAG 使用本地 markdown 和 TF-IDF，适合 MVP，不适合大规模知识库。
- Streamlit UI 适合演示，不是完整商业产品前端。

## SQL Future Work / 真实数据复盘方向

未来可以接入真实业务数据库，用 SQL 分析用户行为事件表、商品表、订单表和实验分组表。

示例数据表：

- `users`
- `events`
- `items` / `products`
- `orders`
- `experiments`

可计算指标：

- CTR
- 发帖转化率
- 商品详情页点击率
- 发起对话率
- 对话 -> 成交转化率
- 留存率
- 复购率

价值说明：

Agent 未来可以基于真实指标判断 A/B 测试是否成功，并自动生成下一轮迭代建议。

## Future Work

- 接入真实业务数据库，用 SQL 分析转化漏斗。
- 接入真实搜索 API 做竞品调研。
- 接入真实埋点数据做自动实验复盘。
- 增加输入质量评估和轻量追问。
- 增加实验优先级评分模型。
- 接入 MCP，让 Agent 能访问更多外部工具。
