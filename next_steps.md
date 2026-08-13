# Next Steps — in plain terms

A simple map of what this project does, what's finished, and what's left.

## What the project does (in one paragraph)

When a server has a problem, an "alert" goes off. This tool acts like an
on-call engineer: it looks at the logs and metrics to see what's happening,
looks up the matching troubleshooting guide ("runbook"), figures out the likely
cause, and writes up a fix — including how serious it is (P1/P2/P3). The point is
that it does this automatically when an alert fires, not by someone asking it
questions.

## How it works (the three steps)

1. **Gather.** The agent looks at the incident's logs and metrics and writes a
   short summary of the symptoms. It only gathers here — it doesn't guess the
   cause yet.
2. **Look it up (RAG).** We take that symptom summary and search the runbook
   library for the most relevant troubleshooting sections. This search is done by
   our own code, on purpose, so it always happens and we can see exactly what it
   found.
3. **Diagnose.** The agent takes the symptoms plus the matching runbook sections
   and writes the final answer: how serious it is, the likely root cause, a fix
   (both a quick stabilizer and a permanent fix), and how confident it is.

## What's done ✅

- **The runbook library** — 10 troubleshooting guides (disk full, cache outage,
  expired SSL certificate, and so on).
- **The search system (RAG)** — the runbooks are turned into searchable pieces
  and stored, and there's a working search that finds the most relevant ones.
- **Step 1 (Gather)** — the agent can pull logs and metrics and summarize the
  symptoms.
- **Step 3 (Diagnose)** — the agent writes a graded diagnosis and remediation
  plan grounded in the runbooks.
- **A fake incident generator** — a script that invents realistic incidents plus
  the "correct answer" for each, so we can test the agent against known cases
  later.

## What needs fixing before it fully works 🔧

These are small but real — the agent won't give good answers until they're done:

1. **Most important:** in Step 3, the code accidentally *throws away* the logs and
   metrics from Step 1 before diagnosing. Right now the agent diagnoses using only
   the runbooks and forgets the actual incident details. One-line fix.
2. The runbook search results are handed to the agent in a messy raw format —
   tidy them up so the agent can quote its sources cleanly.
3. There's a leftover loop in Step 3 that does nothing — remove it.
4. A couple of harmless leftover lines to delete.
5. Nothing yet actually kicks off the whole process with a real incident — need a
   small starting point that loads an incident and runs it.
6. Run the setup script once to build the search database before the search works.

## What's still to build 🚧

Roughly in order of usefulness:

1. **Cleaner output format (recommended first).** Make the diagnosis come back as
   organized fields (severity, cause, fix, confidence) instead of a paragraph.
   This makes everything after it — Slack, testing, approvals — much easier.
2. **The "front door" (webhook).** A small web endpoint so a real alert can
   trigger the agent automatically. This is the piece that makes it a real
   autonomous tool instead of a script.
3. **Slack posting.** Send the finished plan to a Slack channel. (`message.py`
   exists but is empty.)
4. **Testing harness.** Run the agent against a batch of fake incidents and check
   its answers against the known-correct ones. The generator and answer keys are
   already built, so this is mostly wiring.
5. **Safe auto-fixes with human approval.** Let the agent *propose* actions like
   restarting a service, but require a person to approve before anything runs.
6. **README and deployment.** Final polish.

## Important rule

Any action that changes a live system (restart, delete, config change) must be
approved by a human first. The agent suggests — a person decides.
