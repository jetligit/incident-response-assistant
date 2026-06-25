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
    client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_LLM_API_KEY"))

    tools = TOOLS

    system_prompt = f"""
        You are an incident response agent that pulls relevant logs and metrics, searches a runbook knowledge base for known fixes,
        reasons through likely root causes, and drafts a remediation plan.

        - Pulls relevant logs and metrics via tool calls
        - Searches a runbook knowledge base (RAG) for known fixes
        - Reasons through likely root causes
        - Drafts a remediation plan and posts it to Slack
        - Optionally executes safe actions (restart a service, clear a queue)
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
        

