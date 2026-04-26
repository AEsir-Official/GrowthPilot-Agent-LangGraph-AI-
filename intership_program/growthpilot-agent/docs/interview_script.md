# Interview Script

## 30 秒讲法

GrowthPilot Agent 是一个面向消费 / 电商场景的 AI 增长实验设计系统。它不是只生成 PRD，而是把商业想法拆成业务判断、转化漏斗、A/B 测试、需求池、PRD、埋点、指标体系和 Critic 迭代建议。技术上我用了 Python、Streamlit、LangGraph、OpenAI-compatible API 和 TF-IDF RAG，并保留 mock fallback，保证没有 API key 也能完整演示。

## 1 分钟讲法

这个项目叫 GrowthPilot Agent，定位是求职展示型 AI Agent Workflow MVP。用户输入一个商业想法，比如“面向大学生的平价护肤电商平台”，系统先做本地知识库 RAG 检索，再通过 LangGraph 串联多个 Agent。Router Agent 识别业务类型和指标，Funnel Agent 建模转化漏斗，Experiment Agent 设计增长实验和 A/B 测试，Requirement Agent 生成需求池，PRD Agent 输出 PRD 初稿，MVP Agent 输出功能、埋点、指标和 Landing Page 文案，最后 Critic Agent 做评分、badcase 分析、修复方案和迭代建议。它的重点不是大模型写文档，而是用 Agent Workflow 把增长验证过程结构化。

## 3 分钟讲法

GrowthPilot Agent 是我为求职展示做的第一个 AI Agent 项目，面向消费和电商场景。它解决的问题是：很多商业想法只有一句话，但要真正进入产品设计和实验验证，还需要目标用户、转化漏斗、实验方案、需求池、PRD、埋点和指标体系。传统做法往往分散在多个文档里，容易脱节，所以我把它做成了一个可运行的多 Agent 工作流。

项目的主干是 LangGraph。第一步是 RAG Retriever，从本地 markdown 知识库里检索漏斗、A/B 测试、PRD、埋点和指标模板。然后进入 Router Agent，判断业务类型、目标用户、核心业务目标和北极星指标。Funnel Agent 把业务拆成访问、兴趣、加购或留资、转化、复购等环节。Experiment Agent 输出增长实验和 A/B 测试方案，明确实验组、对照组、核心指标、观察指标、成功标准和风险。Requirement Agent 把实验转成需求池。PRD Agent 输出项目背景、目标用户、用户痛点、核心路径、功能需求和验收标准。MVP Agent 输出第一版功能、埋点方案、指标体系和 Landing Page 文案。最后 Critic Agent 对方案打分，指出主要问题、badcase 风险、原因分析、修复方案、修订版方案摘要和下一轮迭代建议。

技术上我刻意保持轻量，只用 Python 技术栈：Streamlit 做本地 UI，LangGraph 做工作流，OpenAI-compatible API 做 LLM 调用，本地 markdown 知识库加 TF-IDF 做轻量 RAG。为了保证项目稳定演示，我给每个 Agent 做了 fallback 机制：没有 API key 或 API 调用失败时，系统自动回退到 mock 输出。最新一轮还增加了 RAG Debug Panel、方案摘要、阶段进度反馈、Skill-like 模块文档，以及导出 Markdown 报告中的 Iteration Log，让这个项目更像一个完整的求职展示资产，而不只是一个 demo。

这个项目最有价值的点是，它不是一个“商业计划书生成器”或“AI PRD 生成器”，而是一个围绕增长实验验证的 Agent Workflow：从业务判断到实验设计，再到需求、PRD、埋点、指标和迭代建议，逻辑链条是完整的。

## 面试官可能问的问题和回答

### Q1：这个项目会不会只是商业计划书生成器？

不是。它不是只生成文档，而是通过 LangGraph 把业务验证过程拆成多个节点。每个需求都绑定漏斗环节和指标，每个实验都包含实验组、对照组、成功标准和风险，最后还有 Critic Agent 负责 badcase 和迭代建议。所以它更像增长实验 workflow，而不是单纯的文案生成器。

