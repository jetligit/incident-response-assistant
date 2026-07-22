import anthropic
from dotenv import load_dotenv
import os
import json

load_dotenv()

INCIDENT_FILE = os.path.join(os.path.dirname(__file__), "incidents", "incident.json")


def retrieve_logs(service=None, level=None):
    """Return log entries from the incident file, optionally filtered.

    Args:
        service: if given, only return logs for this service.
        level:   if given (e.g. "ERROR"), only return logs at this level.
    """
    with open(INCIDENT_FILE) as f:
        incident = json.load(f)

    logs = incident.get("logs", [])
    if service:
        logs = [entry for entry in logs if entry.get("service") == service]
    if level:
        logs = [entry for entry in logs if entry.get("level") == level.upper()]
    return logs

def retrieve_metrics(metric=None, service=None):
    """Return metric time series from the incident file, optionally filtered.

    Args:
        metric:  if given (e.g. "latency.p99_ms"), only return this metric.
        service: if given, only return series for this service.
    """
    with open(INCIDENT_FILE) as f:
        incident = json.load(f)

    metrics = incident.get("metrics", {})
    if metric:
        metrics = {metric: metrics[metric]} if metric in metrics else {}
    if service:
        metrics = {
            name: {svc: series for svc, series in svcs.items() if svc == service}
            for name, svcs in metrics.items()
        }
    return metrics


# Tool schema the API sees. The "name" must match the key we dispatch on below.
TOOLS = [
    {
        "name": "retrieve_logs",
        "description": "Retrieve log entries for the active incident. "
                       "Optionally filter by service name and/or log level.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service to filter logs by, e.g. 'payments-service'.",
                },
                "level": {
                    "type": "string",
                    "description": "Log level to filter by, e.g. 'ERROR', 'WARN', 'INFO'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "retrieve_metrics",
        "description": "Retrieve metric time series for the active incident. "
                       "Optionally filter by metric name and/or service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metric to filter by, e.g. 'latency.p99_ms', "
                                   "'error_rate', 'db.active_connections'.",
                },
                "service": {
                    "type": "string",
                    "description": "Service to filter by, e.g. 'payments-service'.",
                },
            },
            "required": [],
        },
    },
]

# Maps tool name -> the Python function that runs it.
TOOL_DISPATCH = {
    "retrieve_logs": retrieve_logs,
    "retrieve_metrics": retrieve_metrics,
}


def run_agent(history:list[dict]):
    # Phase 2 is supposed to be a separate call for run_agent with its own system_prompt. I am running RAG manually between Phase 1 and Phase 2.



    client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_LLM_API_KEY"))

    tools = TOOLS

    system_prompt = f"""
        You are an incident response agent that pulls relevant logs and metrics, searches a runbook knowledge base for known fixes,
        reasons through likely root causes, and drafts a remediation plan.

        Your job is broken down into 2 phases

        
        Phase 1 — Gather (system prompt for the gathering loop)

        You are an incident investigator. An alert has fired. Your job in this phase is
        to GATHER evidence — not to diagnose or fix anything.

        Use the available tools (get_logs, get_metrics) to pull the data needed to
        characterize what is happening: error messages, the affected host or service,
        relevant resource metrics, and timing.

        Rules for this phase:
        - Investigate only. Do NOT propose a root cause, diagnosis, or remediation — a
        later step handles that.
        - Pull what this alert actually calls for. Start with the most relevant signal
        and expand only if the picture is incomplete; don't fetch data unrelated to
        this alert.
        - When you have enough evidence to describe the symptoms clearly, stop calling
        tools and end with a short, factual summary of what you found (the observed
        symptoms and affected component) — no analysis, just the evidence.

        

        Phase 2 — Grounded diagnosis (system prompt)

        You are an incident responder. You are given: the original alert, the logs and
        metrics gathered during investigation, and relevant runbook sections retrieved
        from the team's knowledge base.

        Diagnose the incident and produce a remediation plan, grounded in the retrieved
        runbooks.

        Grounding rules:
        - Base your root cause and remediation on the retrieved runbook content. When you
        rely on a runbook, name it (use its source file / section).
        - If the retrieved runbooks do not match the symptoms, say so explicitly and give
        your best assessment from the evidence. Do not invent a fix or claim a runbook
        supports something it does not.

        Produce:
        1. Severity — P1, P2, or P3, with a one-line justification.
        2. Root cause — your most likely hypothesis and the evidence supporting it.
        3. Remediation plan, split into:
        - Immediate mitigation — safe steps to stabilize now.
        - Root-cause fix — what prevents recurrence.
        4. Confidence — high / medium / low, and what would raise it.

        Any action that changes system state (restarting services, deleting data,
        editing config, clearing queues) must be flagged as requiring human approval
        before execution. Recommend these actions; do not assume they run automatically.
    """

    messages = list(history or [])

    while True: 
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4096,
            tools=tools,
            system=system_prompt,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    output = TOOL_DISPATCH[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(output),
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            return messages
        

