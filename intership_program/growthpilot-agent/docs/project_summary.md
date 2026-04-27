# Project Summary

## Project Background

Many consumer and e-commerce ideas begin as short descriptions such as “build a campus second-hand marketplace.”  
Turning that idea into an actionable validation plan usually requires multiple artifacts: target users, funnels, experiments, requirements, PRDs, event tracking, and metrics.

GrowthPilot Agent is designed to connect those artifacts into one structured workflow.

## Input

The user provides a short business idea, for example:

```text
我想做一个校园二手交易平台
```

## Output

The system can generate:

- business type classification
- target user analysis
- conversion funnel
- growth experiments and A/B tests
- requirement pool
- PRD draft
- MVP feature list
- event tracking plan
- metrics system
- landing page copy
- critic review
- badcase analysis
- iteration suggestions
- markdown report

## Workflow

```text
User Input
-> RAG Retriever
-> Router Agent
-> Funnel Agent
-> Experiment Agent
-> Requirement Agent
-> PRD Agent
-> MVP Agent
-> Critic Agent
-> Markdown Export
```

Each stage reads upstream outputs and produces a structured artifact for the next stage.

## Technical Stack

- Python
- Streamlit
- LangGraph
- OpenAI-compatible API
- TF-IDF RAG
- Markdown Knowledge Base

## Core Modules

| Module | Responsibility |
| --- | --- |
| `app.py` | Streamlit UI, progress display, summary, debug panel, export |
| `workflow/graph.py` | Main workflow entrypoint |
| `agents/router.py` | Business type, target user, goals, metric direction |
| `agents/funnel_agent.py` | Funnel modeling |
| `agents/experiment_agent.py` | Growth experiments and A/B tests |
| `agents/requirement_agent.py` | Requirement pool generation |
| `agents/prd_agent.py` | PRD draft generation |
| `agents/mvp_agent.py` | MVP, event tracking, metrics, landing page |
| `agents/critic_agent.py` | Critic review, badcase analysis, revision guidance |
| `rag/retriever.py` | Local markdown retrieval and RAG debug output |
| `utils/exporter.py` | Markdown report export and iteration log formatting |
| `mcp_server/server.py` | Optional MCP tool interface |

## Current Limitations

- this is an experimental MVP, not a production-grade system
- no real business database is connected
- no real crawler or external search pipeline is included
- no model fine-tuning is used
- the knowledge base is local and intentionally lightweight
- the Streamlit UI is optimized for local usage rather than production deployment

## SQL Future Work

Future versions can connect to real business tables and use SQL to analyze:

- `users`
- `events`
- `items` / `products`
- `orders`
- `experiments`

Example metrics:

- CTR
- product detail click-through rate
- contact initiation rate
- contact-to-transaction conversion rate
- retention rate
- repurchase rate

This would allow the system to evaluate experiment outcomes based on real data and generate more grounded iteration suggestions.

## Optional MCP Integration

GrowthPilot Agent also provides an optional MCP server layer for exposing internal capabilities as tools:

- `retrieve_growth_templates`
- `generate_growth_report`
- `export_growth_report`

This layer is experimental and is not required for the main Streamlit application.

## Future Work

- add SQL-based experiment result analysis
- expand the RAG knowledge base by vertical
- add rewrite / revision logic for automatic plan refinement
- add SQL-based experiment result analysis as an MCP tool
- add RAG evaluation as an MCP tool
- add Rewrite Agent as an MCP tool