### Q2：为什么不直接用 Dify？

Dify 很适合快速做低代码编排和原型，但这个项目的目标之一是展示 Python 工程实现能力和 Agent 编排能力，所以我选择手写 LangGraph 工作流。这样在面试里更容易说明状态流转、fallback 机制、RAG 接口和导出逻辑，而不是只展示一个低代码画布。

### Q3：为什么不用 LlamaIndex？

LlamaIndex 更偏数据连接、索引管理和 RAG 组织。这个项目当前知识库规模很小，只是本地 Markdown 模板，所以我先用本地 Markdown + TF-IDF 做轻量 RAG，复杂度更低，也更容易讲清楚。如果后续知识库规模扩大，完全可以替换成 LlamaIndex 或向量数据库。

### Q4：RAG 在这里解决什么问题？

RAG 主要解决纯 prompt 输出空泛和结构不稳定的问题。它会把 PRD、A/B 测试、埋点、指标模板注入 Agent 上下文，让输出更具体。现在还增加了 RAG Debug Panel，可以直接看到命中的文件、分数、检索方式和片段预览，方便定位漏召回和模板不足的问题。

### Q5：badcase 是怎么进入迭代闭环的？

Critic Agent 不是只打分，它会输出主要问题、Badcase 风险、原因分析、修复方案、修订版方案摘要和下一轮迭代建议。Markdown 报告里还新增了 Iteration Log，把初版问题、修复动作和后续方向串起来。下一步如果接真实埋点数据，就可以让这个闭环基于真实实验结果自动更新。

### Q6：后续如果接真实数据，你会怎么做？

我会先接入 `events`、`orders`、`experiments` 等表，用 SQL 计算 CTR、详情点击率、对话转化率、订单转化率、留存率和复购率。然后让 Agent 基于真实指标判断 A/B 测试是否成功，再自动生成下一轮迭代建议。这样项目就会从“方案生成系统”进化成“方案生成 + 数据复盘系统”。

### 这和普通 PRD 生成器有什么区别？

普通 PRD 生成器通常把输入扩写成文档。GrowthPilot Agent 的核心是增长实验 workflow：先判断业务类型和目标用户，再建转化漏斗，接着设计 A/B 测试和增长实验，然后生成需求池、PRD、埋点、指标体系，最后由 Critic Agent 做 badcase 和迭代建议。它输出的不只是文档，而是一条可验证的增长实验链路。

### 为什么用 LangGraph？

因为这个任务天然是多步骤、有依赖关系的。Router 的输出会影响 Funnel，Funnel 会影响 Experiment，Experiment 会影响 Requirement 和 PRD，最后 Critic 需要读取前面所有结果。LangGraph 可以把这些步骤组织成清晰的 DAG，比把所有逻辑塞进一个 prompt 更容易维护、扩展和讲解。

### A/B 测试和指标怎么设计？

我先从漏斗环节定位问题，比如访问到兴趣、兴趣到留资、留资到转化。然后为每个问题写业务假设，再设计实验组和对照组。指标分为核心指标和观察指标：核心指标判断实验是否成功，观察指标用来防止局部优化伤害整体转化。比如首屏文案实验的核心指标是 CTA 点击率，观察指标是最终转化率和跳出率。

### 为什么没有做微调？

当前任务更偏结构化业务生成，数据量也不大。用 prompt + RAG + workflow 的性价比更高：prompt 控制输出结构，RAG 提供业务模板，workflow 保证步骤稳定。微调更适合有大量标注数据、固定输出风格和长期稳定任务的场景。这个 MVP 阶段做微调会增加复杂度，但收益不明显。

### 这个项目最有价值的地方是什么？

最有价值的是把产品增长思维和 Agent 工程结合起来。它不是炫技式调用大模型，而是把一个业务想法拆成漏斗、实验、需求、PRD、埋点、指标和迭代建议，形成完整闭环。对面试来说，它能展示我既理解业务增长，也能用 Python 和 LangGraph 把流程做成可运行的系统。
