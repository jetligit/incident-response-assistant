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

## Starting the RAG portion (first-timer notes)

The mental model: RAG = "let the agent look things up before it answers." Instead of hoping the model already knows your runbooks, you store them, find the most relevant ones for the current incident, and paste those into the prompt. Nothing magic — it's search + copy-paste, automated.

**The core pieces, in order:**

- **Write the runbooks first.** Create a `runbooks/` folder with 10–15 short markdown docs, one issue per file (e.g. `connection-pool-exhaustion.md`, `disk-full.md`, `dns-failure.md`). Each should have a title, symptoms, likely causes, and a fix. Make `connection-pool-exhaustion.md` match your current incident so you can prove retrieval works end to end.
- **Understand embeddings.** An embedding turns text into a list of numbers (a vector) where similar meaning → nearby vectors. That's what lets you search by *meaning* ("DB connections maxed out") instead of exact keywords ("pool exhaustion"). You don't compute these yourself — an embedding model does. Pick one: Anthropic doesn't serve embeddings, so use Voyage AI (Anthropic's recommended pairing) or OpenAI's `text-embedding-3-small`, or run a local one via `sentence-transformers` if you want zero API cost.
- **Chunk the docs.** Long docs get split into smaller passages before embedding, so retrieval returns the relevant paragraph, not a whole file. Your runbooks are short, so start dead simple: one chunk per file (or per `##` section). Don't over-engineer chunking on day one.
- **Pick a vector store — start with Chroma.** It's the easiest local option (`pip install chromadb`), runs in-process, and persists to a folder. No server to manage. pgvector is the alternative if you specifically want Postgres, but that's more setup than you need to learn the concept.
- **Build a one-time ingestion script.** Separate from the agent: read each runbook → (chunk) → embed → store in Chroma with the text + metadata (filename, title). Run it once now, and re-run only when runbooks change. Keep it out of the agent's hot path.
- **Add retrieval as a tool, matching your existing pattern.** Write `search_runbooks(query)` that embeds the query, asks Chroma for the top-k (start with k=3) nearest chunks, and returns their text. Register it in `TOOLS` and `TOOL_DISPATCH` exactly like `retrieve_logs` / `retrieve_metrics`. Now the agent decides *when* to look something up — same tool-use loop you already have, no new control flow.
- **Verify retrieval in isolation before wiring it to the LLM.** Call `search_runbooks("payments-service database connections maxed out")` directly and confirm `connection-pool-exhaustion.md` comes back on top. If retrieval is wrong here, the agent can't recover — debug this layer first.
- **Then close the loop.** Let the agent call `retrieve_logs` + `retrieve_metrics` to see the symptoms, `search_runbooks` to find the matching fix, and draft a remediation plan that cites the runbook it used. Citing the source doc is both a good habit and an easy way to catch hallucinated fixes.

**Beginner traps to avoid:**

- Don't embed the query with one model and the documents with another — they must be the *same* embedding model, or "nearness" is meaningless.
- Don't dump all runbooks into the prompt and call it RAG. The point is retrieving only what's relevant; stuffing everything wastes context and buries the signal.
- Don't chase fancy chunking, re-ranking, or hybrid search yet. Get the simple top-k pipeline working and proven against your known incident first — add sophistication only when you can measure it helping (that's what the week-5 eval harness is for).
