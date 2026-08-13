# Incident Response Assistant

## What this project is

An autonomous incident-response agent. When an alert fires, the agent pulls the
relevant logs and metrics, searches a runbook knowledge base (RAG) for known
fixes, reasons through the likely root cause, and drafts a severity-classified
remediation plan. It is a personal/portfolio project — the goal is to understand
agent primitives (tool use, RAG, evals, failure modes) by building the loop by
hand rather than hiding it behind a framework.

The pitch: it is not a chatbot you query — it is an autonomous loop that fires on
real events.

## Architecture

**Design decisions (already settled — don't relitigate):**

- **Classic RAG, not agentic RAG.** Retrieval is a deterministic step in our own
  code, not a tool the model chooses to call. This is intentional: with a small,
  well-separated runbook corpus, a single good query reliably surfaces the right
  runbook, and deterministic retrieval is easier to control, inspect, and debug.
- **Hand-rolled loop, no framework.** No LangGraph/LangChain. We drove and
  dropped LangGraph earlier; the loop is plain Python for transparency.
- **Two-phase staged pipeline.** Retrieval sits *between* two model phases,
  because the runbook search query depends on evidence gathered first.

**The flow** (`handle_incident` in `run_agent.py` orchestrates it):

```
alert (incidents/incident.json)
   │
   ▼
PHASE 1 — Gather   (determine_retrieval_params)
   Agent loop: Claude calls retrieve_logs / retrieve_metrics to characterize
   the incident, then ends with a short factual symptom summary.
   "Gather, don't diagnose yet" — so the loop stops and hands control back.
   │
   ▼
THE SEAM — classic RAG   (search(summary))
   Deterministic. Embeds the symptom summary and pulls the top-k runbook
   sections from Chroma. Plain Python between the two phases.
   │
   ▼
PHASE 2 — Grounded diagnosis   (run_diagnosis)
   Single Claude call (no tools). Given the alert + gathered evidence + runbook
   sections, produces: severity (P1/P2/P3), root cause, remediation plan
   (immediate mitigation + root-cause fix), and confidence. Grounded in the
   runbooks; must say so when the runbooks don't match rather than inventing.
   │
   ▼
(planned) post to Slack
```

## Key files

| File | Role |
| --- | --- |
| `run_agent.py` | The agent. `determine_retrieval_params` (Phase 1 gather loop), `run_diagnosis` (Phase 2 diagnosis), `handle_incident` (orchestrator), the `retrieve_logs` / `retrieve_metrics` tools + schemas. |
| `rag_embeddings.py` | RAG. `create_embeddings` parses runbooks into per-section chunks and stores them in Chroma; `search(query, k=3)` embeds a query (with the bge instruction prefix) and returns the top-k sections. |
| `runbooks/` | 10 markdown runbooks (disk-full, cache-outage, ssl-cert-expiry, …). Each has `##` sections (Summary, Symptoms, Likely causes, Diagnosis, Immediate mitigation, Root-cause fix, Prevention). One chunk per section. |
| `incidents/incident.json` | The active mock incident the tools read from: `alert`, `logs[]`, `metrics{}`. |
| `incidents/incident.truth.json` | Ground-truth root cause + expected signals for the active incident — the oracle for scoring diagnoses in evals. |
| `inc-generator.py` | Synthetic incident generator: produces realistic logs/metrics + matching ground truth for common failure scenarios, single or in batches. The engine for building an eval set. |
| `message.py` | Intended Slack-posting module. Currently empty. |
| `project_info/incident-response.md` | The original project spec, tech stack, and 8-week timeline. |

## Stack

- **LLM:** Anthropic Claude API (`claude-opus-4-8`), called via the `anthropic`
  SDK. API key from env var `CLAUDE_LLM_API_KEY` (loaded via `python-dotenv`;
  `.env` is gitignored).
- **Embeddings:** `BAAI/bge-base-en-v1.5` via `sentence-transformers`. This is an
  *asymmetric* model — queries get the prefix
  `"Represent this sentence for searching relevant passages: "`; stored passages
  do not. Embeddings are L2-normalized.
- **Vector store:** Chroma, `PersistentClient(path="chroma_db")`, collection
  `runbooks` with `hnsw:space: "cosine"`.

## How to run

1. Build the vector store once (creates `chroma_db/`):
   `python rag_embeddings.py`
2. There is no wired-up entry point yet (see Known issues). Intended usage is to
   build an initial alert message from `incidents/incident.json` and call
   `handle_incident([...])`.

## Current status

**Working / built:**
- Runbook knowledge base (10 runbooks).
- RAG ingestion + retrieval (`create_embeddings`, `search`).
- Phase 1 gather loop with the two tools, a 5-iteration cap, and a forced-summary
  fallback if the loop never stops on its own.
- The retrieval seam and Phase 2 grounded-diagnosis prompt.
- Synthetic incident generator and ground-truth files (groundwork for evals).

**Known issues to fix (in `run_agent.py` unless noted):**
1. `run_diagnosis` line ~211: `messages = messages = [...]` **replaces** the
   Phase 1 history instead of appending to it, so Phase 2 loses the alert and the
   gathered logs/metrics — it diagnoses from the runbooks alone. Should be
   `messages = messages + [...]`. **This is the important one.**
2. `run_diagnosis`: `chunks` is Chroma's raw query dict interpolated straight into
   the prompt. It works but is messy — format the retrieved sections (label each
   with `source_file` / `section`) so Claude can cite them cleanly.
3. `run_diagnosis`: the `for i in range(5)` loop returns on the first iteration —
   it does nothing. Phase 2 is a single call; remove the loop.
4. `handle_incident`: `summary = summary` is a no-op; delete it.
5. `rag_embeddings.py`: unused `import collections`.
6. No entry point constructs an alert and calls `handle_incident`.

## Not yet built (from the plan)

- **Structured diagnosis output** — have Phase 2 return validated JSON
  (severity, root_cause, immediate_mitigation, root_cause_fix, confidence,
  cited_runbooks) via the API's structured outputs. Unblocks Slack + evals +
  remediation gating. Recommended next.
- **Trigger layer** — a FastAPI webhook that receives an alert and calls
  `handle_incident` (the "fires on real events" piece).
- **Slack integration** — fill in `message.py` to post the plan to a channel.
- **Eval / replay harness** — run the agent over a batch of generated incidents
  and score its diagnosis against the `.truth.json` files.
- **Remediation executor + human-in-the-loop** — a command-executor tool (mock
  restart/clear-queue) gated behind explicit human approval.
- **README + deploy.**

## Conventions & notes

- **Safety:** any remediation action that changes system state must be flagged as
  requiring human approval before execution. The agent recommends; a human
  approves. Do not wire an executor to run these automatically.
- **Cost:** RAG embeddings/retrieval are free (local model + local Chroma). Only
  the Claude calls cost tokens. Testing the full suite is single-digit dollars.
  Use prompt caching on the stable system prompts if iterating heavily.
- Each runbook section is its own chunk; `k=3` returns the 3 closest sections,
  which may span one or more runbooks. There is no relevance cutoff — the Phase 2
  grounding rule ("say so if the runbooks don't match") handles bad matches.
