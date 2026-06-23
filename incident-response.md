# Incident Response Assistant

## What it actually does

When an alert fires (a server is down, a pipeline fails, an anomaly is detected), the agent automatically:

- Pulls relevant logs and metrics via tool calls
- Searches a runbook knowledge base (RAG) for known fixes
- Reasons through likely root causes
- Drafts a remediation plan and posts it to Slack
- Optionally executes safe actions (restart a service, clear a queue)

The key insight that makes this impressive: it's not just a chatbot you ask questions to. It's an autonomous loop that fires on real events.

## Tech stack

- **Core agent logic:** Python with LangGraph (best for stateful, multi-step agent loops) or LangChain if you want faster setup. LangGraph is the stronger resume signal in 2025.
- **LLM:** Anthropic Claude API or OpenAI — use the API directly so you understand the primitives. Don't hide everything behind LangChain abstractions.
- **Tool layer:** Write Python functions the agent can call — a log query tool (mock Datadog API or use real CloudWatch with free tier), a metrics fetcher, and a command executor (for safe remediation actions like restarting a process).
- **RAG / runbook store:** Chroma (easiest local setup) or pgvector if you want Postgres. Ingest a set of markdown runbook docs — you can write fake but realistic ones based on common infra issues.
- **Backend:** FastAPI to expose a webhook endpoint that triggers the agent when an alert fires.
- **Alerting:** Mock PagerDuty-style webhooks with a simple script, or wire up a free UptimeRobot account to fire real HTTP alerts.
- **Output:** Slack webhook (free, takes 10 minutes to set up) so you have a real demo of messages appearing in a channel.
- **Evals:** Log every agent run with its inputs, tool calls, and outputs. Write a simple replay harness so you can re-run past incidents and check if the agent improves when you change prompts.

## 8-week timeline

| Week | Milestone |
| --- | --- |
| 1–2 | Core agent loop: alert in → tool calls → response out. No RAG yet, just hardcoded tools. |
| 3 | Add RAG: ingest 10–15 runbooks, wire up vector retrieval into the agent's context. |
| 4 | Slack integration + severity classification (P1/P2/P3 with reasoning). |
| 5 | Evaluation harness: replay 20 synthetic incidents, measure response quality. |
| 6 | Optional: add a simple remediation action (restart service, clear cache) with human-in-the-loop confirmation. |
| 7–8 | Polish demo, write README with architecture diagram, deploy to a cheap VPS or Railway. |

## How to present it

On your resume, frame it as:

> "Built an autonomous incident response agent using LangGraph and RAG that triages alerts, queries logs and metrics via tool calls, and posts remediation plans to Slack — reducing mean-time-to-triage by X% on a test incident suite."

In interviews, the story is:

> "At Cypress Creek I saw how much time ops teams spent manually diagnosing alerts. I built this to explore how an autonomous agent with tool access could cut that triage time, and specifically wanted to understand the failure modes — when does the agent hallucinate a root cause, and how do you catch that?"

That last sentence — showing you thought about evals and failure modes — is what separates you from candidates who just built a demo.

Want me to help you spec out the LangGraph state machine or the RAG runbook schema?
